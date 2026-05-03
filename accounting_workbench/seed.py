# Copyright (c) 2026, Author and contributors
# Demo vouchers for Accounting Workbench charts (idempotent, tagged AWB-DEMO).

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


PREFIX = "AWB-DEMO"


def _demo_calendar_window_complete(company: str) -> bool:
	"""True when demo JEs exist for each slot day-to-date in the month plus the draft marker."""
	start = getdate(today()).replace(day=1)
	end = getdate(today())
	d = start
	while d <= end:
		for slot in range(3):
			rmk = f"{PREFIX} cash movement {d.isoformat()} #{slot}"
			if not frappe.db.exists("Journal Entry", {"company": company, "user_remark": rmk}):
				return False
		d += timedelta(days=1)
	return bool(
		frappe.db.exists(
			"Journal Entry", {"company": company, "user_remark": f"{PREFIX} draft review"}
		)
	)


def _roles_ok() -> bool:
	roles = frappe.get_roles(frappe.session.user)
	return "System Manager" in roles or "Accounts Manager" in roles


def _as_bool(v) -> bool:
	if isinstance(v, str):
		return v not in ("", "0", "false", "False", "no")
	return bool(v)


def _resolve_accounts(company: str) -> dict:
	bank = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and account_type='Bank' and is_group=0
		order by name asc limit 1
		""",
		company,
	)
	bank = bank[0][0] if bank else None

	expenses = frappe.get_all(
		"Account",
		filters={
			"company": company,
			"root_type": "Expense",
			"is_group": 0,
			"disabled": 0,
		},
		pluck="name",
		limit=6,
	)

	income = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and root_type='Income' and is_group=0 and disabled=0
		order by name asc limit 1
		""",
		company,
	)
	income = income[0][0] if income else None

	debtors = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and account_type='Receivable' and is_group=0 and disabled=0
		order by name asc limit 1
		""",
		company,
	)
	debtors = debtors[0][0] if debtors else None

	creditors = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and account_type='Payable' and is_group=0 and disabled=0
		order by name asc limit 1
		""",
		company,
	)
	creditors = creditors[0][0] if creditors else None

	cash = frappe.db.sql(
		"""
		select name from `tabAccount`
		where company=%s and account_type='Cash' and is_group=0 and disabled=0
		order by name asc limit 1
		""",
		company,
	)
	cash = cash[0][0] if cash else None

	bank_account = frappe.db.get_value(
		"Bank Account",
		{"company": company, "is_company_account": 1},
		"name",
		order_by="creation asc",
	) or frappe.db.get_value("Bank Account", {"company": company}, "name", order_by="creation asc")

	return {
		"bank": bank,
		"cash": cash,
		"expenses": expenses or [],
		"income": income,
		"debtors": debtors,
		"creditors": creditors,
		"bank_account": bank_account,
	}


def _clear_demo_docs(company: str) -> None:
	"""Cancel & remove demo-tagged vouchers."""
	for je in frappe.get_all(
		"Journal Entry",
		filters={"company": company, "user_remark": ["like", f"{PREFIX}%"]},
		pluck="name",
	):
		doc = frappe.get_doc("Journal Entry", je)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Journal Entry", je, force=True)

	for si in frappe.get_all(
		"Sales Invoice",
		filters={"company": company, "po_no": ["like", f"{PREFIX}%"]},
		pluck="name",
	):
		doc = frappe.get_doc("Sales Invoice", si)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Sales Invoice", si, force=True)

	for pi in frappe.get_all(
		"Purchase Invoice",
		filters={"company": company, "bill_no": ["like", f"{PREFIX}%"]},
		pluck="name",
	):
		doc = frappe.get_doc("Purchase Invoice", pi)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Purchase Invoice", pi, force=True)

	for bt in frappe.get_all(
		"Bank Transaction",
		filters={"company": company, "reference_number": ["like", f"{PREFIX}%"]},
		pluck="name",
	):
		doc = frappe.get_doc("Bank Transaction", bt)
		if doc.docstatus == 1:
			doc.cancel()
		frappe.delete_doc("Bank Transaction", bt, force=True)

	frappe.db.commit()


