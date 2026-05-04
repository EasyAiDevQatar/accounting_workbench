<template>
  <JournalLikeShell
    :title="`Create ${title}`"
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
        class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        @click="goBack"
      >
        Back To List
      </button>
      <button
        type="button"
        class="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700"
        @click="saveDoc"
      >
        Save Draft
      </button>
      <button
        type="button"
        class="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-emerald-600/25 transition hover:bg-emerald-700"
        @click="submitDoc"
      >
        Save And Submit
      </button>
    </template>

    <template #filters>
      <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">Required Fields</span>
    </template>

    <template #table>
      <div class="grid gap-4 p-4 md:grid-cols-2">
        <div v-for="field in requiredFields" :key="field.fieldname">
          <label class="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ field.label }}
          </label>
          <input
            v-if="isTextLike(field)"
            v-model="doc[field.fieldname]"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          />
          <input
            v-else-if="field.fieldtype === 'Date'"
            v-model="doc[field.fieldname]"
            type="date"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          />
          <input
            v-else-if="isNumeric(field)"
            v-model.number="doc[field.fieldname]"
            type="number"
            step="0.01"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          />
          <select
            v-else-if="field.fieldtype === 'Link' || field.fieldtype === 'Select'"
            v-model="doc[field.fieldname]"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          >
            <option value="">Select {{ field.label }}</option>
            <option
              v-for="option in field.options_list || selectOptions(field)"
              :key="option.name || option"
              :value="option.name || option"
            >
              {{ option.name || option }}
            </option>
          </select>
          <input
            v-else-if="field.fieldtype === 'Check'"
            v-model="doc[field.fieldname]"
            type="checkbox"
            class="h-4 w-4 rounded border-slate-300"
          />
          <input
            v-else
            v-model="doc[field.fieldname]"
            type="text"
            class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div v-for="table in childTables" :key="table.fieldname" class="border-t border-slate-100 p-4">
        <div class="mb-2 flex items-center justify-between">
          <h4 class="text-sm font-semibold text-slate-900">{{ table.label }}</h4>
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            @click="addChildRow(table.fieldname, table.fields)"
          >
            + Add Row
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[840px] text-sm">
            <thead class="text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th v-for="field in table.fields" :key="field.fieldname" class="px-2 py-2">{{ field.label }}</th>
                <th class="px-2 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, rowIndex) in (doc[table.fieldname] || [])"
                :key="`${table.fieldname}-${rowIndex}`"
                class="border-t border-slate-100"
              >
                <td v-for="field in table.fields" :key="`${rowIndex}-${field.fieldname}`" class="px-2 py-2">
                  <input
                    v-if="isTextLike(field)"
                    v-model="row[field.fieldname]"
                    type="text"
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                  />
                  <input
                    v-else-if="field.fieldtype === 'Date'"
                    v-model="row[field.fieldname]"
                    type="date"
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                  />
                  <input
                    v-else-if="isNumeric(field)"
                    v-model.number="row[field.fieldname]"
                    type="number"
                    step="0.01"
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                  />
                  <select
                    v-else-if="field.fieldtype === 'Link' || field.fieldtype === 'Select'"
                    v-model="row[field.fieldname]"
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                  >
                    <option value="">Select</option>
                    <option
                      v-for="option in field.options_list || selectOptions(field)"
                      :key="option.name || option"
                      :value="option.name || option"
                    >
                      {{ option.name || option }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="row[field.fieldname]"
                    type="text"
                    class="w-full rounded-lg border border-slate-200 px-2 py-1.5 text-sm"
                  />
                </td>
                <td class="px-2 py-2 text-right">
                  <button
                    type="button"
                    class="text-xs font-semibold text-red-600 hover:underline"
                    @click="removeChildRow(table.fieldname, rowIndex)"
                  >
                    Remove
                  </button>
                </td>
              </tr>
              <tr v-if="!(doc[table.fieldname] || []).length">
                <td :colspan="table.fields.length + 1" class="px-2 py-6 text-center text-xs text-slate-400">
                  No rows yet.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <template #footer>
      <span>Required fields are generated from doctype metadata.</span>
      <span class="font-medium text-slate-700">Status: {{ statusMessage }}</span>
    </template>

    <template #rightRail>
      <h3 class="text-sm font-bold text-slate-900">Create Flow</h3>
      <ul class="mt-3 space-y-2 text-xs text-slate-600">
        <li>Fill required parent fields first.</li>
        <li>Add child rows for required table fields.</li>
        <li>Use Save Draft for review, Save And Submit for posting workflow.</li>
      </ul>
    </template>
  </JournalLikeShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { frappeRequest } from 'frappe-ui'
import JournalLikeShell from '@/components/workbench/JournalLikeShell.vue'
import { callWorkbench } from '@/utils/workbenchApi'
import { currentMonthBounds } from '@/utils/dateRange'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  doctype: { type: String, required: true },
  listRouteName: { type: String, required: true },
})

