<template>
  <JournalLikeShell
    title="Settings"
    subtitle="Company, fiscal year, and accounting dimensions defaults."
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
        @click="router.push({ name: 'companies' })"
      >
        Companies
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-violet-500 bg-white px-4 py-2.5 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
        @click="router.push({ name: 'dimensions' })"
      >
        Dimensions
      </button>
    </template>

    <template #filters>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="load"
      >
        Refresh
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[900px] text-left text-xs">
        <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-3 py-3">Dimension</th>
            <th class="px-3 py-3">Document Type</th>
            <th class="px-3 py-3">Disabled</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in dimensions" :key="row.name" class="border-b border-slate-50 hover:bg-slate-50/80">
            <td class="px-3 py-2.5 font-mono text-blue-600">{{ row.name }}</td>
            <td class="px-3 py-2.5 text-slate-700">{{ row.document_type || '—' }}</td>
            <td class="px-3 py-2.5 text-slate-700">{{ row.disabled ? 'Yes' : 'No' }}</td>
          </tr>
          <tr v-if="!dimensions.length">
            <td colspan="3" class="px-3 py-12 text-center text-sm text-slate-400">No accounting dimensions configured.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>{{ dimensions.length }} accounting dimensions</span>
      <span class="font-medium text-slate-700">Active FY: {{ activeFiscalYear || '—' }}</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Current Defaults</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Default Currency: {{ companyDefaults.default_currency || '—' }}</li>
        <li>Default Cost Center: {{ companyDefaults.cost_center || '—' }}</li>
        <li>Country: {{ companyDefaults.country || '—' }}</li>
      </ul>
      <h4 class="mt-5 text-xs font-semibold uppercase tracking-wide text-slate-500">Fiscal Years</h4>
      <ul class="mt-2 space-y-1 text-xs text-slate-600">
        <li v-for="fy in fiscalYears.slice(0, 6)" :key="fy.name">
          {{ fy.name }} ({{ fy.year_start_date }} → {{ fy.year_end_date }})
        </li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { frappeRequest } from 'frappe-ui'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const companies = ref([])
const router = useRouter()
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const dimensions = ref([])
const companyDefaults = ref({})
const activeFiscalYear = ref('')
const fiscalYears = ref([])
const error = ref('')

const kpis = computed(() => [
  { id: 'dimensions', label: 'Dimensions', icon: '▦', value: dimensions.value.length, subtitle: 'Accounting dimensions' },
  { id: 'fiscal', label: 'Active Fiscal Year', icon: '📅', value: activeFiscalYear.value || '—', subtitle: 'Current fiscal context' },
  { id: 'currency', label: 'Default Currency', icon: '¤', value: companyDefaults.value.default_currency || '—', subtitle: 'Company default' },
  { id: 'cc', label: 'Default Cost Center', icon: '▧', value: companyDefaults.value.cost_center || '—', subtitle: 'Company default' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Selected company' },
])

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
    const res = await callWorkbench('settings_workspace', { company: company.value })
    dimensions.value = res.dimensions || []
    companyDefaults.value = res.company_defaults || {}
    activeFiscalYear.value = res.active_fiscal_year || ''
    fiscalYears.value = res.fiscal_years || []
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }

watch(company, load)

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await load()
})
</script>
