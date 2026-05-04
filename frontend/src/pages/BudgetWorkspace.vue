<template>
  <JournalLikeShell
    title="Budget Control"
    subtitle="Manage budgets and monitor annual limits by fiscal year."
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
        @click="router.push({ name: 'budget-new' })"
      >
        + New Budget
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="router.push({ name: 'reports', query: { report: 'Budget Variance Report' } })"
      >
        Budget Variance Report
      </button>
    </template>

    <template #filters>
      <select
        v-model="fiscalYear"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">All Fiscal Years</option>
        <option v-for="fy in fiscalYears" :key="fy.name" :value="fy.name">{{ fy.name }}</option>
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
      <table class="w-full min-w-[860px] text-left text-xs">
        <thead class="border-b border-slate-200 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-3 py-3">Budget</th>
            <th class="px-3 py-3">Fiscal Year</th>
            <th class="px-3 py-3">Action On Exceed</th>
            <th class="px-3 py-3">Material Request Rule</th>
            <th class="px-3 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in entries" :key="row.name" class="border-b border-slate-50 hover:bg-slate-50/80">
            <td class="px-3 py-2.5 font-mono text-blue-600">{{ row.name }}</td>
            <td class="px-3 py-2.5 text-slate-700">{{ row.fiscal_year }}</td>
            <td class="px-3 py-2.5 text-slate-700">{{ row.action_if_annual_budget_exceeded || '—' }}</td>
            <td class="px-3 py-2.5 text-slate-700">{{ row.applicable_on_material_request || '—' }}</td>
            <td class="px-3 py-2.5">
              <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold" :class="row.docstatus === 1 ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'">
                {{ row.docstatus === 1 ? 'Submitted' : 'Draft' }}
              </span>
            </td>
          </tr>
          <tr v-if="!entries.length">
            <td colspan="5" class="px-3 py-12 text-center text-sm text-slate-400">No budgets found for selected scope.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>Showing {{ entries.length }} budgets</span>
      <span class="font-medium text-slate-700">Use submitted budgets for control rules</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Budget Notes</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Draft budgets do not enforce spending controls.</li>
        <li>Use Budget Variance report to review overspend signals.</li>
        <li>Link budgets with Cost Center and Accounting Dimensions in Desk.</li>
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
const fiscalYear = ref('')
const entries = ref([])
const fiscalYears = ref([])
const data = ref(null)
const error = ref('')

const kpis = computed(() => [
  { id: 'total', label: 'Total Budgets', icon: '▧', value: Number(data.value?.kpis?.total_budgets || 0), subtitle: 'In selected scope' },
  { id: 'submitted', label: 'Submitted', icon: '✓', value: Number(data.value?.kpis?.submitted_budgets || 0), subtitle: 'Active control budgets' },
  { id: 'draft', label: 'Draft', icon: '✎', value: Number(data.value?.kpis?.draft_budgets || 0), subtitle: 'Pending submission' },
  { id: 'fy', label: 'Fiscal Year', icon: '📅', value: fiscalYear.value || 'All', subtitle: 'Applied filter' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current company' },
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
    const res = await callWorkbench('budget_workspace', {
      company: company.value,
      fiscal_year: fiscalYear.value || undefined,
    })
    data.value = res
    entries.value = res.entries || []
    fiscalYears.value = res.fiscal_years || []
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }

watch([company, fiscalYear], load)

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await load()
})
</script>
