<template>
  <div class="flex min-h-0 flex-1 flex-col bg-[#f4f6fb]">
    <!-- Top header (matches Accounting Workspace dashboard chrome) -->
    <header class="border-b border-slate-200/80 bg-white px-8 py-6 shadow-sm">
      <div class="flex flex-wrap items-start gap-6">
        <div class="min-w-[200px] flex-1">
          <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">Accounting Workspace</p>
          <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">Accounting Workspace</h1>
          <p class="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">
            Your command center for smart accounting.
          </p>
        </div>
        <div class="flex flex-1 justify-center">
          <div class="relative w-full max-w-md">
            <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
            <input
              v-model="headerSearch"
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
          <span
            class="relative inline-flex h-11 w-11 cursor-pointer items-center justify-center rounded-full bg-slate-100 text-lg text-slate-600 ring-1 ring-slate-200/80"
          >
            🔔
            <span
              v-if="bellCount > 0"
              class="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
              >{{ bellCount > 99 ? '99+' : bellCount }}</span
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
          <select v-model="company" class="max-w-[16rem] border-0 bg-transparent text-sm font-medium outline-none">
            <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
          </select>
        </div>
        <div class="ml-auto text-xs text-slate-500">{{ periodLabel }}</div>
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto px-8 py-6">
        <div class="mb-6">
          <p class="text-[11px] font-bold uppercase tracking-[0.14em] text-blue-600">Journal Entries</p>
          <h2 class="mt-1 text-xl font-bold text-slate-900">Journal Entries</h2>
          <p class="mt-1 text-sm text-slate-600">Create, review and manage journal entries.</p>
        </div>

        <!-- Primary actions -->
        <section class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
            @click="goDesk('/app/journal-entry/new')"
          >
            + New Journal Entry
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
            @click="goDesk('/app/data-import-tool/Journal%20Entry')"
          >
            <span class="text-base leading-none">⬆</span>
            Bulk Upload
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-xl border-2 border-violet-500 bg-white px-4 py-2.5 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
            @click="goDesk('/app/auto-repeat?reference_doctype=Journal%20Entry')"
          >
            <span class="text-base leading-none">↻</span>
            Recurring Entries
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-600 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-50"
            @click="goDesk('/app/data-import-tool/Journal%20Entry')"
          >
            <span class="text-base leading-none">▦</span>
            Import from Excel
          </button>
          <div class="relative">
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
              @click="moreOpen = !moreOpen"
            >
              More Actions
              <span class="text-xs text-slate-400">▾</span>
            </button>
            <div
              v-if="moreOpen"
              class="absolute left-0 z-20 mt-1 min-w-[200px] rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
            >
              <button
                type="button"
                class="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
                @click="
                  goDesk('/app/journal-entry');
                  moreOpen = false
                "
              >
                Journal Entry list (Desk)
              </button>
              <button
                type="button"
                class="block w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
                @click="
                  goDesk('/app/query-report/General%20Ledger');
                  moreOpen = false
                "
              >
                General Ledger
              </button>
            </div>
          </div>
        </section>

        <section v-if="error" class="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {{ error }}
        </section>

        <!-- KPI row -->
        <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <div
            v-for="card in data?.kpis || []"
            :key="card.id"
            class="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <div class="flex items-start justify-between gap-2">
              <span class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{{ card.label }}</span>
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-lg"
                :class="kpiIconWrap(card.id)"
                >{{ kpiIcon(card.id) }}</span
              >
            </div>
            <div class="mt-3 flex items-end justify-between gap-2">
              <span class="text-[22px] font-bold tabular-nums leading-none text-slate-900">{{
                formatKpi(card)
              }}</span>
              <span
                v-if="card.delta_pct != null"
                class="shrink-0 text-xs font-bold tabular-nums"
                :class="card.delta_pct >= 0 ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ card.delta_pct >= 0 ? '+' : '' }}{{ card.delta_pct }}%
              </span>
            </div>
            <p class="mt-2 text-[11px] text-slate-500">
              vs {{ data?.previous_period_label || 'prior period' }}
            </p>
          </div>
        </section>

        <!-- Filters + table -->
        <section class="mt-6 rounded-2xl border border-slate-200/80 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
          <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 px-5 py-4">
            <div class="relative min-w-[180px] flex-1">
              <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
              <input
                v-model="tableSearch"
                type="search"
                placeholder="Search journal entries..."
                class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm outline-none focus:border-blue-400 focus:bg-white"
                @keydown.enter="applyFilters"
              />
            </div>
            <select
              v-model="filterStatus"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
            >
              <option value="">All Status</option>
              <option value="posted">Posted</option>
              <option value="draft">Draft</option>
            </select>
            <select
              v-model="filterVoucherType"
              class="max-w-[10rem] rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
            >
              <option value="">All Types</option>
              <option v-for="vt in data?.voucher_types || []" :key="vt" :value="vt">{{ vt }}</option>
            </select>
            <select
              v-model="filterOwner"
              class="max-w-[10rem] rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
            >
              <option value="">All Users</option>
              <option v-for="o in data?.owners || []" :key="o" :value="o">{{ o }}</option>
            </select>
            <div class="flex items-center gap-2 text-sm text-slate-600">
              <input v-model="fromDate" type="date" class="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
              <span class="text-slate-400">→</span>
              <input v-model="toDate" type="date" class="rounded-lg border border-slate-200 px-2 py-1.5 text-xs" />
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
              @click="applyFilters"
            >
              <span>⚙</span> Filters
            </button>
            <button
              type="button"
              class="ml-auto inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50"
              title="Column preferences"
              @click="goDesk('/app/journal-entry')"
            >
              ⚙
            </button>
          </div>

          <div class="overflow-x-auto px-2 pb-2">
            <table class="w-full min-w-[880px] text-left text-xs">
              <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th class="px-3 py-3">Date</th>
                  <th class="px-3 py-3">Entry Number</th>
                  <th class="px-3 py-3">Reference</th>
                  <th class="px-3 py-3">Type</th>
                  <th class="px-3 py-3">Account</th>
                  <th class="px-3 py-3 text-right">Debit</th>
                  <th class="px-3 py-3 text-right">Credit</th>
                  <th class="px-3 py-3">Status</th>
                  <th class="px-3 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in data?.entries || []" :key="row.name" class="border-b border-slate-50 hover:bg-slate-50/80">
                  <td class="whitespace-nowrap px-3 py-2.5 text-slate-700">{{ row.posting_date }}</td>
                  <td class="px-3 py-2.5">
                    <button
                      type="button"
                      class="font-mono text-sm font-semibold text-blue-600 hover:underline"
                      @click="goDesk(`/app/journal-entry/${encodeURIComponent(row.name)}`)"
                    >
                      {{ row.name }}
                    </button>
                  </td>
                  <td class="max-w-[10rem] truncate px-3 py-2.5 text-slate-600">{{ row.reference || '—' }}</td>
                  <td class="max-w-[8rem] truncate px-3 py-2.5 text-slate-700">{{ row.voucher_type }}</td>
                  <td class="max-w-[12rem] truncate px-3 py-2.5 text-slate-600">{{ row.first_account || '—' }}</td>
                  <td class="px-3 py-2.5 text-right font-mono tabular-nums text-slate-900">{{ moneyFmt(row.total_debit) }}</td>
                  <td class="px-3 py-2.5 text-right font-mono tabular-nums text-slate-900">{{ moneyFmt(row.total_credit) }}</td>
                  <td class="px-3 py-2.5">
                    <span
                      class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold"
                      :class="row.docstatus === 1 ? 'bg-emerald-50 text-emerald-800' : 'bg-sky-50 text-sky-800'"
                    >
                      {{ row.docstatus === 1 ? 'Posted' : 'Draft' }}
                    </span>
                  </td>
                  <td class="px-3 py-2.5 text-right">
                    <button
                      type="button"
                      class="text-xs font-semibold text-blue-600 hover:underline"
                      @click="goDesk(`/app/journal-entry/${encodeURIComponent(row.name)}`)"
                    >
                      Open
                    </button>
                  </td>
                </tr>
                <tr v-if="!(data?.entries || []).length">
                  <td colspan="9" class="px-3 py-12 text-center text-sm text-slate-400">No journal entries in this period.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-xs text-slate-600">
            <span>
              Showing {{ showingFrom }} to {{ showingTo }} of {{ totalRows }} entries
            </span>
            <div class="flex flex-wrap items-center gap-1">
              <button
                type="button"
                class="rounded-lg border border-slate-200 px-2 py-1 font-medium hover:bg-slate-50 disabled:opacity-40"
                :disabled="page <= 1"
                @click="((page = 1), load())"
              >
                «
              </button>
              <template v-for="p in pageNumbers" :key="'p-' + String(p)">
                <span v-if="p === 'ellipsis'" class="px-1 font-medium text-slate-400">…</span>
                <button
                  v-else
                  type="button"
                  class="min-w-[2rem] rounded-lg border px-2 py-1 font-medium tabular-nums"
                  :class="
                    p === page ? 'border-blue-600 bg-blue-50 text-blue-800' : 'border-slate-200 hover:bg-slate-50'
                  "
                  @click="((page = p), load())"
                >
                  {{ p }}
                </button>
              </template>
              <button
                type="button"
                class="rounded-lg border border-slate-200 px-2 py-1 font-medium hover:bg-slate-50 disabled:opacity-40"
                :disabled="page >= totalPages"
                @click="((page = totalPages), load())"
              >
                »
              </button>
            </div>
          </div>
        </section>

        <footer class="mt-8 border-t border-slate-200/80 pt-5 text-xs text-slate-500">
          Same ERPNext documents · open any row in Desk for full detail.
        </footer>
      </div>

      <!-- Right rail -->
      <aside
        class="hidden w-[300px] shrink-0 overflow-y-auto border-l border-slate-200/80 bg-white px-5 py-6 shadow-[inset_1px_0_0_rgba(148,163,184,0.15)] lg:block xl:w-[320px]"
      >
        <h3 class="text-sm font-bold text-slate-900">Journal Entries by Type</h3>
        <p class="mt-1 text-[11px] text-slate-500">Posted entries in selected period.</p>
        <div class="mt-4 rounded-2xl border border-slate-100 bg-slate-50/50 p-4">
          <ExpenseDonut
            :rows="donutRows"
            :currency="data?.currency || 'USD'"
            :center-text="donutCenter"
          />
        </div>

        <h3 class="mt-8 text-sm font-bold text-slate-900">Quick Shortcuts</h3>
        <ul class="mt-4 space-y-3">
          <li v-for="s in quickShortcuts" :key="s.title">
            <button
              type="button"
              class="flex w-full items-start gap-3 rounded-xl border border-slate-100 bg-white p-3 text-left shadow-sm transition hover:border-blue-200 hover:bg-blue-50/50"
              @click="goDesk(s.route)"
            >
              <span
                class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-lg"
                :class="s.iconBg"
                >{{ s.icon }}</span
              >
              <span class="min-w-0">
                <span class="block text-sm font-semibold text-slate-900">{{ s.title }}</span>
                <span class="mt-0.5 block text-[11px] leading-snug text-slate-500">{{ s.sub }}</span>
              </span>
            </button>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import ExpenseDonut from '@/components/ExpenseDonut.vue'

