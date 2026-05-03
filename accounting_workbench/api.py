# Copyright (c) 2026, Author and contributors
# For license information, please see license.txt

from datetime import date, datetime, timedelta

import frappe
import frappe.sessions
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils import flt, getdate


def _parse_range_date(value):
	"""Coerce request date to datetime.date. Invalid/empty/non-string values fall back to today."""
	if value is None:
		return getdate()
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	if isinstance(value, str):
		raw = value.strip()
		if not raw:
			return getdate()
		try:
			parsed = getdate(raw)
			return parsed if parsed is not None else getdate()
		except Exception:
			return getdate()
	return getdate()


@frappe.whitelist(allow_guest=False)
def session_bootstrap():
	"""Return CSRF token for the current logged-in session (SPA loaded outside Desk shell)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"))
	return {"csrf_token": frappe.sessions.get_csrf_token()}


@frappe.whitelist(allow_guest=True)
def auth_status():
	"""Current session user id (Guest when unauthenticated); safe for SPA route guards."""
	return frappe.session.user


@frappe.whitelist()
def dashboard_summary(company=None, from_date=None, to_date=None):
	"""Aggregate KPIs and widget data for the Accounting Workbench dashboard."""
	if not frappe.has_permission("Company", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = company or frappe.defaults.get_user_default("Company") or _first_company()
	if not company:
		return _empty_summary(_("No Company found"))

	from_date = _parse_range_date(from_date)
	to_date = _parse_range_date(to_date)
	if from_date > to_date:
		from_date, to_date = to_date, from_date

	prev_span = (to_date - from_date).days + 1
	prev_end = from_date - timedelta(days=1)
	prev_start = prev_end - timedelta(days=prev_span - 1)

	currency = frappe.db.get_value("Company", company, "default_currency") or ""

	kpis = _compute_kpis(company, from_date, to_date, prev_start, prev_end)

	return {
		"company": company,
		"currency": currency,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"previous_period_label": _human_date_range(prev_start, prev_end),
		"kpis": kpis,
		"tasks": _tasks(company),
		"cash_series": _cash_in_out_series(company, from_date, to_date),
		"expense_breakdown": _expense_breakdown(company, from_date, to_date),
		"recent_gl": _recent_gl(company, limit=8),
		"due_payables": _due_payables(company, limit=6),
		"alerts": _alerts(company),
	}


def _first_company():
	name = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	return name


def _empty_summary(reason):
	return {
		"company": None,
		"currency": "",
		"from_date": None,
		"to_date": None,
		"previous_period_label": "",
		"kpis": [],
		"tasks": [],
		"cash_series": {"labels": [], "inflow": [], "outflow": []},
		"expense_breakdown": [],
		"recent_gl": [],
		"due_payables": [],
		"alerts": [{"title": reason, "severity": "medium"}],
	}


def _human_date_range(start, end):
	months = (
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec",
	)
	a = f"{months[start.month - 1]} {start.day}"
	b = f"{months[end.month - 1]} {end.day}, {end.year}"
	return f"{a} – {b}"


def _cash_balance(company, account_names, as_of_date):
	"""Net GL balance on bank/cash accounts up to and including as_of_date."""
	if not account_names:
		return 0.0
	row = frappe.db.sql(
		f"""
		select coalesce(sum(debit),0) - coalesce(sum(credit),0)
		from `tabGL Entry`
		where company=%s and posting_date <= %s
		and account in ({",".join(["%s"] * len(account_names))})
		and is_cancelled=0
		""",
		tuple([company, as_of_date, *account_names]),
	)
	return flt(row[0][0] if row else 0)


def _unreconciled_bank_stats(company):
	row = frappe.db.sql(
		"""
		select count(*), coalesce(sum(unallocated_amount), 0)
		from `tabBank Transaction`
		where company=%s and status in ('Pending', 'Unreconciled')
		""",
		company,
	)
	if not row:
		return 0, 0.0
	return int(row[0][0] or 0), flt(row[0][1])


def _cash_account_names(company):
	"""Bank + Cash root accounts for simple cash proxy."""
	roots = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and account_type in ('Bank', 'Cash')
		and is_group=0
		limit 200
		""",
		company,
		as_list=True,
	)
	return [r[0] for r in roots]