const router = useRouter()
const companies = ref([])
const company = ref('')
const fromDate = ref('')
const toDate = ref('')
const requiredFields = ref([])
const childTables = ref([])
const doc = ref({})
const error = ref('')
const statusMessage = ref('Ready')

const kpis = computed(() => [
  { id: 'doctype', label: 'Doctype', icon: '◉', value: props.doctype, subtitle: 'Target document' },
  { id: 'fields', label: 'Required Fields', icon: '▦', value: requiredFields.value.length, subtitle: 'Parent required fields' },
  { id: 'tables', label: 'Child Tables', icon: '▤', value: childTables.value.length, subtitle: 'Required child sections' },
  { id: 'company', label: 'Company', icon: '🏢', value: company.value || '—', subtitle: 'Context company' },
  { id: 'state', label: 'State', icon: '⚙', value: statusMessage.value, subtitle: 'Current action state' },
])

function goBack() {
  router.push({ name: props.listRouteName })
}

function isNumeric(field) {
  return ['Int', 'Float', 'Currency', 'Percent'].includes(field.fieldtype)
}

function isTextLike(field) {
  return ['Data', 'Small Text', 'Text', 'Long Text'].includes(field.fieldtype)
}

function selectOptions(field) {
  if (field.fieldtype === 'Select') {
    return String(field.options || '')
      .split('\n')
      .map((x) => x.trim())
      .filter(Boolean)
  }
  return []
}

function normalizeDefaultValue(value) {
  if (value == null) return ''
  if (typeof value !== 'string') return value
  const raw = value.trim()
  // Ignore unresolved dynamic placeholders like ":Company".
  if (raw.startsWith(':')) return ''
  return raw
}

function addChildRow(fieldname, fields) {
  if (!Array.isArray(doc.value[fieldname])) doc.value[fieldname] = []
  const row = {}
  for (const field of fields) {
    row[field.fieldname] = normalizeDefaultValue(field.default)
  }
  doc.value[fieldname].push(row)
}

function removeChildRow(fieldname, index) {
  doc.value[fieldname].splice(index, 1)
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
  error.value = ''
  try {
    const res = await callWorkbench('doctype_required_meta', {
      doctype: props.doctype,
      company: company.value || undefined,
    })
    requiredFields.value = res.required_fields || []
    childTables.value = res.required_child_tables || []

    const next = {}
    for (const field of requiredFields.value) {
      next[field.fieldname] = normalizeDefaultValue(field.default)
    }
    if (props.doctype !== 'Company' && requiredFields.value.some((f) => f.fieldname === 'company')) {
      next.company = company.value || next.company || ''
    }
    for (const table of childTables.value) {
      next[table.fieldname] = []
    }
    doc.value = next
  } catch (e) {
    error.value = e.message || String(e)
  }
}

async function saveDoc() {
  error.value = ''
  statusMessage.value = 'Saving'
  try {
    const res = await callWorkbench('save_doctype_doc', {
      doctype: props.doctype,
      payload: JSON.stringify(doc.value),
    })
    statusMessage.value = `Saved ${res.name}`
  } catch (e) {
    error.value = e.message || String(e)
    statusMessage.value = 'Save Failed'
  }
}

async function submitDoc() {
  error.value = ''
  statusMessage.value = 'Submitting'
  try {
    const res = await callWorkbench('submit_doctype_doc', {
      doctype: props.doctype,
      payload: JSON.stringify(doc.value),
    })
    statusMessage.value = `Submitted ${res.name}`
    goBack()
  } catch (e) {
    error.value = e.message || String(e)
    statusMessage.value = 'Submit Failed'
  }
}

function onCompanyChange(v) { company.value = v; loadMeta() }
function onFromDateChange(v) { fromDate.value = v }
function onToDateChange(v) { toDate.value = v }

onMounted(async () => {
  const range = currentMonthBounds()
  fromDate.value = range.from
  toDate.value = range.to
  await loadCompanies()
  await loadMeta()
})
</script>
