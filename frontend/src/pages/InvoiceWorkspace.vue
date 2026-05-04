<template>
  <JournalLikeShell
    :title="invoiceType === 'Purchase' ? 'Bills' : 'Invoices'"
    :subtitle="invoiceType === 'Purchase' ? 'Manage supplier bills, outstanding balances and AP workflow.' : 'Manage customer invoices, collections and AR workflow.'"
    :companies="companies"
    :company="company"
    :from-date="fromDate"
    :to-date="toDate"
    :kpis="kpis"
    :error="error"
    :bell-count="draftCount"
    @update:company="onCompanyChange"
    @update:fromDate="onFromDateChange"
    @update:toDate="onToDateChange"
  >
    <template #actions>
      <button
        type="button"
        class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
        @click="openCreate"
      >
        + New {{ invoiceType === 'Purchase' ? 'Bill' : 'Invoice' }}
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="router.push({ name: invoiceType === 'Purchase' ? 'bills-new' : 'invoices-new' })"
      >
        Go To Create Page
      </button>
    </template>

    <template #filters>
      <select
        v-model="party"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">All {{ invoiceType === 'Purchase' ? 'Suppliers' : 'Customers' }}</option>
        <option v-for="p in (meta?.parties || [])" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
      <select
        v-model="status"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">All Status</option>
        <option value="Draft">Draft</option>
        <option value="Submitted">Submitted</option>
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
      <table class="w-full min-w-[900px] text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-2 py-2">Invoice</th>
            <th class="px-2 py-2">Party</th>
            <th class="px-2 py-2">Posting Date</th>
            <th class="px-2 py-2">Due Date</th>
            <th class="px-2 py-2 text-right">Grand Total</th>
            <th class="px-2 py-2 text-right">Outstanding</th>
            <th class="px-2 py-2">Status</th>
            <th class="px-2 py-2 text-right">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.name" class="border-t border-slate-100 hover:bg-slate-50">
            <td class="px-2 py-2 font-mono text-blue-700">{{ row.name }}</td>
            <td class="px-2 py-2 text-slate-700">{{ row.party }}</td>
            <td class="px-2 py-2 text-slate-600">{{ row.posting_date }}</td>
            <td class="px-2 py-2 text-slate-600">{{ row.due_date || '—' }}</td>
            <td class="px-2 py-2 text-right font-mono">{{ formatMoney(row.grand_total, row.currency || currency) }}</td>
            <td class="px-2 py-2 text-right font-mono">{{ formatMoney(row.outstanding_amount, row.currency || currency) }}</td>
            <td class="px-2 py-2">
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{{ row.status }}</span>
            </td>
            <td class="px-2 py-2 text-right">
              <button
                type="button"
                class="text-xs font-semibold text-blue-600 hover:underline"
                @click="goToPayments(row.party)"
              >
                Receive/Pay
              </button>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="8" class="px-2 py-10 text-center text-sm text-slate-400">No records found.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>Showing {{ rows.length }} {{ invoiceType === 'Purchase' ? 'bills' : 'invoices' }}</span>
      <span class="font-medium text-slate-700">Outstanding {{ formatMoney(outstandingTotal, currency) }}</span>
    </template>

    <template #afterTable>
      <section v-if="showCreate" class="mt-6 rounded-2xl border border-blue-200 bg-white p-5">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="text-base font-semibold text-slate-900">Create {{ invoiceType === 'Purchase' ? 'Bill' : 'Invoice' }}</h3>
          <button type="button" class="text-sm text-slate-500 hover:text-slate-700" @click="showCreate = false">Close</button>
        </div>
        <div class="grid gap-3 md:grid-cols-4">
          <input v-model="form.posting_date" type="date" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
          <input v-model="form.due_date" type="date" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
          <select v-model="form.party" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">{{ invoiceType === 'Purchase' ? 'Select supplier' : 'Select customer' }}</option>
            <option v-for="p in (meta?.parties || [])" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
          <select v-model="form.taxes_and_charges" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">No tax template</option>
            <option v-for="t in (meta?.tax_templates || [])" :key="t.name" :value="t.name">{{ t.name }}</option>
          </select>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="w-full min-w-[760px] text-sm">
            <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-2 py-2">Item</th>
                <th class="px-2 py-2">Qty</th>
                <th class="px-2 py-2">Rate</th>
                <th class="px-2 py-2">Cost Center</th>
                <th class="px-2 py-2 text-right">Amount</th>
                <th class="px-2 py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in form.items" :key="idx" class="border-t border-slate-100">
                <td class="px-2 py-2">
                  <select v-model="item.item_code" class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm">
                    <option value="">Select item</option>
                    <option v-for="it in (meta?.items || [])" :key="it.name" :value="it.name">{{ it.name }}</option>
                  </select>
                </td>
                <td class="px-2 py-2"><input v-model.number="item.qty" type="number" min="0" step="0.001" class="w-24 rounded-lg border border-slate-200 px-2 py-1.5 text-sm" /></td>
                <td class="px-2 py-2"><input v-model.number="item.rate" type="number" min="0" step="0.001" class="w-28 rounded-lg border border-slate-200 px-2 py-1.5 text-sm" /></td>
                <td class="px-2 py-2">
                  <select v-model="item.cost_center" class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm">
                    <option value="">Select cost center</option>
                    <option v-for="cc in (meta?.cost_centers || [])" :key="cc.name" :value="cc.name">{{ cc.name }}</option>
                  </select>
                </td>
                <td class="px-2 py-2 text-right font-mono">{{ formatMoney((item.qty || 0) * (item.rate || 0), currency) }}</td>
                <td class="px-2 py-2 text-right">
                  <button type="button" class="text-xs text-red-600 hover:underline" @click="removeItem(idx)">Remove</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mt-4 flex items-center gap-2">
          <button type="button" class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm" @click="addItem">+ Add Item</button>
          <div class="ml-auto text-sm font-semibold text-slate-700">Total: {{ formatMoney(invoiceTotal, currency) }}</div>
          <button type="button" class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700" @click="createInvoice(true)">Submit</button>
        </div>
      </section>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">{{ invoiceType === 'Purchase' ? 'Bills' : 'Invoices' }} Tips</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Submitted vouchers post accounting impact automatically.</li>
        <li>Use tax templates to keep tax lines ERPNext-compliant.</li>
        <li>Use Receive/Pay action to continue workflow in Payments.</li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useRouter } from 'vue-router'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench, formatMoney } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const props = defineProps({
  invoiceType: { type: String, default: 'Sales' },
})