def _seed_journal_entries(company: str, acc: dict) -> None:
	bank = acc["bank"]
	expenses = acc["expenses"]
	income = acc["income"]
	if not bank or not expenses:
		return

	start = getdate(today()).replace(day=1)
	end = getdate(today())
	d = start
	max_entries = 20
	created_idx = 0
	while d <= end:
		for slot in range(3):
			if created_idx >= max_entries:
				break
			remark = f"{PREFIX} cash movement {d.isoformat()} #{slot}"
			if frappe.db.exists("Journal Entry", {"user_remark": remark, "company": company}):
				continue

			amount_in = flt(3000 + (created_idx % 7) * 850 + created_idx * 120)
			amount_out = flt(2200 + (created_idx % 5) * 600 + created_idx * 90)
			exp1 = expenses[created_idx % len(expenses)]
			exp2 = expenses[(created_idx + 1) % len(expenses)]

			je = frappe.new_doc("Journal Entry")
			je.company = company
			je.posting_date = d
			je.user_remark = remark
			je.remark = PREFIX

			if income:
				je.append(
					"accounts",
					{
						"account": bank,
						"debit_in_account_currency": amount_in,
						"credit_in_account_currency": 0,
					},
				)
				je.append(
					"accounts",
					{
						"account": income,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": amount_in,
					},
				)

			je.append(
				"accounts",
				{
					"account": exp1,
					"debit_in_account_currency": amount_out,
					"credit_in_account_currency": 0,
				},
			)
			je.append(
				"accounts",
				{
					"account": bank,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": amount_out,
				},
			)

			small = flt(150 + created_idx * 13)
			je.append(
				"accounts",
				{
					"account": exp2,
					"debit_in_account_currency": small,
					"credit_in_account_currency": 0,
				},
			)
			je.append(
				"accounts",
				{
					"account": bank,
					"debit_in_account_currency": 0,
					"credit_in_account_currency": small,
				},
			)

			je.insert()
			je.submit()
			created_idx += 1
		d += timedelta(days=1)


def _seed_sales_invoices(company: str, acc: dict) -> None:
	if not acc["debtors"] or not acc["income"]:
		return
	customer = frappe.db.get_value("Customer", {"disabled": 0}, "name", order_by="creation asc")
	item = frappe.db.get_value(
		"Item",
		{"disabled": 0, "is_sales_item": 1, "is_stock_item": 0},
		"name",
		order_by="creation asc",
	) or frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "name", order_by="creation asc")
	if not customer or not item:
		return

	base = getdate(today()).replace(day=1)
	for i in range(3):
		po = f"{PREFIX}-SINV-{i + 1:02d}"
		if frappe.db.exists("Sales Invoice", {"po_no": po, "company": company}):
			continue
		rate = flt(4000 + i * 1200)
		si = frappe.new_doc("Sales Invoice")
		si.company = company
		si.customer = customer
		si.posting_date = base + timedelta(days=i * 3)
		si.due_date = si.posting_date + timedelta(days=30)
		si.po_no = po
		row = si.append(
			"items",
			{
				"item_code": item,
				"qty": 1,
				"rate": rate,
			},
		)
		if frappe.get_cached_value("Item", item, "is_stock_item"):
			wh = frappe.db.get_value(
				"Warehouse", {"company": company, "is_group": 0}, "name", order_by="creation asc"
			)
			if wh:
				row.warehouse = wh
		si.insert()
		si.submit()


def _seed_purchase_invoices(company: str, acc: dict) -> None:
	if not acc["creditors"] or not acc["expenses"]:
		return
	supplier = frappe.db.get_value("Supplier", {"disabled": 0}, "name", order_by="creation asc")
	item = frappe.db.get_value(
		"Item",
		{"disabled": 0, "is_purchase_item": 1, "is_stock_item": 0},
		"name",
		order_by="creation asc",
	) or frappe.db.get_value("Item", {"disabled": 0, "is_purchase_item": 1}, "name", order_by="creation asc")
	if not supplier or not item:
		return

	exp = acc["expenses"][0]
	today_d = getdate(today())
	for i in range(4):
		bill = f"{PREFIX}-PINV-{i + 1:02d}"
		if frappe.db.exists("Purchase Invoice", {"bill_no": bill, "company": company}):
			continue
		rate = flt(2500 + i * 800)
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = company
		pi.supplier = supplier
		post = today_d - timedelta(days=50 + i * 5)
		pi.posting_date = post
		pi.bill_date = post
		pi.bill_no = bill
		pi.payment_terms_template = None
		# Past due vs future due for dashboard styling; due must be >= posting_date.
		pi.due_date = (
			today_d - timedelta(days=3 + i) if i % 2 == 0 else today_d + timedelta(days=12 + i * 2)
		)
		row = pi.append(
			"items",
			{
				"item_code": item,
				"qty": 1,
				"rate": rate,
				"expense_account": exp,
			},
		)
		if frappe.get_cached_value("Item", item, "is_stock_item"):
			wh = frappe.db.get_value(
				"Warehouse", {"company": company, "is_group": 0}, "name", order_by="creation asc"
			)
			if wh:
				row.warehouse = wh
		pi.insert()
		pi.submit()