const headerSearch = ref('')
const company = ref('')
const companies = ref([])
const fromDate = ref('')
const toDate = ref('')
const data = ref(null)
const error = ref('')
const moreOpen = ref(false)

const tableSearch = ref('')
const filterStatus = ref('')
const filterVoucherType = ref('')
const filterOwner = ref('')

const page = ref(1)
const pageSize = 8

const months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')

const quickShortcuts = [
  {
    title: 'Standard Journal',
    sub: 'Create a standard journal entry',
    icon: '📝',
    iconBg: 'bg-blue-100 text-blue-700',
    route: '/app/journal-entry/new',
  },
  {
    title: 'Adjusting Journal',
    sub: 'Period-end accruals & adjustments',
    icon: '⚖',
    iconBg: 'bg-teal-100 text-teal-700',
    route: '/app/journal-entry/new',
  },
  {
    title: 'Reversing Journal',
    sub: 'Auto-reverse prior period entries',
    icon: '↩',
    iconBg: 'bg-orange-100 text-orange-700',
    route: '/app/journal-entry/new',
  },
  {
    title: 'Closing Journal',
    sub: 'Year-end closing & allocations',
    icon: '🔒',
    iconBg: 'bg-violet-100 text-violet-700',
    route: '/app/journal-entry/new',
  },
]

