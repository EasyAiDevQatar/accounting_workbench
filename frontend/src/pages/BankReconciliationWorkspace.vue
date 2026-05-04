<template>
  <JournalLikeShell
    title="Bank Reconciliation"
    subtitle="Match bank transactions with system vouchers and track unallocated lines."
    :companies="companies"
    :company="company"
    :from-date="fromDate"
    :to-date="toDate"
    :kpis="kpis"
    :error="error"
    :bell-count="Number(data?.kpis?.pending_count || 0)"
    @update:company="onCompanyChange"
    @update:fromDate="onFromDateChange"
    @update:toDate="onToDateChange"
  >
    <template #actions>
      <button
        type="button"
        class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
        @click="router.push({ name: 'bank-new' })"
      >
        + New Bank Transaction
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="router.push({ name: 'bank-transactions' })"
      >
        Bank Transactions
      </button>
    </template>

    <template #filters>
      <select
        v-model="status"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">All Statuses</option>
        <option v-for="st in statuses" :key="st" :value="st">{{ st }}</option>
      </select>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="load"
      >
        Apply Filters
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[940px] text-left text-xs">
        <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-3 py-3">Date</th>
            <th class="px-3 py-3">Transaction</th>
            <th class="px-3 py-3">Bank Account</th>
            <th class="px-3 py-3 text-right">Deposit</th>
            <th class="px-3 py-3 text-right">Withdrawal</th>
            <th class="px-3 py-3 text-right">Unallocated</th>
            <th class="px-3 py-3">Status</th>
            <th class="px-3 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in entries" :key="row.name" class="border-b border-slate-50 hover:bg-slate-50/80">
            <td class="whitespace-nowrap px-3 py-2.5 text-slate-700">{{ row.date }}</td>
            <td class="px-3 py-2.5 font-mono text-xs text-blue-600">{{ row.name }}</td>
            <td class="max-w-[16rem] truncate px-3 py-2.5 text-slate-700">{{ row.bank_account }}</td>
            <td class="px-3 py-2.5 text-right font-mono tabular-nums text-slate-900">{{ formatMoney(row.deposit || 0, currency) }}</td>
            <td class="px-3 py-2.5 text-right font-mono tabular-nums text-slate-900">{{ formatMoney(row.withdrawal || 0, currency) }}</td>
            <td class="px-3 py-2.5 text-right font-mono tabular-nums text-slate-900">{{ formatMoney(row.unallocated_amount || 0, currency) }}</td>
            <td class="px-3 py-2.5">
              <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold" :class="statusClass(row.status)">
                {{ row.status }}
              </span>
            </td>
            <td class="px-3 py-2.5 text-right">
              <button type="button" class="text-xs font-semibold text-blue-600 hover:underline" @click="router.push({ name: 'bank-transactions', query: { search: row.name } })">
                Open
              </button>
            </td>
          </tr>
          <tr v-if="!entries.length">
            <td colspan="8" class="px-3 py-12 text-center text-sm text-slate-400">No bank transactions in this range.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>Showing {{ entries.length }} bank rows</span>
      <span class="font-medium text-slate-700">
        Unallocated: {{ formatMoney(Number(data?.kpis?.unallocated_total || 0), currency) }}
      </span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Reconciliation Tips</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Use Pending and Unreconciled filters to clear old bank lines first.</li>
        <li>Allocate lines to Payment Entry whenever possible to keep AP/AR accurate.</li>
        <li>Open the Bank Reconciliation Tool for full matching workflows.</li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeRequest } from 'frappe-ui'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench, formatMoney } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const companies = ref([])
const router = useRouter()
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const status = ref('')
const data = ref(null)
const entries = ref([])
const error = ref('')

const statuses = computed(() => data.value?.statuses || [])
const currency = computed(() => data.value?.currency || 'USD')
const kpis = computed(() => [
  { id: 'pending', label: 'Pending', icon: '⌛', value: Number(data.value?.kpis?.pending_count || 0), subtitle: 'Pending bank lines' },
  { id: 'unreconciled', label: 'Unreconciled', icon: '⌁', value: Number(data.value?.kpis?.unreconciled_count || 0), subtitle: 'Need allocation' },
  { id: 'unallocated', label: 'Unallocated', icon: '¤', value: formatMoney(Number(data.value?.kpis?.unallocated_total || 0), currency.value), subtitle: 'Amount waiting for match' },
  { id: 'inperiod', label: 'In Range', icon: '▦', value: Number(data.value?.kpis?.in_period_count || 0), subtitle: 'Transactions listed' },
  { id: 'scope', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current company scope' },
])

function statusClass(st) {
  if (st === 'Pending') return 'bg-amber-50 text-amber-700'
  if (st === 'Unreconciled') return 'bg-blue-50 text-blue-700'
  return 'bg-emerald-50 text-emerald-700'
}

async function loadCompanies() {
  companies.value = (await frappeRequest({
    url: '/api/method/frappe.client.get_list',
    method: 'POST',
    params: { doctype: 'Company', fields: ['name'], limit_page_length: 100 },
  })) || []
  if (!company.value && companies.value.length) company.value = companies.value[0].name
}

async function load() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await callWorkbench('bank_reconciliation_workspace', {
      company: company.value,
      from_date: fromDate.value,
      to_date: toDate.value,
      status: status.value || undefined,
    })
    data.value = res
    entries.value = res.entries || []
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }

watch([company, fromDate, toDate], load)

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await load()
})
</script>
