<template>
  <teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-[100] flex items-start justify-center overflow-y-auto bg-slate-900/50 px-3 py-8 backdrop-blur-[1px]"
      role="dialog"
      aria-modal="true"
      @click.self="requestClose"
    >
      <div
        class="w-full max-w-4xl rounded-2xl border border-slate-200 bg-white shadow-2xl"
        @click.stop
      >
        <header class="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-4">
          <div>
            <h2 class="text-lg font-bold text-slate-900">{{ title }}</h2>
            <p v-if="doc?.name" class="mt-0.5 font-mono text-xs text-slate-500">{{ doc.name }}</p>
          </div>
          <button
            type="button"
            class="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close"
            @click="requestClose"
          >
            ✕
          </button>
        </header>

        <div v-if="loading" class="px-6 py-16 text-center text-sm text-slate-500">Loading…</div>

        <template v-else-if="doc">
          <div class="max-h-[70vh] overflow-y-auto px-6 py-4">
            <p v-if="modalError" class="mb-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {{ modalError }}
            </p>

            <div class="grid gap-4 sm:grid-cols-2">
              <label class="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Posting date
                <input
                  v-model="doc.posting_date"
                  type="date"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  :disabled="isPosted || viewOnly"
                />
              </label>
              <label class="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Entry type
                <select
                  v-model="doc.voucher_type"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  :disabled="isPosted || viewOnly"
                >
                  <option v-for="vt in meta?.voucher_types || []" :key="vt" :value="vt">{{ vt }}</option>
                </select>
              </label>
              <label class="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Series
                <select
                  v-model="doc.naming_series"
                  class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                  :disabled="!!doc.name || isPosted || viewOnly"
                >
                  <option v-for="ns in meta?.naming_series || []" :key="ns" :value="ns">{{ ns }}</option>
                </select>
              </label>
              <div class="flex items-end gap-2 text-sm">
                <span
                  class="rounded-full px-2.5 py-1 text-[11px] font-semibold"
                  :class="isPosted ? 'bg-emerald-50 text-emerald-800' : 'bg-sky-50 text-sky-800'"
                >
                  {{ isPosted ? 'Submitted' : 'Draft' }}
                </span>
                <span v-if="totals.debit || totals.credit" class="text-slate-500">
                  Δ {{ formatAmt(Math.abs(totals.debit - totals.credit)) }}
                  <span v-if="totals.balanced" class="text-emerald-600">· balanced</span>
                  <span v-else class="text-amber-600">· not balanced</span>
                </span>
              </div>
            </div>

            <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Remark
              <textarea
                v-model="doc.user_remark"
                rows="2"
                class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
                :disabled="isPosted || viewOnly"
              />
            </label>

            <div class="mt-6">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-sm font-bold text-slate-900">Accounts</h3>
                <button
                  v-if="!isPosted && !viewOnly"
                  type="button"
                  class="text-xs font-semibold text-blue-600 hover:underline"
                  @click="addRow"
                >
                  + Add row
                </button>
              </div>

              <div class="mt-2 overflow-x-auto rounded-xl border border-slate-200">
                <table class="w-full min-w-[640px] text-left text-xs">
                  <thead class="border-b border-slate-100 bg-slate-50 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    <tr>
                      <th class="px-3 py-2">Account</th>
                      <th class="w-28 px-3 py-2 text-right">Debit</th>
                      <th class="w-28 px-3 py-2 text-right">Credit</th>
                      <th class="w-10 px-2 py-2" />
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in doc.accounts || []" :key="rowKey(row, idx)" class="border-b border-slate-50">
                      <td class="relative px-3 py-2 align-top">
                        <input
                          v-model="row.account"
                          type="text"
                          placeholder="Search account…"
                          class="w-full rounded-lg border border-slate-200 px-2 py-1.5 font-mono text-[11px]"
                          :disabled="isPosted || viewOnly"
                          @focus="activeRow = idx"
                          @input="onAccountInput(idx)"
                        />
                        <ul
                          v-if="activeRow === idx && accountHits.length && !isPosted && !viewOnly"
                          class="absolute left-3 right-3 z-10 mt-1 max-h-48 overflow-auto rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
                        >
                          <li
                            v-for="h in accountHits"
                            :key="h.value"
                            class="cursor-pointer px-3 py-2 text-left text-[11px] hover:bg-blue-50"
                            @mousedown.prevent="pickAccount(idx, h.value)"
                          >
                            <span class="font-mono font-semibold text-slate-900">{{ h.value }}</span>
                            <span v-if="h.description || h.label" class="block text-slate-500">{{
                              h.description || h.label
                            }}</span>
                          </li>
                        </ul>
                      </td>
                      <td class="px-3 py-2 text-right">
                        <input
                          v-model.number="row.debit"
                          type="number"
                          step="0.01"
                          min="0"
                          class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-right font-mono tabular-nums"
                          :disabled="isPosted || viewOnly"
                          @focus="activeRow = -1"
                        />
                      </td>
                      <td class="px-3 py-2 text-right">
                        <input
                          v-model.number="row.credit"
                          type="number"
                          step="0.01"
                          min="0"
                          class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-right font-mono tabular-nums"
                          :disabled="isPosted || viewOnly"
                          @focus="activeRow = -1"
                        />
                      </td>
                      <td class="px-2 py-2 text-center">
                        <button
                          v-if="!isPosted && !viewOnly && (doc.accounts || []).length > 2"
                          type="button"
                          class="text-slate-400 hover:text-red-600"
                          title="Remove row"
                          @click="removeRow(idx)"
                        >
                          ×
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <footer class="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 px-6 py-4">
            <button
              type="button"
              class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="requestClose"
            >
              {{ viewOnly ? 'Close' : 'Cancel' }}
            </button>
            <button
              v-if="!viewOnly && !isPosted && doc.name"
              type="button"
              class="rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:opacity-40"
              :disabled="busy"
              @click="onDelete"
            >
              Delete
            </button>
            <button
              v-if="viewOnly && !isPosted && doc.name"
              type="button"
              class="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
              @click="emit('switch-edit')"
            >
              Edit
            </button>
            <button
              v-if="!viewOnly && !isPosted"
              type="button"
              class="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-900 disabled:opacity-40"
              :disabled="busy || !totals.balanced"
              :title="!totals.balanced ? 'Debits must equal credits' : ''"
              @click="onSave(false)"
            >
              Save draft
            </button>
            <button
              v-if="!viewOnly && !isPosted"
              type="button"
              class="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-40"
              :disabled="busy || !totals.balanced"
              :title="!totals.balanced ? 'Debits must equal credits' : ''"
              @click="onSave(true)"
            >
              Save &amp; submit
            </button>
          </footer>
        </template>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'
