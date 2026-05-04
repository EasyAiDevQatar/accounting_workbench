<template>
  <div class="flex min-h-0 flex-1 flex-col bg-[#f4f6fb]">
    <header class="border-b border-slate-200/80 bg-white px-8 py-6 shadow-sm">
      <div class="flex flex-wrap items-start gap-6">
        <div class="min-w-[200px] flex-1">
          <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">Accounting Workspace</p>
          <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-900">{{ title }}</h1>
          <p class="mt-1 max-w-xl text-sm leading-relaxed text-slate-600">{{ subtitle }}</p>
        </div>
        <div class="flex flex-1 justify-center">
          <div class="relative w-full max-w-md">
            <span class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">⌕</span>
            <input
              v-model="headerSearch"
              type="search"
              placeholder="Search accounts, transactions, reports…"
              class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-24 text-sm outline-none ring-blue-500/30 transition focus:border-blue-400 focus:bg-white focus:ring-4"
            />
            <kbd
              class="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-medium text-slate-500 sm:inline-block"
              >Ctrl K</kbd
            >
          </div>
        </div>
        <div class="flex flex-shrink-0 items-center gap-4">
          <span
            class="relative inline-flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-lg text-slate-600 ring-1 ring-slate-200/80"
          >
            🔔
            <span
              v-if="bellCount > 0"
              class="absolute -right-0.5 -top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
              >{{ bellCount > 99 ? '99+' : bellCount }}</span
            >
          </span>
          <span
            class="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-sm font-bold text-white shadow-md ring-2 ring-white"
            >AW</span
          >
        </div>
      </div>
      <div class="mt-6 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-5">
        <div
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
        >
          <span class="text-base text-slate-500">📅</span>
          <input
            :value="fromDate"
            type="date"
            class="rounded-lg border-0 bg-transparent text-sm outline-none"
            @input="$emit('update:fromDate', $event.target.value)"
          />
          <span class="text-slate-400">–</span>
          <input
            :value="toDate"
            type="date"
            class="rounded-lg border-0 bg-transparent text-sm outline-none"
            @input="$emit('update:toDate', $event.target.value)"
          />
        </div>
        <div
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm"
        >
          <span class="text-base text-slate-500">🏢</span>
          <select
            :value="company"
            class="max-w-[16rem] border-0 bg-transparent text-sm font-medium outline-none"
            @change="$emit('update:company', $event.target.value)"
          >
            <option v-for="c in companies" :key="c.name" :value="c.name">{{ c.name }}</option>
          </select>
        </div>
        <slot name="headerControls" />
        <div class="ml-auto text-xs text-slate-500">{{ periodLabel }}</div>
      </div>
    </header>

    <div class="flex min-h-0 flex-1">
      <div class="min-w-0 flex-1 overflow-y-auto px-8 py-6">
        <section class="flex flex-wrap items-center gap-2">
          <slot name="actions" />
        </section>

        <section v-if="error" class="mt-5 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {{ error }}
        </section>

        <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <div
            v-for="card in kpis"
            :key="card.id"
            class="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_8px_30px_rgba(15,23,42,0.06)]"
          >
            <div class="flex items-start justify-between gap-2">
              <span class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{{ card.label }}</span>
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-lg bg-slate-100 text-slate-600">
                {{ card.icon || '◆' }}
              </span>
            </div>
            <div class="mt-3 flex items-end justify-between gap-2">
              <span class="text-[22px] font-bold tabular-nums leading-none text-slate-900">{{ card.value }}</span>
              <span
                v-if="card.delta != null"
                class="shrink-0 text-xs font-bold tabular-nums"
                :class="card.delta >= 0 ? 'text-emerald-600' : 'text-rose-600'"
              >
                {{ card.delta >= 0 ? '+' : '' }}{{ card.delta }}%
              </span>
            </div>
            <p class="mt-2 text-[11px] text-slate-500">{{ card.subtitle || '' }}</p>
          </div>
        </section>

        <section class="mt-6 rounded-2xl border border-slate-200/80 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
          <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 px-5 py-4">
            <slot name="filters" />
          </div>
          <div class="overflow-x-auto px-2 pb-2">
            <slot name="table" />
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-xs text-slate-600">
            <slot name="footer" />
          </div>
        </section>

        <slot name="afterTable" />
      </div>

      <aside
        class="hidden w-[300px] shrink-0 overflow-y-auto border-l border-slate-200/80 bg-white px-5 py-6 shadow-[inset_1px_0_0_rgba(148,163,184,0.15)] lg:block xl:w-[320px]"
      >
        <slot name="rightRail" />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  companies: { type: Array, default: () => [] },
  company: { type: String, default: '' },
  fromDate: { type: String, default: '' },
  toDate: { type: String, default: '' },
  kpis: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  bellCount: { type: Number, default: 0 },
})

defineEmits(['update:company', 'update:fromDate', 'update:toDate'])

const headerSearch = ref('')
const months = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')
const periodLabel = computed(() => {
  if (!props.fromDate || !props.toDate) return ''
  const a = new Date(`${props.fromDate}T12:00:00`)
  const b = new Date(`${props.toDate}T12:00:00`)
  return `${months[a.getMonth()]} ${a.getDate()} - ${months[b.getMonth()]} ${b.getDate()}, ${b.getFullYear()}`
})
</script>
