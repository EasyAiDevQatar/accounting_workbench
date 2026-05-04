<template>
  <JournalLikeShell
    title="Chart of Accounts"
    subtitle="Manage account hierarchy and monitor live balances from posted entries."
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
        @click="load"
      >
        Refresh CoA
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="router.push({ name: 'coa-new' })"
      >
        + New Account
      </button>
    </template>

    <template #filters>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="expandAll"
      >
        Expand All
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="collapseAll"
      >
        Collapse All
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[880px] text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-2 py-2">Account</th>
            <th class="px-2 py-2">Root Type</th>
            <th class="px-2 py-2">Account Type</th>
            <th class="px-2 py-2">Currency</th>
            <th class="px-2 py-2 text-right">Balance</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in visibleRows"
            :key="row.name"
            class="border-t border-slate-100 hover:bg-slate-50"
          >
            <td class="px-2 py-2">
              <div class="flex items-center gap-2" :style="{ paddingLeft: `${row.depth * 18}px` }">
                <button
                  v-if="row.children?.length"
                  type="button"
                  class="inline-flex h-5 w-5 items-center justify-center rounded border border-slate-200 text-xs text-slate-500"
                  @click="toggle(row.name)"
                >
                  {{ expanded.has(row.name) ? '-' : '+' }}
                </button>
                <span v-else class="inline-block h-5 w-5"></span>
                <span :class="row.is_group ? 'font-semibold text-slate-800' : 'text-slate-700'">
                  {{ row.account_name }}
                </span>
              </div>
            </td>
            <td class="px-2 py-2 text-slate-600">{{ row.root_type || '—' }}</td>
            <td class="px-2 py-2 text-slate-600">{{ row.account_type || '—' }}</td>
            <td class="px-2 py-2 text-slate-600">{{ row.account_currency || data?.currency || '—' }}</td>
            <td class="px-2 py-2 text-right font-mono text-slate-900">
              {{ formatMoney(row.balance || 0, data?.currency || 'USD') }}
            </td>
          </tr>
          <tr v-if="!visibleRows.length">
            <td colspan="5" class="px-2 py-10 text-center text-sm text-slate-400">No accounts found.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>{{ data?.summary?.leaf_accounts || 0 }} posting accounts / {{ data?.summary?.total_accounts || 0 }} total</span>
      <span class="font-medium text-slate-700">Data source: Account + GL Entry</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">CoA Guidance</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Group accounts structure the tree; posting accounts receive transactions.</li>
        <li>Balances shown are computed from submitted GL Entries.</li>
        <li>Create or edit accounts in Desk when changing chart structure.</li>
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
const data = ref(null)
const error = ref('')
const expanded = ref(new Set())
const kpis = computed(() => [
  { id: 'total', label: 'Total Accounts', icon: '▦', value: Number(data.value?.summary?.total_accounts || 0), subtitle: 'Full chart nodes' },
  { id: 'leaf', label: 'Posting Accounts', icon: '▣', value: Number(data.value?.summary?.leaf_accounts || 0), subtitle: 'Leaf accounts' },
  { id: 'group', label: 'Group Accounts', icon: '▤', value: Number(data.value?.summary?.group_accounts || 0), subtitle: 'Hierarchy groups' },
  { id: 'currency', label: 'Currency', icon: '¤', value: data.value?.currency || '—', subtitle: 'Company default currency' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Selected scope' },
])

const visibleRows = computed(() => {
  const rows = []
  const walk = (nodes, depth = 0, parentVisible = true) => {
    for (const node of nodes || []) {
      if (!parentVisible) continue
      const row = { ...node, depth, is_group: Number(node.is_group) === 1 }
      rows.push(row)
      const showChildren = expanded.value.has(node.name)
      walk(node.children || [], depth + 1, showChildren)
    }
  }
  walk(data.value?.tree || [], 0, true)
  return rows
})

function toggle(name) {
  const next = new Set(expanded.value)
  if (next.has(name)) next.delete(name)
  else next.add(name)
  expanded.value = next
}

function expandAll() {
  const next = new Set()
  const walk = (nodes) => {
    for (const n of nodes || []) {
      if (n.children?.length) next.add(n.name)
      walk(n.children || [])
    }
  }
  walk(data.value?.tree || [])
  expanded.value = next
}

function collapseAll() {
  expanded.value = new Set()
}

async function loadCompanies() {
  const res = await frappeRequest({
    url: '/api/method/frappe.client.get_list',
    method: 'POST',
    params: {
      doctype: 'Company',
      fields: ['name'],
      limit_page_length: 200,
    },
  })
  companies.value = res || []
  if (!company.value && companies.value.length) company.value = companies.value[0].name
}

async function load() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await callWorkbench('coa_workspace', { company: company.value })
    data.value = res
    const initial = new Set((res.tree || []).map((r) => r.name))
    expanded.value = initial
  } catch (e) {
    error.value = e.message || String(e)
  }
}

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await load()
})

watch(company, load)

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }
</script>
