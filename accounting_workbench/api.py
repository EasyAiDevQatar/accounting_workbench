# Copyright (c) 2026, Author and contributors
# For license information, please see license.txt

import json
from datetime import date, datetime, timedelta

import frappe
import frappe.sessions
from frappe import _
from frappe.model.db_query import DatabaseQuery
from frappe.utils import cint, flt, getdate


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
				"route": "/journal",
			}
		)
	pe_d = frappe.db.count("Payment Entry", {"company": company, "docstatus": 0})
	if pe_d:
		tasks.append(
			{
				"title": _("Review draft payments"),
				"count": pe_d,
				"priority": "medium",
				"route": "/payments",
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
def journal_entry_form_meta(company=None):
	"""Naming series and voucher types for the workbench Journal Entry modal."""
	if not frappe.has_permission("Journal Entry", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = company or frappe.defaults.get_user_default("Company") or _first_company()
	meta = frappe.get_meta("Journal Entry")
	ns_field = meta.get_field("naming_series")
	naming_series = []
	if ns_field and ns_field.options:
		naming_series = [x.strip() for x in ns_field.options.split("\n") if x.strip()]
	vt_field = meta.get_field("voucher_type")
	voucher_types = []
	if vt_field and vt_field.options:
		voucher_types = [x.strip() for x in vt_field.options.split("\n") if x.strip()]

	currency = frappe.db.get_value("Company", company, "default_currency") or ""

	return {
		"company": company,
		"currency": currency,
		"naming_series": naming_series,
		"voucher_types": voucher_types,
	}


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

@frappe.whitelist()
def get_coa_tree(company):
	"""Returns the full Chart of Accounts tree for a company."""
	if not frappe.has_permission("Account", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	accounts = frappe.get_all("Account", 
		filters={"company": company},
		fields=["name", "account_name", "parent_account", "is_group", "root_type", "account_type", "account_currency"],
		order_by="lft"
	)
	
	# Build tree
	tree = []
	acc_map = {}
	for acc in accounts:
		acc["children"] = []
		acc_map[acc.name] = acc
		
	for acc in accounts:
		if acc.parent_account and acc.parent_account in acc_map:
			acc_map[acc.parent_account]["children"].append(acc)
		else:
			tree.append(acc)
			
	return tree

@frappe.whitelist()
def get_party_outstanding(party_type, party, company):
	"""Fetches unpaid invoices for a party."""
	from erpnext.accounts.utils import get_outstanding_invoices
	return get_outstanding_invoices(party_type, party, company)

@frappe.whitelist()
def submit_invoice(data):
	"""Unified endpoint to create and submit an invoice."""
	import json
	if isinstance(data, str):
		data = json.loads(data)
		
	doctype = "Sales Invoice" if data.get("type") == "Sales" else "Purchase Invoice"
	
	doc = frappe.new_doc(doctype)
	doc.company = data.get("company")
	if doctype == "Sales Invoice":
		doc.customer = data.get("party")
	else:
		doc.supplier = data.get("party")
		
	doc.posting_date = data.get("posting_date") or frappe.utils.today()
	doc.due_date = data.get("due_date")
	
	for item in data.get("items", []):
		doc.append("items", {
			"item_code": item.get("item_code"),
			"qty": item.get("qty"),
			"rate": item.get("rate"),
			"cost_center": item.get("cost_center")
		})
		
	if data.get("taxes_and_charges"):
		doc.taxes_and_charges = data.get("taxes_and_charges")
		doc.set_taxes()
		
	doc.save()
	doc.submit()
	return doc.name

@frappe.whitelist()
def create_payment_with_allocation(data):
	"""Creates a Payment Entry and allocates it to invoices."""
	import json
	if isinstance(data, str):
		data = json.loads(data)
		
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = data.get("payment_type") # "Receive" or "Pay"
	pe.company = data.get("company")
	pe.posting_date = data.get("posting_date") or frappe.utils.today()
	pe.mode_of_payment = data.get("mode_of_payment")
	pe.party_type = data.get("party_type")
	pe.party = data.get("party")
	pe.paid_amount = data.get("paid_amount")
	pe.received_amount = data.get("received_amount")
	
	if pe.payment_type == "Receive":
		pe.paid_to = data.get("bank_account")
	else:
		pe.paid_from = data.get("bank_account")
		
	# ERPNext helper to set missing values
	pe.setup_party_account_field()
	pe.set_missing_values()
	
	for alloc in data.get("allocations", []):
		pe.append("references", {
			"reference_doctype": alloc.get("voucher_type"),
			"reference_name": alloc.get("voucher_no"),
			"allocated_amount": alloc.get("allocated_amount")
		})
		
	pe.save()
	pe.submit()
	return pe.name

@frappe.whitelist()
def submit_journal_entry(data):
	"""Validates and submits a Journal Entry."""
	import json
	from frappe.utils import flt
	
	if isinstance(data, str):
		data = json.loads(data)
		
	je = frappe.new_doc("Journal Entry")
	je.company = data.get("company")
	je.posting_date = data.get("posting_date") or frappe.utils.today()
	je.voucher_type = data.get("voucher_type", "Journal Entry")
	je.user_remark = data.get("user_remark")
	
	total_debit = 0
	total_credit = 0
	
	for acc in data.get("accounts", []):
		debit = flt(acc.get("debit", 0))
		credit = flt(acc.get("credit", 0))
		total_debit += debit
		total_credit += credit
		
		je.append("accounts", {
			"account": acc.get("account"),
			"party_type": acc.get("party_type"),
			"party": acc.get("party"),
			"debit_in_account_currency": debit,
			"credit_in_account_currency": credit,
			"cost_center": acc.get("cost_center")
		})
		
	if abs(total_debit - total_credit) > 0.001:
		frappe.throw(_("Total Debit must equal Total Credit"))
		
	je.save()
	je.submit()
	return je.name


def _resolve_company(company=None):
	return company or frappe.defaults.get_user_default("Company") or _first_company()


def _invoice_doctype(invoice_type):
	return "Purchase Invoice" if (invoice_type or "").strip().lower() in {"purchase", "bill", "bills"} else "Sales Invoice"


def _invoice_party_field(doctype):
	return "supplier" if doctype == "Purchase Invoice" else "customer"


def _status_to_filter(status):
	st = (status or "").strip().lower()
	if st == "draft":
		return {"docstatus": 0}
	if st in {"submitted", "posted"}:
		return {"docstatus": 1}
	if st in {"cancelled", "canceled"}:
		return {"docstatus": 2}
	return {}


@frappe.whitelist()
def coa_workspace(company=None):
	"""Chart of Accounts tree + account balances for the selected company."""
	company = _resolve_company(company)
	if not company:
		return {"company": None, "currency": "", "tree": [], "summary": {}}
	if not frappe.has_permission("Account", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	tree = get_coa_tree(company)
	currency = frappe.db.get_value("Company", company, "default_currency") or ""

	balance_rows = frappe.db.sql(
		"""
		select account, coalesce(sum(debit), 0) - coalesce(sum(credit), 0) as balance
		from `tabGL Entry`
		where company = %s and is_cancelled = 0
		group by account
		""",
		company,
		as_dict=True,
	)
	balance_map = {r.account: flt(r.balance) for r in balance_rows}

	total_accounts = 0
	leaf_accounts = 0

	def attach_balance(nodes):
		nonlocal total_accounts, leaf_accounts
		for node in nodes:
			total_accounts += 1
			if not cint(node.get("is_group")):
				leaf_accounts += 1
			node["balance"] = flt(balance_map.get(node.get("name"), 0))
			children = node.get("children") or []
			if children:
				attach_balance(children)

	attach_balance(tree)

	return {
		"company": company,
		"currency": currency,
		"tree": tree,
		"summary": {
			"total_accounts": total_accounts,
			"leaf_accounts": leaf_accounts,
			"group_accounts": total_accounts - leaf_accounts,
		},
	}


@frappe.whitelist()
def invoice_workspace(
	invoice_type="Sales",
	company=None,
	party=None,
	status=None,
	from_date=None,
	to_date=None,
	search=None,
	limit_start=None,
	limit_page_length=None,
):
	"""Invoice list payload for Sales/Purchase with ERPNext-compatible fields."""
	doctype = _invoice_doctype(invoice_type)
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	if not company:
		frappe.throw(_("No Company found"))
	party_field = _invoice_party_field(doctype)

	from_date = _parse_range_date(from_date)
	to_date = _parse_range_date(to_date)
	if from_date > to_date:
		from_date, to_date = to_date, from_date

	filters = {
		"company": company,
		"posting_date": ["between", [from_date, to_date]],
	}
	filters.update(_status_to_filter(status))
	if party:
		filters[party_field] = party

	or_filters = None
	if search and str(search).strip():
		wild = f"%{str(search).strip()}%"
		or_filters = [["name", "like", wild], [party_field, "like", wild]]

	ls = int(limit_start or 0)
	lp = min(max(int(limit_page_length or 20), 1), 100)

	fields = [
		"name",
		"posting_date",
		"due_date",
		party_field,
		"grand_total",
		"outstanding_amount",
		"currency",
		"status",
		"docstatus",
	]
	rows = frappe.get_list(
		doctype,
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="posting_date desc, modified desc",
		limit_start=ls,
		limit_page_length=lp,
	)

	for r in rows:
		r["party"] = r.get(party_field)
		r["invoice_type"] = "Purchase" if doctype == "Purchase Invoice" else "Sales"

	partial_query = DatabaseQuery(doctype).execute(
		filters=filters,
		or_filters=or_filters or [],
		fields=[f"`tab{doctype}`.name"],
		order_by="posting_date desc",
		limit_start=0,
		limit_page_length=None,
		run=False,
	)
	total_rows = int(frappe.db.sql(f"select count(*) from ({partial_query}) _awb_inv_cnt")[0][0])

	return {
		"company": company,
		"currency": frappe.db.get_value("Company", company, "default_currency") or "",
		"invoice_type": "Purchase" if doctype == "Purchase Invoice" else "Sales",
		"from_date": str(from_date),
		"to_date": str(to_date),
		"entries": rows,
		"total_rows": total_rows,
	}


@frappe.whitelist()
def invoice_form_meta(invoice_type="Sales", company=None):
	"""Metadata required to create Sales/Purchase invoices with child tables."""
	doctype = _invoice_doctype(invoice_type)
	if not frappe.has_permission(doctype, "create"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	party_doctype = "Supplier" if doctype == "Purchase Invoice" else "Customer"
	tax_template_doctype = (
		"Purchase Taxes and Charges Template"
		if doctype == "Purchase Invoice"
		else "Sales Taxes and Charges Template"
	)

	parties = frappe.get_list(party_doctype, fields=["name"], limit_page_length=200, order_by="name asc")
	items = frappe.get_list("Item", fields=["name", "item_name", "stock_uom"], limit_page_length=200, order_by="name asc")
	cost_centers = frappe.get_list(
		"Cost Center",
		filters={"company": company, "is_group": 0},
		fields=["name"],
		limit_page_length=200,
		order_by="name asc",
	)
	tax_templates = frappe.get_list(
		tax_template_doctype,
		fields=["name"],
		limit_page_length=200,
		order_by="name asc",
	)

	return {
		"company": company,
		"currency": frappe.db.get_value("Company", company, "default_currency") or "",
		"invoice_type": "Purchase" if doctype == "Purchase Invoice" else "Sales",
		"party_doctype": party_doctype,
		"tax_template_doctype": tax_template_doctype,
		"parties": parties,
		"items": items,
		"cost_centers": cost_centers,
		"tax_templates": tax_templates,
	}


@frappe.whitelist()
def payment_workspace(
	company=None,
	party_type=None,
	party=None,
	payment_type=None,
	from_date=None,
	to_date=None,
	limit_start=None,
	limit_page_length=None,
):
	"""Payment list plus party outstanding references for allocation UI."""
	if not frappe.has_permission("Payment Entry", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	if not company:
		frappe.throw(_("No Company found"))

	from_date = _parse_range_date(from_date)
	to_date = _parse_range_date(to_date)
	if from_date > to_date:
		from_date, to_date = to_date, from_date

	filters = {"company": company, "posting_date": ["between", [from_date, to_date]]}
	if payment_type:
		filters["payment_type"] = payment_type
	if party_type:
		filters["party_type"] = party_type
	if party:
		filters["party"] = party

	ls = int(limit_start or 0)
	lp = min(max(int(limit_page_length or 20), 1), 100)
	entries = frappe.get_list(
		"Payment Entry",
		filters=filters,
		fields=[
			"name",
			"posting_date",
			"payment_type",
			"party_type",
			"party",
			"paid_from",
			"paid_to",
			"paid_amount",
			"received_amount",
			"docstatus",
			"status",
		],
		order_by="posting_date desc, modified desc",
		limit_start=ls,
		limit_page_length=lp,
	)
	total_rows = frappe.db.count("Payment Entry", filters=filters)

	outstanding = []
	if party_type and party:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents

		outstanding = get_outstanding_reference_documents(
			{
				"company": company,
				"party_type": party_type,
				"party": party,
				"payment_type": payment_type or "Receive",
				"get_outstanding_invoices": 1,
			}
		)

	mode_of_payments = frappe.get_list("Mode of Payment", fields=["name"], limit_page_length=200, order_by="name asc")
	bank_accounts = frappe.get_list(
		"Account",
		filters={"company": company, "is_group": 0, "account_type": ["in", ["Bank", "Cash"]]},
		fields=["name", "account_name", "account_type"],
		limit_page_length=500,
		order_by="name asc",
	)
	customers = frappe.get_list("Customer", fields=["name"], limit_page_length=200, order_by="name asc")
	suppliers = frappe.get_list("Supplier", fields=["name"], limit_page_length=200, order_by="name asc")

	return {
		"company": company,
		"currency": frappe.db.get_value("Company", company, "default_currency") or "",
		"from_date": str(from_date),
		"to_date": str(to_date),
		"entries": entries,
		"total_rows": total_rows,
		"outstanding": outstanding or [],
		"options": {
			"mode_of_payments": mode_of_payments,
			"bank_accounts": bank_accounts,
			"customers": customers,
			"suppliers": suppliers,
		},
	}


def _resolve_date_range(from_date=None, to_date=None):
	from_dt = _parse_range_date(from_date)
	to_dt = _parse_range_date(to_date)
	if from_dt > to_dt:
		from_dt, to_dt = to_dt, from_dt
	return from_dt, to_dt


@frappe.whitelist()
def bank_reconciliation_workspace(company=None, from_date=None, to_date=None, status=None, limit_page_length=None):
	"""Bank reconciliation cockpit data based on Bank Transaction."""
	if not frappe.has_permission("Bank Transaction", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	from_dt, to_dt = _resolve_date_range(from_date, to_date)
	filters = {"company": company, "date": ["between", [from_dt, to_dt]]}
	if status:
		filters["status"] = status

	limit = min(max(int(limit_page_length or 100), 1), 500)
	entries = frappe.get_list(
		"Bank Transaction",
		filters=filters,
		fields=[
			"name",
			"date",
			"bank_account",
			"description",
			"deposit",
			"withdrawal",
			"unallocated_amount",
			"status",
		],
		order_by="date desc, modified desc",
		limit_page_length=limit,
	)

	pending_count = frappe.db.count("Bank Transaction", {"company": company, "status": "Pending"})
	unreconciled_count = frappe.db.count("Bank Transaction", {"company": company, "status": "Unreconciled"})
	unallocated_total = (
		frappe.db.sql(
			"""
			select coalesce(sum(unallocated_amount), 0)
			from `tabBank Transaction`
			where company=%s and status in ('Pending', 'Unreconciled')
			""",
			company,
		)[0][0]
		or 0
	)

	return {
		"company": company,
		"currency": frappe.db.get_value("Company", company, "default_currency") or "",
		"from_date": str(from_dt),
		"to_date": str(to_dt),
		"kpis": {
			"pending_count": int(pending_count or 0),
			"unreconciled_count": int(unreconciled_count or 0),
			"unallocated_total": flt(unallocated_total),
			"in_period_count": len(entries),
		},
		"entries": entries,
		"statuses": ["Pending", "Unreconciled", "Reconciled"],
	}


@frappe.whitelist()
def budget_workspace(company=None, fiscal_year=None, limit_page_length=None):
	"""Budget workspace data (kpis + list) for budget control page."""
	if not frappe.has_permission("Budget", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	filters = {"company": company}
	if fiscal_year:
		filters["fiscal_year"] = fiscal_year

	limit = min(max(int(limit_page_length or 100), 1), 500)
	budgets = frappe.get_list(
		"Budget",
		filters=filters,
		fields=["name", "fiscal_year", "action_if_annual_budget_exceeded", "applicable_on_material_request", "docstatus"],
		order_by="modified desc",
		limit_page_length=limit,
	)

	submitted = sum(1 for b in budgets if cint(b.get("docstatus")) == 1)
	drafts = sum(1 for b in budgets if cint(b.get("docstatus")) == 0)

	return {
		"company": company,
		"fiscal_year": fiscal_year,
		"kpis": {
			"total_budgets": len(budgets),
			"submitted_budgets": submitted,
			"draft_budgets": drafts,
		},
		"entries": budgets,
		"fiscal_years": frappe.get_list("Fiscal Year", fields=["name"], order_by="year_start_date desc", limit_page_length=200),
	}


@frappe.whitelist()
def period_close_workspace(company=None, from_date=None, to_date=None, limit_page_length=None):
	"""Period close page payload from Period Closing Voucher and Accounting Period."""
	if not frappe.has_permission("Period Closing Voucher", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	from_dt, to_dt = _resolve_date_range(from_date, to_date)
	limit = min(max(int(limit_page_length or 100), 1), 500)

	vouchers = frappe.get_list(
		"Period Closing Voucher",
		filters={"company": company, "posting_date": ["between", [from_dt, to_dt]]},
		fields=["name", "posting_date", "fiscal_year", "period_start_date", "period_end_date", "docstatus"],
		order_by="posting_date desc",
		limit_page_length=limit,
	)
	periods = frappe.get_list(
		"Accounting Period",
		fields=["name", "start_date", "end_date", "closed"],
		order_by="start_date desc",
		limit_page_length=limit,
	)

	return {
		"company": company,
		"from_date": str(from_dt),
		"to_date": str(to_dt),
		"kpis": {
			"period_close_vouchers": len(vouchers),
			"submitted_vouchers": sum(1 for x in vouchers if cint(x.get("docstatus")) == 1),
			"closed_periods": sum(1 for p in periods if cint(p.get("closed")) == 1),
		},
		"vouchers": vouchers,
		"accounting_periods": periods,
	}


@frappe.whitelist()
def settings_workspace(company=None):
	"""Settings data for Company, Fiscal Year and Accounting Dimensions defaults."""
	if not frappe.has_permission("Company", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	company = _resolve_company(company)
	company_doc = frappe.get_doc("Company", company) if company else None
	active_fy = frappe.db.get_value(
		"Fiscal Year",
		{"year_start_date": ["<=", getdate()], "year_end_date": [">=", getdate()]},
		"name",
		order_by="year_start_date desc",
	)
	dimensions = frappe.get_list(
		"Accounting Dimension",
		fields=["name", "document_type", "disabled"],
		order_by="creation asc",
		limit_page_length=200,
	)

	return {
		"company": company,
		"company_defaults": {
			"default_currency": getattr(company_doc, "default_currency", None),
			"country": getattr(company_doc, "country", None),
			"cost_center": getattr(company_doc, "cost_center", None),
		},
		"active_fiscal_year": active_fy,
		"dimensions": dimensions,
		"fiscal_years": frappe.get_list("Fiscal Year", fields=["name", "year_start_date", "year_end_date"], order_by="year_start_date desc", limit_page_length=200),
		"companies": frappe.get_list("Company", fields=["name"], order_by="name asc", limit_page_length=200),
	}


_ACCOUNTS_REPORT_ALLOWLIST = {
	"General Ledger",
	"Trial Balance",
	"Profit and Loss Statement",
	"Balance Sheet",
	"Cash Flow",
	"Accounts Receivable",
	"Accounts Payable",
}


@frappe.whitelist()
def reports_explorer_meta(company=None):
	"""Report explorer metadata including allowlisted report names."""
	company = _resolve_company(company)
	return {
		"company": company,
		"reports": sorted(_ACCOUNTS_REPORT_ALLOWLIST),
		"companies": frappe.get_list("Company", fields=["name"], order_by="name asc", limit_page_length=200),
	}


@frappe.whitelist()
def run_accounts_report(report_name, filters=None):
	"""Run allowlisted accounts reports using ERPNext report runner."""
	if report_name not in _ACCOUNTS_REPORT_ALLOWLIST:
		frappe.throw(_("Report not allowed"))
	if not frappe.has_permission("Report", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if isinstance(filters, str):
		import json

		filters = json.loads(filters)
	filters = filters or {}

	from frappe.desk.query_report import run

	return run(report_name=report_name, filters=filters)


_DESKLESS_DOCTYPES = {
	"Sales Invoice",
	"Purchase Invoice",
	"Payment Entry",
	"Journal Entry",
	"Budget",
	"Period Closing Voucher",
	"Bank Transaction",
	"Customer",
	"Supplier",
	"Bank Account",
	"Fiscal Year",
	"Accounting Dimension",
	"Account",
	"Company",
	"Accounting Period",
}

_FIELDTYPE_SKIP = {
	"Section Break",
	"Column Break",
	"Tab Break",
	"Button",
	"Read Only",
	"HTML",
	"Heading",
	"Fold",
}


def _parse_json_like(value, default):
	if value is None:
		return default
	if isinstance(value, str):
		raw = value.strip()
		if not raw:
			return default
		return json.loads(raw)
	return value


def _assert_supported_doctype(doctype):
	if doctype not in _DESKLESS_DOCTYPES:
		frappe.throw(_("Unsupported doctype: {0}").format(doctype))


def _link_options_for_field(df, company=None):
	if df.fieldtype != "Link" or not df.options:
		return []
	if df.options.startswith("[") or df.options.startswith("dynamic"):
		return []
	link_doctype = df.options
	if not frappe.db.exists("DocType", link_doctype):
		return []
	if not frappe.has_permission(link_doctype, "read"):
		return []

	filters = {}
	if company and frappe.db.has_column(link_doctype, "company"):
		filters["company"] = company

	try:
		return frappe.get_list(link_doctype, filters=filters, fields=["name"], order_by="modified desc", limit_page_length=200)
	except Exception:
		return []


def _field_payload(df, company=None):
	default_value = df.default
	if isinstance(default_value, str):
		raw_default = default_value.strip()
		# Ignore unresolved dynamic placeholders like ":Company" in deskless forms.
		if raw_default.startswith(":"):
			default_value = ""
		else:
			default_value = raw_default
	return {
		"fieldname": df.fieldname,
		"label": df.label or df.fieldname,
		"fieldtype": df.fieldtype,
		"options": df.options,
		"reqd": cint(df.reqd),
		"default": default_value,
		"options_list": _link_options_for_field(df, company=company),
	}


def _required_parent_fields(meta, company=None):
	fields = []
	for df in meta.fields:
		if not df.fieldname:
			continue
		if df.fieldtype in _FIELDTYPE_SKIP:
			continue
		if df.fieldtype == "Table":
			continue
		if cint(df.reqd):
			fields.append(_field_payload(df, company=company))
	return fields


def _required_child_tables(meta, company=None):
	tables = []
	for df in meta.fields:
		if df.fieldtype != "Table" or not df.options:
			continue
		child_meta = frappe.get_meta(df.options)
		required_child_fields = []
		for cdf in child_meta.fields:
			if not cdf.fieldname:
				continue
			if cdf.fieldtype in _FIELDTYPE_SKIP or cdf.fieldtype == "Table":
				continue
			if cint(cdf.reqd):
				required_child_fields.append(_field_payload(cdf, company=company))
		if required_child_fields:
			tables.append(
				{
					"fieldname": df.fieldname,
					"label": df.label or df.fieldname,
					"child_doctype": df.options,
					"fields": required_child_fields,
				}
			)
	return tables


def _default_list_fields(meta):
	candidate = ["name"]
	preferred = ["posting_date", "due_date", "status", "docstatus", "owner", "modified", "company", "customer", "supplier", "party"]
	fieldnames = {f.fieldname for f in meta.fields if f.fieldname and f.fieldtype not in _FIELDTYPE_SKIP and f.fieldtype != "Table"}
	for fname in preferred:
		if fname in fieldnames and fname not in candidate:
			candidate.append(fname)
	for f in meta.fields:
		if len(candidate) >= 8:
			break
		if not f.fieldname or f.fieldname in candidate:
			continue
		if f.fieldtype in _FIELDTYPE_SKIP or f.fieldtype == "Table":
			continue
		if f.fieldtype in {"Data", "Link", "Select", "Date", "Currency", "Float", "Int", "Check"}:
			candidate.append(f.fieldname)
	return candidate


@frappe.whitelist()
def doctype_required_meta(doctype, company=None):
	"""Required field metadata for deskless create pages."""
	_assert_supported_doctype(doctype)
	if not frappe.has_permission(doctype, "create"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	meta = frappe.get_meta(doctype)
	return {
		"doctype": doctype,
		"title_field": meta.title_field,
		"required_fields": _required_parent_fields(meta, company=company),
		"required_child_tables": _required_child_tables(meta, company=company),
	}


@frappe.whitelist()
def list_doctype_workspace(
	doctype,
	filters=None,
	search=None,
	limit_start=None,
	limit_page_length=None,
	order_by=None,
):
	"""Generic list endpoint for deskless module list pages."""
	_assert_supported_doctype(doctype)
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	filters = _parse_json_like(filters, {}) or {}
	search = (search or "").strip()
	limit_start = int(limit_start or 0)
	limit_page_length = min(max(int(limit_page_length or 50), 1), 200)
	order_by = order_by or "modified desc"

	meta = frappe.get_meta(doctype)
	fields = _default_list_fields(meta)
	or_filters = None
	if search:
		or_filters = [["name", "like", f"%{search}%"]]
		if meta.title_field and meta.title_field != "name":
			or_filters.append([meta.title_field, "like", f"%{search}%"])

	rows = frappe.get_list(
		doctype,
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by=order_by,
		limit_start=limit_start,
		limit_page_length=limit_page_length,
	)
	total_rows = frappe.db.count(doctype, filters=filters)
	return {"doctype": doctype, "fields": fields, "rows": rows, "total_rows": total_rows}


@frappe.whitelist()
def save_doctype_doc(doctype, payload):
	"""Save draft doctype document using payload fields and child rows."""
	_assert_supported_doctype(doctype)
	if not frappe.has_permission(doctype, "create"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	payload = _parse_json_like(payload, {}) or {}
	if not isinstance(payload, dict):
		frappe.throw(_("Invalid payload"))

	doc = frappe.new_doc(doctype)
	for key, value in payload.items():
		if key in {"doctype", "name"}:
			continue
		doc.set(key, value)
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist()
def submit_doctype_doc(doctype, payload=None, name=None):
	"""Save and submit or submit existing document for supported doctypes."""
	_assert_supported_doctype(doctype)
	if not frappe.has_permission(doctype, "submit"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if name:
		doc = frappe.get_doc(doctype, name)
		if doc.docstatus == 0:
			doc.submit()
		return {"name": doc.name, "docstatus": doc.docstatus}

	payload_data = _parse_json_like(payload, {}) or {}
	if not isinstance(payload_data, dict):
		frappe.throw(_("Invalid payload"))

	doc = frappe.new_doc(doctype)
	for key, value in payload_data.items():
		if key in {"doctype", "name"}:
			continue
		doc.set(key, value)
	doc.save()
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus}
