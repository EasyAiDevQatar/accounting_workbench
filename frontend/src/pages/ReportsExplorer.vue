<template>
  <JournalLikeShell
    title="Reports Explorer"
    subtitle="Run core financial statements and drill into ledger outputs."
    :companies="companies"
    :company="company"
    :from-date="fromDate"
    :to-date="toDate"
    :kpis="kpis"
    :error="error"
    @update:company="onCompanyChange"
    @update:fromDate="onFromDateChange"
    @update:toDate="onToDateChange"
  >
    <template #actions>
      <button
        type="button"
        class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
        @click="runReport"
      >
        Run Report
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="runReport"
      >
        Refresh Data
      </button>
    </template>

    <template #filters>
      <select
        v-model="reportName"
        class="min-w-[220px] rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option v-for="r in reportOptions" :key="r" :value="r">{{ r }}</option>
      </select>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="runReport"
      >
        Apply Scope
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[980px] text-left text-xs">
        <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th v-for="col in tableColumns" :key="col.fieldname || col.label" class="px-3 py-3">
              {{ col.label || col.fieldname }}
            </th>
            <th class="px-3 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in tableRows" :key="idx" class="border-b border-slate-50 hover:bg-slate-50/80">
            <td v-for="col in tableColumns" :key="`${idx}-${col.fieldname || col.label}`" class="px-3 py-2.5 text-slate-700">
              {{ cellValue(row, col) }}
            </td>
            <td class="px-3 py-2.5 text-right">
              <button
                v-if="drillRoute(row)"
                type="button"
                class="text-xs font-semibold text-blue-600 hover:underline"
                @click="goDrill(row)"
              >
                Drill
              </button>
            </td>
          </tr>
          <tr v-if="!tableRows.length">
            <td :colspan="Math.max(tableColumns.length + 1, 1)" class="px-3 py-12 text-center text-sm text-slate-400">
              Run a report to load results.
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>{{ tableRows.length }} rows returned</span>
      <span class="font-medium text-slate-700">{{ reportName }}</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Report Scope</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Use company and date range in header to align all statements.</li>
        <li>General Ledger and Trial Balance are best for audit trace checks.</li>
        <li>P&L, Balance Sheet and Cash Flow validate posting-level correctness.</li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { frappeRequest } from 'frappe-ui'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const companies = ref([])
const router = useRouter()
const route = useRoute()
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const reportOptions = ref([])
const reportName = ref('General Ledger')
const tableColumns = ref([])
const tableRows = ref([])
const error = ref('')

const kpis = computed(() => [
  { id: 'report', label: 'Selected Report', icon: '▨', value: reportName.value || '—', subtitle: 'Active report' },
  { id: 'rows', label: 'Rows', icon: '▦', value: tableRows.value.length, subtitle: 'Returned rows' },
  { id: 'cols', label: 'Columns', icon: '≡', value: tableColumns.value.length, subtitle: 'Visible columns' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current scope' },
  { id: 'range', label: 'Date Range', icon: '📅', value: `${fromDate.value || ''} → ${toDate.value || ''}`, subtitle: 'Filter window' },
])

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }

function cellValue(row, col) {
  if (Array.isArray(row)) {
    const idx = Number(col?.index ?? -1)
    return idx >= 0 ? row[idx] : ''
  }
  return row?.[col.fieldname] ?? ''
}

function drillRoute(row) {
  if (!row || Array.isArray(row)) return ''
  if (row.voucher_type && row.voucher_no) {
    const voucherType = String(row.voucher_type)
    if (voucherType === 'Sales Invoice') return { name: 'invoices', query: { search: row.voucher_no } }
    if (voucherType === 'Purchase Invoice') return { name: 'bills', query: { search: row.voucher_no } }
    if (voucherType === 'Payment Entry') return { name: 'payments', query: { search: row.voucher_no } }
    if (voucherType === 'Journal Entry') return { name: 'journal' }
    return ''
  }
  return ''
}

async function loadCompanies() {
  companies.value = (await frappeRequest({
    url: '/api/method/frappe.client.get_list',
    method: 'POST',
    params: { doctype: 'Company', fields: ['name'], limit_page_length: 100 },
  })) || []
  if (!company.value && companies.value.length) company.value = companies.value[0].name
}

async function loadMeta() {
  const res = await callWorkbench('reports_explorer_meta', { company: company.value || undefined })
  reportOptions.value = res.reports || []
  if (!reportOptions.value.includes(reportName.value) && reportOptions.value.length) {
    reportName.value = reportOptions.value[0]
  }
}

async function runReport() {
  if (!reportName.value) return
  error.value = ''
  try {
    const payload = await callWorkbench('run_accounts_report', {
      report_name: reportName.value,
      filters: JSON.stringify({
        company: company.value || undefined,
        from_date: fromDate.value || undefined,
        to_date: toDate.value || undefined,
      }),
    })
    tableColumns.value = (payload.columns || []).map((col, index) => ({ ...col, index }))
    tableRows.value = payload.result || []
  } catch (e) {
    error.value = e.message || String(e)
    tableColumns.value = []
    tableRows.value = []
  }
}

function goDrill(row) {
  const target = drillRoute(row)
  if (target) router.push(target)
}

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await loadMeta()
  if (route.query?.report && reportOptions.value.includes(String(route.query.report))) {
    reportName.value = String(route.query.report)
  }
  await runReport()
})
</script>
