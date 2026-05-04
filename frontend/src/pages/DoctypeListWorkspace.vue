<template>
  <JournalLikeShell
    :title="title"
    :subtitle="subtitle"
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
        @click="goCreate"
      >
        + New {{ title }}
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="load"
      >
        Refresh
      </button>
    </template>

    <template #filters>
      <input
        v-model="search"
        type="search"
        placeholder="Search by name"
        class="w-full max-w-sm rounded-xl border border-slate-200 bg-slate-50 py-2 px-3 text-sm outline-none focus:border-blue-400 focus:bg-white"
        @keydown.enter="applyFilters"
      />
      <select
        v-if="fields.includes('docstatus')"
        v-model="docstatus"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">All Status</option>
        <option value="0">Draft</option>
        <option value="1">Submitted</option>
        <option value="2">Cancelled</option>
      </select>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="applyFilters"
      >
        Apply Filters
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[900px] text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th v-for="field in fields" :key="field" class="px-2 py-2">{{ prettyLabel(field) }}</th>
            <th class="px-2 py-2 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.name" class="border-t border-slate-100 hover:bg-slate-50">
            <td v-for="field in fields" :key="`${row.name}-${field}`" class="px-2 py-2 text-slate-700">
              <span v-if="field === 'name'" class="font-mono text-blue-700">{{ row[field] }}</span>
              <span v-else>{{ row[field] ?? '—' }}</span>
            </td>
            <td class="px-2 py-2 text-right">
              <button type="button" class="text-xs font-semibold text-blue-600 hover:underline" @click="goView(row.name)">
                View
              </button>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="fields.length + 1" class="px-2 py-10 text-center text-sm text-slate-400">No records found.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>Showing {{ rows.length }} rows</span>
      <span class="font-medium text-slate-700">Total {{ totalRows }}</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">{{ title }} guidance</h3>
      <p class="mt-3 text-xs text-slate-600">
        This is a fully native workspace list view. Use create route to add records without Desk.
      </p>
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

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  doctype: { type: String, required: true },
  createRouteName: { type: String, required: true },
})

const router = useRouter()
const companies = ref([])
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const search = ref('')
const docstatus = ref('')
const fields = ref(['name'])
const rows = ref([])
const totalRows = ref(0)
const error = ref('')

const kpis = computed(() => [
  { id: 'rows', label: 'Rows', icon: '▦', value: rows.value.length, subtitle: 'Current page rows' },
  { id: 'total', label: 'Total', icon: '≡', value: totalRows.value, subtitle: 'Total matching records' },
  { id: 'doctype', label: 'Doctype', icon: '◉', value: props.doctype, subtitle: 'Source doctype' },
  { id: 'search', label: 'Search', icon: '⌕', value: search.value || 'None', subtitle: 'Active filter' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current context' },
])

function prettyLabel(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (m) => m.toUpperCase())
}

function goCreate() {
  router.push({ name: props.createRouteName })
}

function goView(name) {
  router.push({ name: props.createRouteName, query: { clone_from: name } })
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
  error.value = ''
  try {
    const filters = {}
    if (docstatus.value !== '') filters.docstatus = Number(docstatus.value)
    if (company.value && props.doctype !== 'Company' && props.doctype !== 'Fiscal Year' && props.doctype !== 'Accounting Dimension') {
      filters.company = company.value
    }
    const res = await callWorkbench('list_doctype_workspace', {
      doctype: props.doctype,
      filters: JSON.stringify(filters),
      search: search.value || undefined,
      limit_page_length: 100,
    })
    fields.value = res.fields || ['name']
    rows.value = res.rows || []
    totalRows.value = Number(res.total_rows || 0)
  } catch (e) {
    error.value = e.message || String(e)
    rows.value = []
    totalRows.value = 0
  }
}

function applyFilters() {
  load()
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
