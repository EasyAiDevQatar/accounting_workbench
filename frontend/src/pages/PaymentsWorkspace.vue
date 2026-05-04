<template>
  <JournalLikeShell
    title="Payments"
    subtitle="Create Payment Entries, allocate to invoices, and monitor posted cash movement."
    :companies="companies"
    :company="company"
    :from-date="fromDate"
    :to-date="toDate"
    :kpis="kpis"
    :error="error"
    :bell-count="pendingCount"
    @update:company="onCompanyChange"
    @update:fromDate="onFromDateChange"
    @update:toDate="onToDateChange"
  >
    <template #actions>
      <button
        type="button"
        class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
        @click="submitPayment"
      >
        Submit Payment
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-emerald-500 bg-white px-4 py-2.5 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-50"
        @click="router.push({ name: 'payments-new' })"
      >
        + New Payment Entry
      </button>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-xl border-2 border-violet-500 bg-white px-4 py-2.5 text-sm font-semibold text-violet-700 transition hover:bg-violet-50"
        @click="goBank"
      >
        Reconciliation Queue
      </button>
    </template>

    <template #filters>
      <select
        v-model="form.payment_type"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="Receive">Receive</option>
        <option value="Pay">Pay</option>
      </select>
      <select
        v-model="form.party"
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none"
      >
        <option value="">Select party</option>
        <option v-for="p in partyOptions" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
      <input
        v-model.number="form.amount"
        type="number"
        min="0"
        step="0.01"
        placeholder="Amount"
        class="rounded-xl border border-slate-200 px-3 py-2 text-sm"
        @input="autoAllocate"
      />
      <button
        type="button"
        class="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
        @click="load"
      >
        Refresh
      </button>
    </template>

    <template #table>
      <table class="w-full min-w-[960px] text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th class="px-2 py-2">Payment Entry</th>
            <th class="px-2 py-2">Date</th>
            <th class="px-2 py-2">Type</th>
            <th class="px-2 py-2">Party</th>
            <th class="px-2 py-2 text-right">Paid</th>
            <th class="px-2 py-2 text-right">Received</th>
            <th class="px-2 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in entries" :key="row.name" class="border-t border-slate-100 hover:bg-slate-50">
            <td class="px-2 py-2 font-mono text-blue-700">{{ row.name }}</td>
            <td class="px-2 py-2 text-slate-600">{{ row.posting_date }}</td>
            <td class="px-2 py-2 text-slate-700">{{ row.payment_type }}</td>
            <td class="px-2 py-2 text-slate-700">{{ row.party_type }} / {{ row.party }}</td>
            <td class="px-2 py-2 text-right font-mono">{{ formatMoney(row.paid_amount, currency) }}</td>
            <td class="px-2 py-2 text-right font-mono">{{ formatMoney(row.received_amount, currency) }}</td>
            <td class="px-2 py-2"><span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{{ row.status }}</span></td>
          </tr>
          <tr v-if="!entries.length">
            <td colspan="7" class="px-2 py-10 text-center text-sm text-slate-400">No payment entries found.</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template #footer>
      <span>Showing {{ entries.length }} payments</span>
      <span class="font-medium text-slate-700">Allocated {{ formatMoney(allocatedTotal, currency) }} / Entered {{ formatMoney(form.amount || 0, currency) }}</span>
    </template>

    <template #afterTable>
      <section class="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
        <h3 class="text-sm font-semibold text-slate-900">Allocation Grid</h3>
        <div class="mt-3 grid gap-3 md:grid-cols-4">
          <input v-model="form.posting_date" type="date" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
          <select v-model="form.mode_of_payment" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">Mode of payment</option>
            <option v-for="m in options.mode_of_payments" :key="m.name" :value="m.name">{{ m.name }}</option>
          </select>
          <select v-model="form.bank_account" class="rounded-xl border border-slate-200 px-3 py-2 text-sm">
            <option value="">Bank/Cash account</option>
            <option v-for="a in options.bank_accounts" :key="a.name" :value="a.name">{{ a.name }}</option>
          </select>
          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
            Party Type: {{ partyType }}
          </div>
        </div>

        <div class="mt-4 overflow-x-auto">
          <table class="w-full min-w-[760px] text-sm">
            <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th class="px-2 py-2">Reference</th>
                <th class="px-2 py-2">Date</th>
                <th class="px-2 py-2 text-right">Outstanding</th>
                <th class="px-2 py-2 text-right">Allocate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in outstandingRows" :key="`${row.voucher_type}-${row.voucher_no}-${idx}`" class="border-t border-slate-100">
                <td class="px-2 py-2">
                  <div class="font-mono text-xs text-slate-700">{{ row.voucher_type }} / {{ row.voucher_no }}</div>
                  <div class="text-xs text-slate-500">{{ row.party || '' }}</div>
                </td>
                <td class="px-2 py-2 text-slate-600">{{ row.posting_date || row.due_date || '—' }}</td>
                <td class="px-2 py-2 text-right font-mono">{{ formatMoney(row.outstanding_amount || 0, currency) }}</td>
                <td class="px-2 py-2 text-right">
                  <input v-model.number="row.allocated_amount" type="number" min="0" :max="row.outstanding_amount || 0" step="0.01" class="w-28 rounded-lg border border-slate-200 px-2 py-1.5 text-right text-sm" />
                </td>
              </tr>
              <tr v-if="!outstandingRows.length">
                <td colspan="4" class="px-2 py-8 text-center text-sm text-slate-400">Select a party to fetch outstanding invoices.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Payment Workflow</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Use Receive for customers and Pay for suppliers.</li>
        <li>Allocation rows map directly to Payment Entry Reference child table.</li>
        <li>Submit payment to update invoice outstanding and ledger impact.</li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench, formatMoney } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const route = useRoute()