def _compute_kpis(company, cur_start, cur_end, prev_start, prev_end):
	cash_accounts = _cash_account_names(company)

	cash_bal = _cash_balance(company, cash_accounts, cur_end)
	cash_bal_prev = _cash_balance(company, cash_accounts, prev_end)

	ar = (
		frappe.db.sql(
			"""
			select sum(outstanding_amount)
			from `tabSales Invoice`
			where company=%s and docstatus=1 and outstanding_amount > 0
			""",
			company,
		)[0][0]
		or 0
	)

	ap = (
		frappe.db.sql(
			"""
			select sum(outstanding_amount)
			from `tabPurchase Invoice`
			where company=%s and docstatus=1 and outstanding_amount > 0
			""",
			company,
		)[0][0]
		or 0
	)

	je_d = frappe.db.count("Journal Entry", {"company": company, "docstatus": 0})
	pe_d = frappe.db.count("Payment Entry", {"company": company, "docstatus": 0})
	pending_total = je_d + pe_d

	unreconciled_n, unreconciled_amt = _unreconciled_bank_stats(company)

	pl = _profit_loss_simple(company, cur_start, cur_end)
	pl_prev = _profit_loss_simple(company, prev_start, prev_end)

	def pct_change(cur, prev):
		if prev == 0:
			return 100.0 if cur else 0.0
		return round((cur - prev) / abs(prev) * 100, 1)

	spark_cash = _daily_net_cash_series(cash_accounts, company, cur_end, days=14)

	return [
		{
			"id": "cash_position",
			"label": _("Cash Position"),
			"value": cash_bal,
			"delta_pct": pct_change(cash_bal, cash_bal_prev),
			"sparkline": spark_cash,
		},
		{
			"id": "ar",
			"label": _("Accounts Receivable"),
			"value": flt(ar),
			"delta_pct": None,
			"sparkline": [],
		},
		{
			"id": "ap",
			"label": _("Accounts Payable"),
			"value": flt(ap),
			"delta_pct": None,
			"sparkline": [],
		},
		{
			"id": "pending_approvals",
			"label": _("Pending Approvals"),
			"value": pending_total,
			"delta_pct": None,
			"sparkline": [],
			"urgent_count": je_d,
		},
		{
			"id": "unreconciled",
			"label": _("Unreconciled Transactions"),
			"value": unreconciled_n,
			"delta_pct": None,
			"sparkline": [],
			"subtitle_amount": unreconciled_amt,
		},
		{
			"id": "pnl",
			"label": _("This Month Profit/Loss"),
			"value": pl,
			"delta_pct": pct_change(pl, pl_prev),
			"sparkline": [],
		},
	]


def _daily_net_cash_series(account_names, company, end_date, days=14):
	"""Last `days` ending at end_date: daily (debit - credit) on cash/bank GL."""
	if not account_names:
		return []
	start_series = end_date - timedelta(days=days - 1)
	rows = frappe.db.sql(
		f"""
		select posting_date,
			coalesce(sum(debit),0) - coalesce(sum(credit),0) as net
		from `tabGL Entry`
		where company=%s and posting_date between %s and %s
		and account in ({",".join(["%s"] * len(account_names))})
		and is_cancelled=0
		group by posting_date
		order by posting_date asc
		""",
		tuple([company, start_series, end_date, *account_names]),
		as_dict=False,
	)
	by_day = {r[0]: flt(r[1]) for r in rows}
	out = []
	d = start_series
	while d <= end_date:
		out.append(flt(by_day.get(d, 0)))
		d += timedelta(days=1)
	return out


