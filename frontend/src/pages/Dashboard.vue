<template>
  <div class="flex min-h-0 flex-1 flex-col bg-[#f4f6fb]">
    <header class="border-b border-slate-200/80 bg-white px-8 py-6 shadow-sm">
      <div class="flex flex-wrap items-start gap-6">
        <div class="min-w-[200px] flex-1">
          <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">
            Accounting Workspace
          </p>
          <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">
            Accounting Workspace
          </h1>
          <p class="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">
            Your command center for fast, unified accounting.
          </p>
        </div>
        <div class="flex flex-1 justify-center">
          <div class="relative w-full max-w-md">
            <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
            <input
              v-model="searchQ"
              type="search"
              placeholder="Search accounts, transactions, reports…"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-24 text-sm outline-none ring-blue-500/30 transition focus:border-blue-400 focus:bg-white focus:ring-4"
            />
            <kbd
              class="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-medium text-slate-500 sm:inline-block"
              >Ctrl K</kbd
            >
          </div>
        </div>
        <div class="flex flex-shrink-0 items-center gap-4">
          <span class="relative inline-flex h-11 w-11 cursor-pointer items-center justify-center rounded-full bg-slate-100 text-lg text-slate-600 ring-1 ring-slate-200/80">
            🔔
            <span
              v-if="alertCount > 0"
              class="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
              >{{ alertCount > 99 ? '99+' : alertCount }}</span
            >
          </span>
          <span
            class="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-sm font-bold text-white shadow-md ring-2 ring-white"
            >AS</span
          >
        </div>
      </div>
      <div class="mt-6 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
        <div
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
        >
          <span class="text-base text-slate-500">📅</span>
          <input v-model="fromDate" type="date" class="rounded-lg border-0 bg-transparent text-sm outline-none" />
          <span class="text-slate-400">–</span>
          <input v-model="toDate" type="date" class="rounded-lg border-0 bg-transparent text-sm outline-none" />
        </div>
        <div
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm"
        >
          <span class="text-base text-slate-500">🏢</span>
          <select
            v-model="company"
            class="max-w-[14rem] border-0 bg-transparent text-sm font-medium outline-none"
          >
            <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
          </select>
        </div>
        <div class="ml-auto text-xs text-slate-500">{{ periodLabel }}</div>
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto px-8 py-6">
        <section class="flex flex-wrap gap-3">
          <button
            type="button"
            class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
            @click="goDesk('/app/journal-entry')"
          >
            + New Journal Entry
          </button>
          <button
            type="button"
            class="rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
            @click="goDesk('/app/payment-entry')"
          >
            Record Payment
          </button>
          <button
            type="button"
            class="rounded-xl border-2 border-blue-500 bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 transition hover:bg-blue-50"
            @click="goDesk('/app/sales-invoice')"
          >
            New Invoice
          </button>
          <button
            type="button"
            class="rounded-xl border-2 border-orange-500 bg-white px-4 py-2.5 text-sm font-semibold text-orange-700 transition hover:bg-orange-50"
            @click="goDesk('/app/purchase-invoice')"
          >
            Add Bill
          </button>
          <button
            type="button"
            class="rounded-xl border-2 border-violet-500 bg-white px-4 py-2.5 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
            @click="goDesk('/app/bank-reconciliation-tool')"
          >
            Reconcile Bank
          </button>
          <button
            type="button"
            class="rounded-xl border-2 border-red-500 bg-white px-4 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-50"
            @click="goDesk('/app/closing-voucher')"
          >
            Close Period
          </button>
        </section>

        <section v-if="error" class="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {{ error }}
        </section>

        <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <div
            v-for="card in summary?.kpis || []"
            :key="card.id"
            class="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <div class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              {{ card.label }}
            </div>
            <div class="mt-3 flex items-end justify-between gap-3">
              <div class="text-[26px] font-bold tabular-nums leading-none text-slate-900">
                {{ formatKpiValue(card) }}
              </div>
              <div
                v-if="card.delta_pct != null"
                class="shrink-0 text-xs font-bold tabular-nums"
                :class="card.delta_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ card.delta_pct >= 0 ? '+' : '' }}{{ card.delta_pct }}%
              </div>
            </div>
            <p v-if="kpiSubtitle(card)" class="mt-2 text-xs leading-snug text-slate-500">
              {{ kpiSubtitle(card) }}
            </p>
            <div class="mt-4">
              <Sparkline
                v-if="card.sparkline?.length"
                :values="card.sparkline"
                :color="sparklineColor(card.id)"
              />
              <div v-else class="h-10 w-full rounded-lg bg-slate-50" />
            </div>
          </div>
        </section>

        <section class="mt-6 grid gap-5 xl:grid-cols-3 xl:items-start">
          <div
            class="min-h-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <h2 class="text-sm font-bold text-slate-900">Today's Finance Tasks</h2>
            <ul class="mt-4 divide-y divide-slate-100">
              <li
                v-for="(t, i) in tasksOrPlaceholder"
                :key="i"
                class="flex items-start justify-between gap-3 py-3 first:pt-0"
              >
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <span v-if="t.priority" :class="priBadge(t.priority)" class="rounded-full px-2 py-0.5 text-[10px] font-bold capitalize">{{
                      priLabel(t.priority)
                    }}</span>
                    <span class="font-medium text-slate-800">{{ t.title }}</span>
                    <span v-if="t.count != null" class="text-slate-500">({{ t.count }})</span>
                  </div>
                </div>
                <button
                  v-if="t.route"
                  type="button"
                  class="shrink-0 text-xs font-semibold text-blue-600 hover:underline"
                  @click="goDesk(t.route)"
                >
                  Open
                </button>
              </li>
            </ul>
          </div>

          <div
            class="min-h-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)] xl:col-span-1"
          >
            <h2 class="text-sm font-bold text-slate-900">Cash In vs Cash Out</h2>
            <p class="mt-1 text-xs text-slate-500">Bank & cash GL accounts · daily in period.</p>
            <CashFlowChart
              class="mt-4"
              :labels="summary?.cash_series?.labels || []"
              :inflow="summary?.cash_series?.inflow || []"
              :outflow="summary?.cash_series?.outflow || []"
              :currency="summary?.currency || 'USD'"
            />
          </div>

          <div
            class="min-h-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <h2 class="text-sm font-bold text-slate-900">Expense Breakdown</h2>
            <p class="mt-1 text-xs text-slate-500">Expense accounts · share of total.</p>
            <ExpenseDonut class="mt-5" :rows="expenseRows" :currency="summary?.currency || 'USD'" />
            <p v-if="!expenseRows.length" class="mt-6 text-center text-xs text-slate-400">
              No expense postings in this period.
            </p>
          </div>
        </section>

        <section class="mt-6 grid gap-5 lg:grid-cols-2">
          <div
            class="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <h2 class="text-sm font-bold text-slate-900">Recent Transactions</h2>
            <div class="mt-4 overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th class="pb-2 pr-2">Date</th>
                    <th class="pb-2 pr-2">Type</th>
                    <th class="pb-2 pr-2">Reference</th>
                    <th class="pb-2 pr-2">Party</th>
                    <th class="pb-2 pr-2">Account</th>
                    <th class="pb-2 pr-2 text-right">Amount</th>
                    <th class="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(r, i) in summary?.recent_gl || []"
                    :key="i"
                    class="border-b border-slate-50"
                  >
                    <td class="py-2 pr-2 whitespace-nowrap text-slate-700">{{ r.posting_date }}</td>
                    <td class="py-2 pr-2 text-slate-700">{{ r.voucher_type }}</td>
                    <td class="py-2 pr-2 font-mono text-slate-800">{{ r.voucher_no }}</td>
                    <td class="max-w-[7rem] truncate py-2 pr-2 text-slate-600">{{ r.party || '—' }}</td>
                    <td class="max-w-[8rem] truncate py-2 pr-2 text-slate-600">{{ r.account }}</td>
                    <td class="py-2 pr-2 text-right font-mono font-medium text-slate-900">{{ glAmount(r) }}</td>
                    <td class="py-2">
                      <span class="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">Posted</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div
            class="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <h2 class="text-sm font-bold text-slate-900">Upcoming Due Payments</h2>
            <div class="mt-4 overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  <tr>
                    <th class="pb-2 pr-2">Due Date</th>
                    <th class="pb-2 pr-2">Type</th>
                    <th class="pb-2 pr-2">Reference</th>
                    <th class="pb-2 pr-2">Party</th>
                    <th class="pb-2 pr-2 text-right">Amount</th>
                    <th class="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in summary?.due_payables || []"
                    :key="row.name"
                    class="border-b border-slate-50"
                  >
                    <td class="py-2 pr-2 whitespace-nowrap">{{ row.due_date }}</td>
                    <td class="py-2 pr-2">Bill</td>
                    <td class="py-2 pr-2 font-mono">{{ row.name }}</td>
                    <td class="max-w-[8rem] truncate py-2 pr-2">{{ row.supplier }}</td>
                    <td class="py-2 pr-2 text-right font-mono">{{ moneyFmt(row.outstanding_amount) }}</td>
                    <td class="py-2">
                      <span
                        class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                        :class="
                          dueTone(row) === 'overdue'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-50 text-amber-900'
                        "
                        >{{ dueLabel(row) }}</span
                      >
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <footer
          class="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/80 pt-5 text-xs text-slate-500"
        >
          <span class="inline-flex items-center gap-2 text-slate-600">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">✓</span>
            Unified workflow · same ERPNext documents underneath.
          </span>
          <span class="inline-flex items-center gap-2">
            <span class="text-base text-slate-400" aria-hidden="true">↻</span>
            <span v-if="lastSynced">Last synced {{ lastSynced }}</span>
            <span v-else>Waiting for data…</span>
          </span>
        </footer>
      </div>

      <aside
        class="hidden w-[340px] shrink-0 overflow-y-auto border-l border-slate-200/80 bg-white px-6 py-6 shadow-[inset_1px_0_0_rgba(148,163,184,0.15)] xl:block"
      >
        <div class="rounded-2xl border border-slate-200/80 bg-slate-50/50 p-5">
          <h2 class="text-sm font-bold text-slate-900">Approvals &amp; Alerts</h2>
          <div class="mt-4 space-y-4">
            <template v-if="(summary?.alerts || []).length">
              <div v-for="(a, i) in summary.alerts" :key="i" class="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
                <div class="text-[10px] font-bold uppercase tracking-wide text-slate-400">{{ a.category }}</div>
                <div class="mt-1 text-sm font-semibold text-slate-900">{{ a.title }}</div>
                <div class="mt-1 text-xs text-slate-600">{{ a.detail }}</div>
              </div>
            </template>
            <p v-else class="text-xs text-slate-400">No urgent alerts.</p>
          </div>
        </div>
        <div class="mt-5 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <h2 class="text-sm font-bold text-slate-900">Shortcuts</h2>
          <div class="mt-4 grid grid-cols-3 gap-2">
            <button
              v-for="s in shortcuts"
              :key="s.label"
              type="button"
              class="flex flex-col items-center rounded-xl border border-slate-100 bg-slate-50 py-3 text-[10px] font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-800"
              @click="goDesk(s.route)"
            >
              <span class="mb-1 text-lg">{{ s.icon }}</span>
              {{ s.label }}
            </button>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import Sparkline from '@/components/Sparkline.vue'