const router = useRouter()
const companies = ref([])
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const entries = ref([])
const options = ref({ mode_of_payments: [], bank_accounts: [], customers: [], suppliers: [] })
const outstandingRows = ref([])
const error = ref('')
const currency = ref('USD')

const form = ref({
  payment_type: 'Receive',
  posting_date: new Date().toISOString().slice(0, 10),
  party: '',
  mode_of_payment: '',
  bank_account: '',
  amount: 0,
})

const partyType = computed(() => (form.value.payment_type === 'Receive' ? 'Customer' : 'Supplier'))
const partyOptions = computed(() =>
  partyType.value === 'Customer' ? options.value.customers || [] : options.value.suppliers || []
)
const allocatedTotal = computed(() =>
  outstandingRows.value.reduce((acc, row) => acc + Number(row.allocated_amount || 0), 0)
)
const pendingCount = computed(() =>
  entries.value.filter((row) => String(row.status || '').toLowerCase().includes('draft')).length
)
const kpis = computed(() => [
  { id: 'payments', label: 'Payments', icon: '¤', value: entries.value.length, subtitle: 'Entries in range' },
  { id: 'draft', label: 'Draft/Pending', icon: '✎', value: pendingCount.value, subtitle: 'Need review' },
  { id: 'allocation', label: 'Allocated', icon: '▦', value: formatMoney(allocatedTotal.value, currency.value), subtitle: 'Current allocation' },
  { id: 'party', label: 'Party', icon: '◉', value: form.value.party || 'Not selected', subtitle: 'Current party' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Current company' },
])

function autoAllocate() {
  let remaining = Number(form.value.amount || 0)
  outstandingRows.value = outstandingRows.value.map((row) => {
    const maxAlloc = Number(row.outstanding_amount || 0)
    const allocated = Math.max(0, Math.min(maxAlloc, remaining))
    remaining -= allocated
    return { ...row, allocated_amount: allocated }
  })
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

async function load() {
  if (!company.value) return
  error.value = ''
  try {
    const res = await callWorkbench('payment_workspace', {
      company: company.value,
      payment_type: form.value.payment_type,
      party_type: form.value.party ? partyType.value : undefined,
      party: form.value.party || undefined,
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      limit_page_length: 100,
    })
    entries.value = res.entries || []
    options.value = res.options || options.value
    currency.value = res.currency || currency.value
    outstandingRows.value = (res.outstanding || []).map((r) => ({ ...r, allocated_amount: 0 }))
    autoAllocate()
  } catch (e) {
    error.value = e.message || String(e)
  }
}

async function submitPayment() {
  error.value = ''
  try {
    const amount = Number(form.value.amount || 0)
    const allocations = outstandingRows.value
      .filter((r) => Number(r.allocated_amount || 0) > 0)
      .map((r) => ({
        voucher_type: r.voucher_type,
        voucher_no: r.voucher_no,
        allocated_amount: Number(r.allocated_amount || 0),
      }))

    await callWorkbench('create_payment_with_allocation', {
      data: JSON.stringify({
        payment_type: form.value.payment_type,
        company: company.value,
        posting_date: form.value.posting_date,
        mode_of_payment: form.value.mode_of_payment,
        party_type: partyType.value,
        party: form.value.party,
        bank_account: form.value.bank_account,
        paid_amount: form.value.payment_type === 'Pay' ? amount : amount,
        received_amount: form.value.payment_type === 'Receive' ? amount : amount,
        allocations,
      }),
    })
    form.value.amount = 0
    await load()
  } catch (e) {
    error.value = e.message || String(e)
  }
}

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  if (route.query?.type === 'Pay' || route.query?.type === 'Receive') {
    form.value.payment_type = String(route.query.type)
  }
  if (route.query?.party) {
    form.value.party = String(route.query.party)
  }
  await loadCompanies()
  await load()
})

watch([company, fromDate, toDate, () => form.value.payment_type, () => form.value.party], load)

function goBank() {
  router.push({ name: 'bank' })
}

function onCompanyChange(v) { company.value = v }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }
</script>