const periodLabel = computed(() => {
  if (!fromDate.value || !toDate.value) return ''
  const a = new Date(fromDate.value + 'T12:00:00')
  const b = new Date(toDate.value + 'T12:00:00')
  return `${months[a.getMonth()]} ${a.getDate()} – ${months[b.getMonth()]} ${b.getDate()}, ${b.getFullYear()}`
})

const totalRows = computed(() => Number(data.value?.total_rows || 0))
const totalPages = computed(() => Math.max(1, Math.ceil(totalRows.value / pageSize)))

const draftKpi = computed(() => data.value?.kpis?.find((k) => k.id === 'draft'))
const bellCount = computed(() => {
  const d = Number(draftKpi.value?.value || 0)
  return Math.min(99, Math.max(d, 0))
})

const showingFrom = computed(() => {
  if (!totalRows.value) return 0
  return (page.value - 1) * pageSize + 1
})
const showingTo = computed(() => Math.min(page.value * pageSize, totalRows.value))

const donutRows = computed(() => data.value?.by_type || [])
const donutCenter = computed(() => {
  const n = Number(data.value?.posted_total_for_chart || 0)
  return n ? String(n) : '—'
})

const pageNumbers = computed(() => {
  const tp = totalPages.value
  const cur = page.value
  if (tp <= 7) {
    return Array.from({ length: tp }, (_, i) => i + 1)
  }
  const set = new Set([1, tp, cur, cur - 1, cur + 1].filter((x) => x >= 1 && x <= tp))
  const sorted = [...set].sort((a, b) => a - b)
  const out = []
  let prev = 0
  for (const x of sorted) {
    if (prev && x - prev > 1) out.push('ellipsis')
    out.push(x)
    prev = x
  }
  return out
})

