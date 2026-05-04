import { createRouter, createWebHistory } from 'vue-router'
import { fetchAuthUser, ensureCsrfToken } from '@/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    meta: { requiresAuth: false },
    component: () => import('@/pages/Login.vue'),
  },
  {
    path: '/',
    component: () => import('@/layouts/WorkbenchLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: {
          helpTitle: 'Dashboard Overview',
          helpContent: 'The Dashboard gives you a real-time overview of your financial health, including Cash Flow, Income vs Expenses, and outstanding Receivables/Payables.'
        }
      },
      {
        path: 'journal',
        name: 'journal',
        component: () => import('@/pages/JournalEntries.vue'),
        meta: {
          helpTitle: 'Journal Entries',
          helpContent: '### Journal Entries\n\nUse Journal Entries for manual adjustments, opening balances, or complex multi-account transactions.\n\n**Rules:**\n- Total Debit must equal Total Credit.\n- You cannot post against a Group account.'
        }
      },
      {
        path: 'journal/new',
        name: 'journal-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Journal Entry',
          subtitle: 'Create Journal Entry using required fields and accounts child rows.',
          doctype: 'Journal Entry',
          listRouteName: 'journal',
        },
      },
      {
        path: 'invoices',
        name: 'invoices',
        component: () => import('@/pages/InvoiceWorkspace.vue'),
        props: { invoiceType: 'Sales' },
        meta: {
          helpTitle: 'Sales Invoices',
          helpContent:
            'Create and submit Sales Invoices with item child rows and optional tax templates. Submitted invoices automatically post accounting impact in ERPNext and appear in receivables.',
        },
      },
      {
        path: 'invoices/new',
        name: 'invoices-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Sales Invoice',
          subtitle: 'Create Sales Invoice with required parent and child-table fields.',
          doctype: 'Sales Invoice',
          listRouteName: 'invoices',
        },
      },
      {
        path: 'bills',
        name: 'bills',
        component: () => import('@/pages/InvoiceWorkspace.vue'),
        props: { invoiceType: 'Purchase' },
        meta: {
          helpTitle: 'Purchase Bills',
          helpContent:
            'Create Purchase Invoices using supplier, items, and cost center lines. Submitted bills feed Accounts Payable and are available for payment allocation.',
        },
      },
      {
        path: 'bills/new',
        name: 'bills-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Purchase Invoice',
          subtitle: 'Create Purchase Invoice with required parent and child-table fields.',
          doctype: 'Purchase Invoice',
          listRouteName: 'bills',
        },
      },
      {
        path: 'payments',
        name: 'payments',
        component: () => import('@/pages/PaymentsWorkspace.vue'),
        meta: {
          helpTitle: 'Payments and Allocation',
          helpContent:
            'Use this page to create Payment Entries and allocate amounts to outstanding invoices. Allocation maps to Payment Entry Reference rows so invoice outstanding balances are updated correctly.',
        },
      },
      {
        path: 'payments/new',
        name: 'payments-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Payment Entry',
          subtitle: 'Create Payment Entry with required references and deduction rows.',
          doctype: 'Payment Entry',
          listRouteName: 'payments',
        },
      },
      {
        path: 'bank',
        name: 'bank',
        component: () => import('@/pages/BankReconciliationWorkspace.vue'),
        meta: {
          helpTitle: 'Bank Reconciliation',
          helpContent:
            'Reconcile Bank Transactions and allocate amounts to vouchers. Keep pending and unreconciled lines low to ensure accurate cash position.',
        },
      },
      {
        path: 'bank/new',
        name: 'bank-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Bank Transaction',
          subtitle: 'Create Bank Transaction for reconciliation workflow.',
          doctype: 'Bank Transaction',
          listRouteName: 'bank',
        },
      },
      {
        path: 'coa',
        name: 'coa',
        component: () => import('@/pages/ChartOfAccounts.vue'),
        meta: {
          helpTitle: 'Chart of Accounts',
          helpContent:
            'Chart of Accounts shows your account hierarchy and current balances. Group accounts organize structure; posting accounts receive transaction impact from submitted documents.',
        },
      },
      {
        path: 'coa/new',
        name: 'coa-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Account',
          subtitle: 'Create account nodes for chart structure and posting.',
          doctype: 'Account',
          listRouteName: 'coa',
        },
      },
      {
        path: 'budget',
        name: 'budget',
        component: () => import('@/pages/BudgetWorkspace.vue'),
        meta: {
          helpTitle: 'Budget Control',
          helpContent:
            'Manage Budget and Budget Account controls by fiscal year. Submitted budgets enforce annual spending checks in ERPNext.',
        },
      },
      {
        path: 'budget/new',
        name: 'budget-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Budget',
          subtitle: 'Create budget with required control fields and accounts rows.',
          doctype: 'Budget',
          listRouteName: 'budget',
        },
      },
      {
        path: 'reports',
        name: 'reports',
        component: () => import('@/pages/ReportsExplorer.vue'),
        meta: {
          helpTitle: 'Reports Explorer',
          helpContent:
            'Run core accounting reports (GL, Trial Balance, P&L, Balance Sheet, Cash Flow, AR, AP) from one page with shared company/date scope.',
        },
      },
      {
        path: 'period-close',
        name: 'period-close',
        component: () => import('@/pages/PeriodCloseWorkspace.vue'),
        meta: {
          helpTitle: 'Period Close',
          helpContent:
            'Track Period Closing Vouchers and Accounting Period locks. Closing controls prevent accidental postings in completed periods.',
        },
      },
      {
        path: 'period-close/new',
        name: 'period-close-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Period Closing Voucher',
          subtitle: 'Create period closing voucher with required accounting fields.',
          doctype: 'Period Closing Voucher',
          listRouteName: 'period-close',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/SettingsWorkspace.vue'),
        meta: {
          helpTitle: 'Accounting Settings',
          helpContent:
            'Review company defaults, active fiscal year, and accounting dimensions. Use these settings to keep module behavior consistent across all workflows.',
        },
      },
      {
        path: 'customers',
        name: 'customers',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Customers',
          subtitle: 'Receivables party master used by Sales Invoices and Payment Entries.',
          doctype: 'Customer',
          createRouteName: 'customers-new',
        },
        meta: {
          helpTitle: 'Customers',
          helpContent:
            'Customer master records are required for Sales Invoices, receivables aging, and payment allocation.',
        },
      },
      {
        path: 'suppliers',
        name: 'suppliers',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Suppliers',
          subtitle: 'Payables party master used by Purchase Invoices and outgoing payments.',
          doctype: 'Supplier',
          createRouteName: 'suppliers-new',
        },
        meta: {
          helpTitle: 'Suppliers',
          helpContent:
            'Supplier master records drive Purchase Invoices, accounts payable aging, and payment workflows.',
        },
      },
      {
        path: 'bank-accounts',
        name: 'bank-accounts',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Bank Accounts',
          subtitle: 'Bank account master records for payment and reconciliation flows.',
          doctype: 'Bank Account',
          createRouteName: 'bank-accounts-new',
        },
        meta: {
          helpTitle: 'Bank Accounts',
          helpContent:
            'Bank Account records map payments and reconciliations to actual company bank ledgers.',
        },
      },
      {
        path: 'bank-transactions',
        name: 'bank-transactions',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Bank Transactions',
          subtitle: 'Imported or synced bank lines awaiting reconciliation or review.',
          doctype: 'Bank Transaction',
          createRouteName: 'bank-transactions-new',
        },
        meta: {
          helpTitle: 'Bank Transactions',
          helpContent:
            'Bank Transactions are the source lines used in bank reconciliation and settlement matching.',
        },
      },
      {
        path: 'fiscal-years',
        name: 'fiscal-years',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Fiscal Years',
          subtitle: 'Fiscal year master controls accounting date boundaries.',
          doctype: 'Fiscal Year',
          createRouteName: 'fiscal-years-new',
        },
        meta: {
          helpTitle: 'Fiscal Years',
          helpContent:
            'Fiscal Year records define annual accounting periods and are required for period close and reporting.',
        },
      },
      {
        path: 'dimensions',
        name: 'dimensions',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Dimensions',
          subtitle: 'Accounting dimensions used for cost center, project, and analytic controls.',
          doctype: 'Accounting Dimension',
          createRouteName: 'dimensions-new',
        },
        meta: {
          helpTitle: 'Accounting Dimensions',
          helpContent:
            'Accounting Dimensions add multi-dimensional analysis (cost center/project style) to entries and reports.',
        },
      },
      {
        path: 'customers/new',
        name: 'customers-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Customer',
          subtitle: 'Create customer master record with required fields.',
          doctype: 'Customer',
          listRouteName: 'customers',
        },
      },
      {
        path: 'suppliers/new',
        name: 'suppliers-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Supplier',
          subtitle: 'Create supplier master record with required fields.',
          doctype: 'Supplier',
          listRouteName: 'suppliers',
        },
      },
      {
        path: 'bank-accounts/new',
        name: 'bank-accounts-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Bank Account',
          subtitle: 'Create bank account master record.',
          doctype: 'Bank Account',
          listRouteName: 'bank-accounts',
        },
      },
      {
        path: 'bank-transactions/new',
        name: 'bank-transactions-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Bank Transaction',
          subtitle: 'Create bank transaction for reconciliation queue.',
          doctype: 'Bank Transaction',
          listRouteName: 'bank-transactions',
        },
      },
      {
        path: 'fiscal-years/new',
        name: 'fiscal-years-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Fiscal Year',
          subtitle: 'Create fiscal year master record.',
          doctype: 'Fiscal Year',
          listRouteName: 'fiscal-years',
        },
      },
      {
        path: 'dimensions/new',
        name: 'dimensions-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Accounting Dimension',
          subtitle: 'Create accounting dimension definition.',
          doctype: 'Accounting Dimension',
          listRouteName: 'dimensions',
        },
      },
      {
        path: 'companies',
        name: 'companies',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Companies',
          subtitle: 'Company master records for multi-company accounting.',
          doctype: 'Company',
          createRouteName: 'companies-new',
        },
      },
      {
        path: 'companies/new',
        name: 'companies-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Company',
          subtitle: 'Create company master record.',
          doctype: 'Company',
          listRouteName: 'companies',
        },
      },
      {
        path: 'accounting-periods',
        name: 'accounting-periods',
        component: () => import('@/pages/DoctypeListWorkspace.vue'),
        props: {
          title: 'Accounting Periods',
          subtitle: 'Accounting period records for transaction locks and controls.',
          doctype: 'Accounting Period',
          createRouteName: 'accounting-periods-new',
        },
      },
      {
        path: 'accounting-periods/new',
        name: 'accounting-periods-new',
        component: () => import('@/pages/DoctypeCreateWorkspace.vue'),
        props: {
          title: 'Accounting Period',
          subtitle: 'Create accounting period lock definition.',
          doctype: 'Accounting Period',
          listRouteName: 'accounting-periods',
        },
      },
    ],
  },
]

// BASE_URL points at /assets/.../workbench/ in production; Vue history must match the public website path.
const historyBase = import.meta.env.DEV ? '/' : '/accounting-workbench/'

const router = createRouter({
  history: createWebHistory(historyBase),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth !== false)
  const user = await fetchAuthUser()

  if (!requiresAuth) {
    if (to.name === 'login' && user && user !== 'Guest') {
      next({ path: '/' })
      return
    }
    next()
    return
  }

  if (!user || user === 'Guest') {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  try {
    await ensureCsrfToken()
  } catch {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