import { ensureCsrfToken } from '@/auth'
import { localISODate } from '@/utils/dateRange'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  company: { type: String, required: true },
  /** create | edit | view */
  mode: { type: String, default: 'create' },
  entryName: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue', 'close', 'saved', 'deleted', 'switch-edit'])

const loading = ref(false)
const busy = ref(false)
const modalError = ref('')
const meta = ref(null)
const doc = ref(null)
const activeRow = ref(-1)
const accountHits = ref([])
let searchTimer = null

const viewOnly = computed(() => props.mode === 'view')
const isPosted = computed(() => Number(doc.value?.docstatus) === 1)

const title = computed(() => {
  if (props.mode === 'create') return 'New Journal Entry'
  if (props.mode === 'view') return 'Journal Entry'
  return 'Edit Journal Entry'
})

const totals = computed(() => {
  let debit = 0
  let credit = 0
  for (const r of doc.value?.accounts || []) {
    debit += Number(r.debit) || 0
    credit += Number(r.credit) || 0
  }
  const balanced = Math.abs(debit - credit) < 0.0005
  return { debit, credit, balanced }
})

function rowKey(row, i) {
  return row.name || `new-${i}`
}

function formatAmt(n) {
  const cur = meta.value?.currency || 'USD'
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency: cur }).format(n)
  } catch {
    return n.toFixed(2)
  }
}

function requestClose() {
  emit('update:modelValue', false)
  emit('close')
}

async function loadMeta() {
  const res = await frappeRequest({
    url: '/api/method/accounting_workbench.api.journal_entry_form_meta',
    method: 'POST',
    params: { company: props.company },
  })
  meta.value = res
}

function blankRows() {
  return [
    { doctype: 'Journal Entry Account', account: '', debit: 0, credit: 0 },
    { doctype: 'Journal Entry Account', account: '', debit: 0, credit: 0 },
  ]
}

function resetNew() {
  const ns = meta.value?.naming_series?.[0] || 'ACC-JV-.YYYY.-'
  const vt = meta.value?.voucher_types?.[0] || 'Journal Entry'
  doc.value = {
    doctype: 'Journal Entry',
    company: props.company,
    posting_date: localISODate(new Date()),
    voucher_type: vt,
    naming_series: ns,
    user_remark: '',
    accounts: blankRows(),
  }
}

async function fetchExisting(name) {
  const d = await frappeRequest({
    url: '/api/method/frappe.client.get',
    method: 'POST',
    params: { doctype: 'Journal Entry', name },
  })
  doc.value = d
}