function goDesk(route) {
  window.location.href = `${window.location.origin}${route}`
}

function monthBounds() {
  const d = new Date()
  const start = new Date(d.getFullYear(), d.getMonth(), 1)
  const end = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  const iso = (x) => x.toISOString().slice(0, 10)
  return { from: iso(start), to: iso(end) }
}

function kpiIcon(id) {
  const m = {
    total: '📒',
    posted: '✓',
    draft: '✎',
    debit: '↑',
    credit: '↓',
  }
  return m[id] || '◆'
}

function kpiIconWrap(id) {
  const m = {
    total: 'bg-blue-50 text-blue-600',
    posted: 'bg-emerald-50 text-emerald-600',
    draft: 'bg-amber-50 text-amber-600',
    debit: 'bg-indigo-50 text-indigo-600',
    credit: 'bg-rose-50 text-rose-600',
  }
  return m[id] || 'bg-slate-100 text-slate-600'
}

function moneyFmt(v) {
  if (v == null || v === '') return '—'
  const n = Number(v)
  if (!Number.isFinite(n)) return String(v)
  const cur = data.value?.currency || 'USD'
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: cur,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n)
  } catch {
    return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
}

function formatKpi(card) {
  if (card.format === 'int') return String(Math.round(Number(card.value || 0)))
  return moneyFmt(card.value)
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

async function load() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await frappeRequest({
      url: '/api/method/accounting_workbench.api.journal_entries_dashboard',
      method: 'POST',
      params: {
        company: company.value,
        from_date: fromDate.value,
        to_date: toDate.value,
        status: filterStatus.value,
        voucher_type: filterVoucherType.value || undefined,
        owner: filterOwner.value || undefined,
        search: tableSearch.value || undefined,
        limit_start: (page.value - 1) * pageSize,
        limit_page_length: pageSize,
      },
    })
    data.value = res
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function applyFilters() {
  page.value = 1
  load()
}

watch([company, fromDate, toDate], () => {
  page.value = 1
  load()
})

watch([filterStatus, filterVoucherType, filterOwner], () => {
  page.value = 1
  load()
})

onMounted(async () => {
  const m = monthBounds()
  fromDate.value = m.from
  toDate.value = m.to
  await loadCompanies()
  await load()
})
</script>