def _seed_bank_transactions(company: str, acc: dict) -> None:
	if not acc["bank_account"]:
		return
	today_d = getdate(today())
	for i in range(5):
		ref = f"{PREFIX}-BT-{i + 1:02d}"
		if frappe.db.exists("Bank Transaction", {"reference_number": ref, "company": company}):
			continue
		gl_bank = frappe.db.get_value("Bank Account", acc["bank_account"], "account")
		tx_currency = (
			frappe.db.get_value("Account", gl_bank, "account_currency")
			if gl_bank
			else frappe.db.get_value("Company", company, "default_currency")
		)
		bt = frappe.new_doc("Bank Transaction")
		bt.date = today_d - timedelta(days=i)
		bt.bank_account = acc["bank_account"]
		bt.company = company
		bt.currency = tx_currency
		bt.reference_number = ref
		bt.description = PREFIX
		if i % 3 == 0:
			bt.deposit = flt(1800 + i * 200)
			bt.withdrawal = 0
		else:
			bt.deposit = 0
			bt.withdrawal = flt(950 + i * 150)
		bt.insert()
		# Keep unsubmitted so status stays Pending / counts toward unreconciled KPI in dashboard_summary.


def _seed_drafts(company: str, acc: dict) -> None:
	if not acc["bank"] or not acc["expenses"]:
		return
	remark = f"{PREFIX} draft review"
	if frappe.db.exists("Journal Entry", {"user_remark": remark, "company": company}):
		return
	exp = acc["expenses"][0]
	je = frappe.new_doc("Journal Entry")
	je.company = company
	je.posting_date = getdate(today())
	je.user_remark = remark
	je.append(
		"accounts",
		{"account": exp, "debit_in_account_currency": 100, "credit_in_account_currency": 0},
	)
	je.append(
		"accounts",
		{"account": acc["bank"], "debit_in_account_currency": 0, "credit_in_account_currency": 100},
	)
	je.insert()


@frappe.whitelist()
def seed_demo_accounting_data(company=None, force=False):
	"""
	Create demo Journal Entries, invoices, and bank lines tagged AWB-DEMO (same ERPNext users).

	Requires System Manager or Accounts Manager. Safe to re-run; skips if enough data exists unless force=1.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"))
	if not _roles_ok():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	force = _as_bool(force)
	company = company or frappe.defaults.get_user_default("Company")
	if not company:
		company = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	if not company:
		frappe.throw(_("No Company found"))

	if force:
		_clear_demo_docs(company)

	if not force and _demo_calendar_window_complete(company):
		count = frappe.db.count(
			"Journal Entry",
			{"company": company, "user_remark": ["like", f"{PREFIX}%"]},
		)
		return {
			"ok": True,
			"skipped": True,
			"company": company,
			"journal_entries": count,
			"message": _("Demo data already present for this month. Pass force=1 to recreate."),
		}

	acc = _resolve_accounts(company)
	if not acc["bank"]:
		frappe.throw(
			_("No leaf Bank account for company {0}. Complete chart of accounts first.").format(company)
		)
	if len(acc["expenses"]) < 1:
		frappe.throw(
			_("No expense accounts for company {0}. Complete chart of accounts first.").format(company)
		)

	frappe.flags.ignore_permissions = True
	try:
		_seed_journal_entries(company, acc)
		_seed_sales_invoices(company, acc)
		_seed_purchase_invoices(company, acc)
		_seed_bank_transactions(company, acc)
		_seed_drafts(company, acc)
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.flags.ignore_permissions = False

	frappe.db.commit()

	final_je = frappe.db.count(
		"Journal Entry",
		{"company": company, "user_remark": ["like", f"{PREFIX}%"]},
	)
	return {
		"ok": True,
		"company": company,
		"journal_entries": final_je,
		"message": _("Seeded demo vouchers for Accounting Workbench."),
	}