import CashFlowChart from '@/components/CashFlowChart.vue'
import ExpenseDonut from '@/components/ExpenseDonut.vue'

const searchQ = ref('')
const company = ref('')
const companies = ref([])
const fromDate = ref('')
const toDate = ref('')
const summary = ref(null)
const error = ref('')
const lastSynced = ref('')

const shortcuts = [
  { label: 'Trial Balance', route: '/app/query-report/Trial%20Balance', icon: '⚖' },
  { label: 'Balance Sheet', route: '/app/query-report/Balance%20Sheet', icon: '▤' },
  { label: 'Cash Flow', route: '/app/query-report/Cash%20Flow', icon: '≋' },
  { label: 'P/L', route: '/app/query-report/Profit%20and%20Loss%20Statement', icon: '📈' },
  { label: 'General Ledger', route: '/app/query-report/General%20Ledger', icon: '☰' },
  { label: 'AR Summary', route: '/app/query-report/Accounts%20Receivable', icon: '⎆' },
  { label: 'AP Summary', route: '/app/query-report/Accounts%20Payable', icon: '⎇' },
  { label: 'Budget Variance', route: '/app/budget', icon: '◫' },
  { label: 'Asset Report', route: '/app/query-report/Fixed%20Asset%20Register', icon: '🏭' },
]