def _profit_loss_simple(company, start, end):
	"""Income credit minus expense debit for the interval (simplified)."""
	inc = frappe.db.sql(
		"""
		select sum(credit) - sum(debit)
		from `tabGL Entry` gle
		inner join `tabAccount` a on a.name = gle.account
		where gle.company=%s and gle.posting_date between %s and %s
		and gle.is_cancelled=0
		and a.root_type = 'Income'
		""",
		(company, start, end),
	)[0][0]
	exp = frappe.db.sql(
		"""
		select sum(debit) - sum(credit)
		from `tabGL Entry` gle
		inner join `tabAccount` a on a.name = gle.account
		where gle.company=%s and gle.posting_date between %s and %s
		and gle.is_cancelled=0
		and a.root_type = 'Expense'
		""",
		(company, start, end),
	)[0][0]
	return flt(inc) - flt(exp)


def _tasks(company):
	tasks = []
	je_d = frappe.db.count("Journal Entry", {"company": company, "docstatus": 0})
	if je_d:
		tasks.append(
			{
				"title": _("Submit draft journal entries"),
				"count": je_d,
				"priority": "high",
				"route": "/app/journal-entry",
			}
		)
	pe_d = frappe.db.count("Payment Entry", {"company": company, "docstatus": 0})
	if pe_d:
		tasks.append(
			{
				"title": _("Review draft payments"),
				"count": pe_d,
				"priority": "medium",
				"route": "/app/payment-entry",
			}
		)
	return tasks


def _cash_in_out_series(company, from_date, to_date):
	accounts = _cash_account_names(company)
	if not accounts:
		return {"labels": [], "inflow": [], "outflow": []}

	rows = frappe.db.sql(
		f"""
		select posting_date,
			sum(debit) as ind,
			sum(credit) as outd
		from `tabGL Entry`
		where company=%s and posting_date between %s and %s
		and account in ({",".join(["%s"] * len(accounts))})
		and is_cancelled=0
		group by posting_date
		order by posting_date asc
		""",
		tuple([company, from_date, to_date, *accounts]),
		as_dict=True,
	)
	return {
		"labels": [str(r.posting_date) for r in rows],
		"inflow": [flt(r.ind) for r in rows],
		"outflow": [flt(r.outd) for r in rows],
	}


def _expense_breakdown(company, from_date, to_date):
	rows = frappe.db.sql(
		"""
		select a.account_name as name,
			sum(gle.debit) - sum(gle.credit) as value
		from `tabGL Entry` gle
		inner join `tabAccount` a on a.name = gle.account
		where gle.company=%s and gle.posting_date between %s and %s
		and gle.is_cancelled=0
		and a.root_type = 'Expense'
		and a.is_group = 0
		group by a.account_name
		order by value desc
		limit 8
		""",
		(company, from_date, to_date),
		as_dict=True,
	)
	total = sum(flt(r.value) for r in rows) or 1.0
	for r in rows:
		r["pct"] = round(flt(r.value) / total * 100, 1)
	return rows


def _recent_gl(company, limit=8):
	return frappe.get_list(
		"GL Entry",
		filters={"company": company, "is_cancelled": 0},
		fields=[
			"posting_date",
			"voucher_type",
			"voucher_no",
			"account",
			"party_type",
			"party",
			"debit",
			"credit",
		],
		order_by="modified desc",
		limit_page_length=limit,
	)


