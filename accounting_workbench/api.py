# Copyright (c) 2026, Author and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
import frappe.sessions
from frappe import _
from frappe.utils import flt, getdate


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

	from_date = getdate(from_date) if from_date else getdate(frappe.utils.today())
	to_date = getdate(to_date) if to_date else getdate(frappe.utils.today())
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