const months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')

const periodLabel = computed(() => {
  if (!fromDate.value || !toDate.value) return ''
  const a = new Date(fromDate.value + 'T12:00:00')
  const b = new Date(toDate.value + 'T12:00:00')
  return `${months[a.getMonth()]} ${a.getDate()} – ${months[b.getMonth()]} ${b.getDate()}, ${b.getFullYear()}`
})

const alertCount = computed(() => {
  const pend = summary.value?.kpis?.find((k) => k.id === 'pending_approvals')
  const n = pend ? Number(pend.value || 0) : 0
  return Math.min(99, n)
})

const tasksOrPlaceholder = computed(() => {
  const t = summary.value?.tasks || []
  if (t.length) return t
  return [{ title: 'No queued drafts — great job.', count: null, route: null, priority: 'low' }]
})

const expenseRows = computed(() => summary.value?.expense_breakdown || [])

function priLabel(p) {
  const x = String(p || '').toLowerCase()
  if (!x) return ''
  return x.charAt(0).toUpperCase() + x.slice(1)
}

function priBadge(p) {
  const x = String(p).toLowerCase()
  if (x === 'high') return 'bg-rose-100 text-rose-800'
  if (x === 'medium') return 'bg-amber-100 text-amber-900'
  return 'bg-slate-100 text-slate-700'
}