def _due_payables(company, limit=6):
	return frappe.get_list(
		"Purchase Invoice",
		filters={"company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "supplier", "due_date", "outstanding_amount", "status"],
		order_by="due_date asc",
		limit_page_length=limit,
	)


def _alerts(company):
	alerts = []
	overdue = frappe.db.sql(
		"""
		select count(*) from `tabPurchase Invoice`
		where company=%s and docstatus=1 and outstanding_amount > 0
		and due_date < CURDATE()
		""",
		company,
	)[0][0]
	if overdue:
		alerts.append(
			{
				"category": _("Payables"),
				"title": _("Overdue bills"),
				"detail": _("{0} invoices overdue").format(int(overdue)),
				"severity": "high",
			}
		)
	bt = frappe.db.count(
		"Bank Transaction",
		filters={"company": company, "status": "Pending"},
	)
	if bt:
		alerts.append(
			{
				"category": _("Bank"),
				"title": _("Pending bank lines"),
				"detail": _("{0} to reconcile").format(bt),
				"severity": "medium",
			}
		)
	return alerts


def _je_type_bucket(voucher_type: str | None) -> str:
	vt = voucher_type or "Journal Entry"
	adjusting = {
		"Depreciation Entry",
		"Write Off Entry",
		"Deferred Revenue",
		"Deferred Expense",
		"Excise Entry",
		"Exchange Rate Revaluation",
		"Exchange Gain Or Loss",
	}
	reversing = {"Debit Note", "Credit Note"}
	closing = {"Opening Entry"}
	if vt in adjusting:
		return "Adjusting"
	if vt in reversing:
		return "Reversing"
	if vt in closing:
		return "Closing"
	return "General"


def _je_period_agg(company, start, end):
	row = frappe.db.sql(
		"""
		select
			count(*) as total,
			coalesce(sum(case when docstatus = 1 then 1 else 0 end), 0) as posted,
			coalesce(sum(case when docstatus = 0 then 1 else 0 end), 0) as draft,
			coalesce(sum(case when docstatus = 1 then total_debit else 0 end), 0) as total_debit,
			coalesce(sum(case when docstatus = 1 then total_credit else 0 end), 0) as total_credit
		from `tabJournal Entry`
		where company = %s and posting_date between %s and %s
		""",
		(company, start, end),
		as_dict=True,
	)
	return row[0] if row else {}


def _pct_delta(cur, prev):
	if prev == 0:
		return round(100.0 if cur else 0.0, 1)
	return round((cur - prev) / abs(prev) * 100, 1)


@frappe.whitelist()
def journal_entries_dashboard(
	company=None,
	from_date=None,
	to_date=None,
	status=None,
	voucher_type=None,
	owner=None,
	search=None,
	limit_start=None,
	limit_page_length=None,
):
	"""Journal Entries workbench page: KPIs, type breakdown, paginated list."""
	if not frappe.has_permission("Journal Entry", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = company or frappe.defaults.get_user_default("Company") or _first_company()
	if not company:
		frappe.throw(_("No Company found"))

	from_date = _parse_range_date(from_date)
	to_date = _parse_range_date(to_date)
	if from_date > to_date:
		from_date, to_date = to_date, from_date

	prev_span = (to_date - from_date).days + 1
	prev_end = from_date - timedelta(days=1)
	prev_start = prev_end - timedelta(days=prev_span - 1)

	cur = _je_period_agg(company, from_date, to_date)
	prev = _je_period_agg(company, prev_start, prev_end)

	t_total = int(cur.get("total") or 0)
	t_posted = int(cur.get("posted") or 0)
	t_draft = int(cur.get("draft") or 0)
	t_deb = flt(cur.get("total_debit"))
	t_cred = flt(cur.get("total_credit"))

	p_total = int(prev.get("total") or 0)
	p_posted = int(prev.get("posted") or 0)
	p_draft = int(prev.get("draft") or 0)
	p_deb = flt(prev.get("total_debit"))
	p_cred = flt(prev.get("total_credit"))

	kpis = [
		{
			"id": "total",
			"label": _("Total Journal Entries"),
			"value": t_total,
			"delta_pct": _pct_delta(t_total, p_total),
			"format": "int",
		},
		{
			"id": "posted",
			"label": _("Posted Entries"),
			"value": t_posted,
			"delta_pct": _pct_delta(t_posted, p_posted),
			"format": "int",
		},
		{
			"id": "draft",
			"label": _("Draft Entries"),
			"value": t_draft,
			"delta_pct": _pct_delta(t_draft, p_draft),
			"format": "int",
		},
		{
			"id": "debit",
			"label": _("Total Debit"),
			"value": t_deb,
			"delta_pct": _pct_delta(t_deb, p_deb),
			"format": "money",
		},
		{
			"id": "credit",
			"label": _("Total Credit"),
			"value": t_cred,
			"delta_pct": _pct_delta(t_cred, p_cred),
			"format": "money",
		},
	]

	rows_vt = frappe.db.sql(
		"""
		select voucher_type, count(*) as c
		from `tabJournal Entry`
		where company = %s and posting_date between %s and %s and docstatus = 1
		group by voucher_type
		""",
		(company, from_date, to_date),
		as_dict=True,
	)
	buckets = {"General": 0, "Adjusting": 0, "Reversing": 0, "Closing": 0}
	for r in rows_vt:
		buckets[_je_type_bucket(r.voucher_type)] += int(r.c or 0)

	type_total = sum(buckets.values()) or 1
	by_type = []
	for name in ("General", "Adjusting", "Reversing", "Closing"):
		v = buckets[name]
		if not v:
			continue
		by_type.append(
			{
				"name": name,
				"value": float(v),
				"pct": round(v / type_total * 100, 1),
			}
		)

	currency = frappe.db.get_value("Company", company, "default_currency") or ""

	meta = frappe.get_meta("Journal Entry")
	vt_field = meta.get_field("voucher_type")
	voucher_types = []
	if vt_field and vt_field.options:
		voucher_types = [x.strip() for x in vt_field.options.split("\n") if x.strip()]

	owners = [
		r[0]
		for r in frappe.db.sql(
			"""
			select distinct owner from `tabJournal Entry`
			where company = %s
			order by owner asc
			limit 200
			""",
			company,
		)
	]

	filters: dict = {
		"company": company,
		"posting_date": ["between", [from_date, to_date]],
	}
	st = (status or "").strip().lower()
	if st == "posted":
		filters["docstatus"] = 1
	elif st == "draft":
		filters["docstatus"] = 0

	if voucher_type:
		filters["voucher_type"] = voucher_type
	if owner:
		filters["owner"] = owner

	or_filters = []
	if search and str(search).strip():
		term = str(search).strip()
		wild = f"%{term}%"
		or_filters = [["name", "like", wild], ["user_remark", "like", wild]]

	ls = int(limit_start or 0)
	lp = int(limit_page_length or 8)
	lp = min(max(lp, 1), 100)

	entries = frappe.get_list(
		"Journal Entry",
		filters=filters,
		or_filters=or_filters or None,
		fields=[
			"name",
			"posting_date",
			"voucher_type",
			"docstatus",
			"total_debit",
			"total_credit",
			"owner",
			"user_remark",
			"bill_no",
		],
		order_by="posting_date desc, modified desc",
		limit_start=ls,
		limit_page_length=lp,
	)

	partial_query = DatabaseQuery("Journal Entry").execute(
		filters=filters,
		or_filters=or_filters or [],
		fields=["`tabJournal Entry`.name"],
		order_by="posting_date desc",
		limit_start=0,
		limit_page_length=None,
		run=False,
	)
	total_rows = int(frappe.db.sql(f"select count(*) from ({partial_query}) _awb_je_cnt")[0][0])

	parents = [e["name"] for e in entries]
	first_acc = {}
	if parents:
		acc_rows = frappe.db.sql(
			"""
			select jea.parent, jea.account
			from `tabJournal Entry Account` jea
			inner join (
				select parent, min(idx) as midx
				from `tabJournal Entry Account`
				where parent in ({})
				group by parent
			) x on x.parent = jea.parent and x.midx = jea.idx
			""".format(",".join(["%s"] * len(parents))),
			tuple(parents),
			as_dict=False,
		)
		first_acc = {a[0]: a[1] for a in acc_rows}

	for e in entries:
		ref = e.get("user_remark") or e.get("bill_no") or ""
		e["reference"] = ref
		e["first_account"] = first_acc.get(e["name"]) or ""

	return {
		"company": company,
		"currency": currency,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"previous_period_label": _human_date_range(prev_start, prev_end),
		"kpis": kpis,
		"by_type": by_type,
		"posted_total_for_chart": int(type_total) if sum(buckets.values()) else 0,
		"entries": entries,
		"total_rows": int(total_rows),
		"voucher_types": voucher_types,
		"owners": owners,
	}