const router = useRouter()
const companies = ref([])
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const party = ref('')
const status = ref('')
const rows = ref([])
const currency = ref('USD')
const meta = ref(null)
const error = ref('')
const showCreate = ref(false)
const form = ref({ posting_date: '', due_date: '', party: '', taxes_and_charges: '', items: [] })

const invoiceTotal = computed(() =>
  (form.value.items || []).reduce((acc, it) => acc + Number(it.qty || 0) * Number(it.rate || 0), 0)
)
const outstandingTotal = computed(() =>
  rows.value.reduce((acc, row) => acc + Number(row.outstanding_amount || 0), 0)
)
const draftCount = computed(() => rows.value.filter((row) => String(row.status || '').toLowerCase() === 'draft').length)
const kpis = computed(() => [
  { id: 'total', label: 'Total', icon: '▤', value: rows.value.length, subtitle: `${props.invoiceType} documents` },
  { id: 'draft', label: 'Draft', icon: '✎', value: draftCount.value, subtitle: 'Need submission' },
  { id: 'outstanding', label: 'Outstanding', icon: '¤', value: formatMoney(outstandingTotal.value, currency.value), subtitle: 'Open balance' },
  { id: 'party', label: 'Party Filter', icon: '◉', value: party.value || 'All', subtitle: 'Current party scope' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current company' },
])

function addItem() {
  form.value.items.push({ item_code: '', qty: 1, rate: 0, cost_center: '' })
}

function removeItem(index) {
  form.value.items.splice(index, 1)
}

function openCreate() {
  showCreate.value = true
  form.value = {
    posting_date: new Date().toISOString().slice(0, 10),
    due_date: new Date().toISOString().slice(0, 10),
    party: '',
    taxes_and_charges: '',
    items: [{ item_code: '', qty: 1, rate: 0, cost_center: '' }],
  }
}

function goToPayments(selectedParty) {
  router.push({ name: 'payments', query: { party: selectedParty, type: props.invoiceType === 'Purchase' ? 'Pay' : 'Receive' } })
}

async function loadCompanies() {
  const res = await frappeRequest({
    url: '/api/method/frappe.client.get_list',
    method: 'POST',
    params: { doctype: 'Company', fields: ['name'], limit_page_length: 200 },
  })
  companies.value = res || []
  if (!company.value && companies.value.length) company.value = companies.value[0].name
}

async function loadMeta() {
  if (!company.value) return
  meta.value = await callWorkbench('invoice_form_meta', { invoice_type: props.invoiceType, company: company.value })
  currency.value = meta.value?.currency || 'USD'
}

async function load() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await callWorkbench('invoice_workspace', {
      invoice_type: props.invoiceType,
      company: company.value,
      party: party.value || undefined,
      status: status.value || undefined,
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      limit_page_length: 100,
    })
    rows.value = res.entries || []
    currency.value = res.currency || currency.value
  } catch (e) {
    error.value = e.message || String(e)
  }
}

async function createInvoice(submit) {
  error.value = ''
  try {
    await callWorkbench('submit_invoice', {
      data: JSON.stringify({
        type: props.invoiceType,
        company: company.value,
        party: form.value.party,
        posting_date: form.value.posting_date,
        due_date: form.value.due_date,
        taxes_and_charges: form.value.taxes_and_charges || undefined,
        items: form.value.items.filter((it) => it.item_code),
        submit,
      }),
    })
    showCreate.value = false
    await load()
  } catch (e) {
    error.value = e.message || String(e)
  }
}

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await loadMeta()
  await load()
})

watch([company, fromDate, toDate], async () => {
  await loadMeta()
  await load()
})

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }
</script>