function stripNoise(o) {
  const out = JSON.parse(JSON.stringify(o))
  for (const k of Object.keys(out)) {
    if (k.startsWith('__')) delete out[k]
  }
  return out
}

function normalizeAccounts(accounts, keepChildNames) {
  return (accounts || [])
    .map((row, i) => {
      const r = {
        doctype: 'Journal Entry Account',
        idx: i + 1,
        account: (row.account || '').trim(),
        debit: Number(row.debit) || 0,
        credit: Number(row.credit) || 0,
      }
      if (keepChildNames && row.name) r.name = row.name
      return r
    })
    .filter((r) => r.account)
}

function docForWrite() {
  const d = stripNoise(doc.value)
  d.accounts = normalizeAccounts(d.accounts, !!d.name)
  return d
}

async function onSave(submitAfter) {
  modalError.value = ''
  busy.value = true
  try {
    await ensureCsrfToken()
    const rows = (doc.value.accounts || []).filter((r) => (r.account || '').trim())
    if (rows.length < 2) {
      modalError.value = 'Add at least two account lines.'
      return
    }
    if (!totals.value.balanced) {
      modalError.value = 'Total debit must equal total credit.'
      return
    }

    let payload = docForWrite()
    if (!payload.name) {
      const created = await frappeRequest({
        url: '/api/method/frappe.client.insert',
        method: 'POST',
        params: { doc: payload },
      })
      doc.value = created
      emit('saved', created)
    } else {
      const saved = await frappeRequest({
        url: '/api/method/frappe.client.save',
        method: 'POST',
        params: { doc: payload },
      })
      doc.value = saved
      emit('saved', saved)
    }

    if (submitAfter && doc.value.name) {
      await ensureCsrfToken()
      const submitted = await frappeRequest({
        url: '/api/method/frappe.client.submit',
        method: 'POST',
        params: { doc: docForWrite() },
      })
      doc.value = submitted
      emit('saved', submitted)
    }
    requestClose()
  } catch (e) {
    modalError.value = e.messages?.length ? e.messages.join(' ') : e.message || String(e)
  } finally {
    busy.value = false
  }
}

async function onDelete() {
  if (!doc.value?.name || isPosted.value) return
  if (!window.confirm(`Delete draft ${doc.value.name}?`)) return
  modalError.value = ''
  busy.value = true
  try {
    await ensureCsrfToken()
    await frappeRequest({
      url: '/api/method/frappe.client.delete',
      method: 'POST',
      params: { doctype: 'Journal Entry', name: doc.value.name },
    })
    emit('deleted', doc.value.name)
    requestClose()
  } catch (e) {
    modalError.value = e.messages?.length ? e.messages.join(' ') : e.message || String(e)
  } finally {
    busy.value = false
  }
}

function addRow() {
  doc.value.accounts = [...(doc.value.accounts || []), { doctype: 'Journal Entry Account', account: '', debit: 0, credit: 0 }]
}

function removeRow(i) {
  const next = [...(doc.value.accounts || [])]
  next.splice(i, 1)
  doc.value.accounts = next.length ? next : blankRows()
}

function onAccountInput(idx) {
  activeRow.value = idx
  const q = (doc.value.accounts[idx].account || '').trim()
  window.clearTimeout(searchTimer)
  if (!q) {
    accountHits.value = []
    return
  }
  searchTimer = window.setTimeout(() => searchAccounts(q), 280)
}

async function searchAccounts(txt) {
  try {
    const hits = await frappeRequest({
      url: '/api/method/frappe.desk.search.search_link',
      method: 'POST',
      params: {
        doctype: 'Account',
        txt,
        page_length: 15,
        filters: JSON.stringify({ company: props.company, is_group: 0, disabled: 0 }),
      },
    })
    accountHits.value = Array.isArray(hits) ? hits : []
  } catch {
    accountHits.value = []
  }
}

function pickAccount(idx, value) {
  doc.value.accounts[idx].account = value
  accountHits.value = []
  activeRow.value = -1
}

watch(
  () => [props.modelValue, props.mode, props.entryName, props.company],
  async ([open]) => {
    if (!open || !props.company) return
    modalError.value = ''
    accountHits.value = []
    activeRow.value = -1
    loading.value = true
    doc.value = null
    try {
      await loadMeta()
      if (props.mode === 'create') resetNew()
      else if (props.entryName) await fetchExisting(props.entryName)
    } catch (e) {
      modalError.value = e.message || String(e)
    } finally {
      loading.value = false
    }
  },
  { flush: 'post' },
)

watch(
  () => props.company,
  async (c) => {
    if (props.modelValue && c && props.mode === 'create' && doc.value && !doc.value.name) {
      doc.value.company = c
    }
  },
)
</script>