function sparklineColor(id) {
  const colors = {
    cash_position: '#2563eb',
    ar: '#7c3aed',
    ap: '#ea580c',
    pending_approvals: '#ca8a04',
    unreconciled: '#db2777',
    pnl: '#16a34a',
  }
  return colors[id] || '#2563eb'
}

function goDesk(route) {
  window.location.href = `${window.location.origin}${route}`
}

function moneyFmt(v) {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (!Number.isFinite(n)) return String(v)
  const cur = summary.value?.currency || 'USD'
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: cur,
      maximumFractionDigits: 2,
    }).format(n)
  } catch {
    return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
}

function formatKpiValue(card) {
  if (['pending_approvals', 'unreconciled'].includes(card.id)) {
    return String(Math.round(Number(card.value || 0)))
  }
  return moneyFmt(card.value)
}

function kpiSubtitle(card) {
  const cmp = summary.value?.previous_period_label
  if (card.delta_pct != null && cmp) return `vs ${cmp}`
  if (card.id === 'pending_approvals' && card.urgent_count != null) {
    const u = Number(card.urgent_count || 0)
    return u ? `${u} urgent` : ''
  }
  if (card.id === 'unreconciled' && card.subtitle_amount != null) {
    return moneyFmt(card.subtitle_amount)
  }
  return card.subtitle || ''
}

function glAmount(r) {
  const d = Number(r.debit || 0)
  const c = Number(r.credit || 0)
  if (d) return moneyFmt(d)
  if (c) return moneyFmt(-c)
  return '—'
}

function dueTone(row) {
  if (!row?.due_date) return 'due'
  const due = new Date(String(row.due_date).slice(0, 10) + 'T12:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return due < today ? 'overdue' : 'due'
}

function dueLabel(row) {
  if (row.status === 'Overdue' || dueTone(row) === 'overdue') return 'Overdue'
  if (!row?.due_date) return 'Due'
  const due = new Date(String(row.due_date).slice(0, 10) + 'T12:00:00')
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const ms = due - today
  const days = Math.ceil(ms / (86400000))
  if (days <= 0) return 'Overdue'
  return `Due in ${days} days`
}

async function loadCompanies() {
  try {
    const res = await frappeRequest({
      url: '/api/method/frappe.client.get_list',
      method: 'POST',
      params: {
        doctype: 'Company',
        fields: ['name'],
        limit_page_length: 100,
      },
    })
    companies.value = res || []
    if (!company.value && companies.value.length) {
      company.value = companies.value[0].name
    }
  } catch (e) {
    error.value = e.message || String(e)
  }
}

async function loadSummary() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await frappeRequest({
      url: '/api/method/accounting_workbench.api.dashboard_summary',
      method: 'POST',
      params: {
        company: company.value,
        from_date: fromDate.value,
        to_date: toDate.value,
      },
    })
    summary.value = res
    lastSynced.value = new Date().toLocaleString()
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function monthBounds() {
  const d = new Date()
  const start = new Date(d.getFullYear(), d.getMonth(), 1)
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  const iso = (x) => x.toISOString().slice(0, 10)
  return { from: iso(start), to: iso(end) }
}

onMounted(async () => {
  const m = monthBounds()
  fromDate.value = m.from
  toDate.value = m.to
  await loadCompanies()
  await loadSummary()
})

watch([company, fromDate, toDate], () => {
  loadSummary()
})
</script>
