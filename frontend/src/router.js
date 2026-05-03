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
      },
      {
        path: 'journal',
        name: 'journal',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Journal Entries',
          subtitle: 'Standard Desk form · quick-entry UI coming next.',
          deskRoute: '/app/journal-entry',
        },
      },
      {
        path: 'invoices',
        name: 'invoices',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Sales Invoices',
          subtitle: 'Unified invoice composer is planned on the workbench roadmap.',
          deskRoute: '/app/sales-invoice',
        },
      },
      {
        path: 'bills',
        name: 'bills',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Purchase Invoices / Bills',
          subtitle: 'Use Desk PI until the shared composer lands.',
          deskRoute: '/app/purchase-invoice',
        },
      },
      {
        path: 'payments',
        name: 'payments',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Payments',
          subtitle: 'Allocation-focused payment workspace is next.',
          deskRoute: '/app/payment-entry',
        },
      },
      {
        path: 'bank',
        name: 'bank',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Bank reconciliation',
          subtitle: 'Split-view reconciliation cockpit is planned.',
          deskRoute: '/app/bank-reconciliation-tool',
        },
      },
      {
        path: 'coa',
        name: 'coa',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Chart of Accounts',
          subtitle: 'Tree + searchable grid hybrid comes later.',
          deskRoute: '/app/account',
        },
      },
      {
        path: 'budget',
        name: 'budget',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Budget',
          subtitle: 'Open Budget entry in Desk.',
          deskRoute: '/app/budget',
        },
      },
      {
        path: 'reports',
        name: 'reports',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Reports',
          subtitle: 'Report explorer with saved views is on the roadmap.',
          deskRoute: '/app/query-report/General%20Ledger',
        },
      },
      {
        path: 'period-close',
        name: 'period-close',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Period close',
          subtitle: 'Checklist-style close flows will live here.',
          deskRoute: '/app/accounting-period',
        },
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('@/pages/StubDesk.vue'),
        props: {
          title: 'Workbench settings',
          subtitle: 'Defaults, shortcuts, and density preferences.',
          deskRoute: '/app/company',
        },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
