import frappe


def after_install():
	remove_accounting_workbench_workspace()


def after_migrate():
	remove_accounting_workbench_workspace()


def remove_accounting_workbench_workspace():
	"""Remove Desk Workspace so the SPA is not listed in ERPNext sidebar."""
	name = "Accounting Workbench"
	if not frappe.db.exists("Workspace", name):
		return
	frappe.delete_doc("Workspace", name, ignore_permissions=True, force=True)
	frappe.db.commit()
