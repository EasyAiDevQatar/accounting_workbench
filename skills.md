# Accounting Workbench Skills & Rules

This document defines mandatory implementation standards for `accounting_workbench`.
Our module is a custom UX and API orchestration layer on top of ERPNext accounting, not a replacement accounting engine.

## 1. ERPNext-First Mandate (Non-Negotiable)

Before implementing any page, API, child table payload, validation, or workflow, inspect ERPNext and mirror it.

- **Authoritative source**: `apps/erpnext/erpnext/accounts/doctype/...` and `apps/erpnext/erpnext/accounts/report/...`.
- **What must match**: doctype design, child table structure, statuses, submit/cancel lifecycle, posting side effects, reconciliation behavior, and report filters.
- **No reinvention**: custom code must wrap ERPNext behavior; it must not create alternate accounting logic.
- **Deviation policy**: any intentional difference from ERPNext must be explicitly documented and approved first.

## 2. Accounting Engine Constraints

- Never create or edit `GL Entry` or `Payment Ledger Entry` directly from custom logic.
- Always create valid business documents and submit them (`Sales Invoice`, `Purchase Invoice`, `Payment Entry`, `Journal Entry`, etc.).
- Use ERPNext's standard posting and cancellation flows so audit trail and double-entry behavior stay correct.
- Treat child tables as first-class accounting inputs, not optional UI details.

## 3. Required Child Table Alignment

At minimum, implement and validate payloads to match ERPNext child tables:

- Sales: `Sales Invoice Item`, `Sales Taxes and Charges`, `Sales Invoice Payment`.
- Purchase: `Purchase Invoice Item`, `Purchase Taxes and Charges`.
- Payment: `Payment Entry Reference`, `Payment Entry Deduction`.
- Journal: `Journal Entry Account`.
- Budgeting/controls: relevant child doctypes when feature is enabled.

All child-row field names and semantics must remain ERPNext-compatible.

## 4. UX and UI Standards (Minimal Clicks)

- **List + Create parity**: every major module must have a clear List page and a focused Create/Edit experience.
- **Smart defaults**: auto-fill company, fiscal year, currency, posting date, and common accounts where applicable.
- **Interconnected flows**: payment page must fetch outstanding invoices; invoice pages must expose direct payment actions; reconciliation must link back to source vouchers.
- **Low-friction editing**: use split panes, drawers, and contextual modals instead of full page hops where possible.

## 5. Mandatory Help System

- Every page must include a Help button.
- Help opens contextual guidance for the current page/module.
- Help content must cover:
  - what the page does,
  - required accounting fields,
  - child table behavior,
  - submit/cancel impact on accounting.

## 6. API Strategy for `accounting_workbench/api.py`

- Use custom whitelisted methods for workflow endpoints that span multiple doctypes or child tables.
- API endpoints must return frontend-friendly structures but remain ERPNext-compatible in inputs and outputs.
- When ERPNext already provides stable helper methods, reuse/import those patterns instead of duplicating logic.
- Every API for transactional documents must preserve idempotent and auditable behavior.

## 7. Development Workflow (Always Follow)

1. Identify the accounting capability to build.
2. Inspect ERPNext doctype, child tables, and related report/tool code.
3. Design list page + create/edit page + help content together.
4. Define custom API contract around ERPNext-compatible payloads.
5. Implement backend wrapper and frontend UI.
6. Validate submit/cancel/reconcile behavior with real document flows.
7. Confirm generated ledger impact is correct through ERPNext reports.