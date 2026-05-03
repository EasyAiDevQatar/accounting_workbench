<template>
  <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
    <div class="relative mx-auto h-[200px] w-[200px] shrink-0 sm:mx-0">
      <Doughnut v-if="hasRows" :data="chartData" :options="chartOptions" />
      <div
        v-if="hasRows"
        class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pt-1"
      >
        <div class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Total</div>
        <div class="mt-0.5 text-lg font-bold tabular-nums text-slate-900">{{ centerLabel }}</div>
      </div>
      <div
        v-else
        class="flex h-full w-full items-center justify-center rounded-full bg-slate-100 text-xs text-slate-400"
      >
        No data
      </div>
    </div>
    <ul class="min-w-0 flex-1 space-y-2.5">
      <li
        v-for="(row, i) in rows"
        :key="row.name"
        class="flex items-center gap-2 text-sm"
      >
        <span
          class="h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-white"
          :style="{ backgroundColor: colors[i % colors.length] }"
        />
        <span class="flex-1 truncate text-slate-700">{{ row.name }}</span>
        <span class="shrink-0 font-semibold tabular-nums text-slate-900">{{ row.pct }}%</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  currency: { type: String, default: 'USD' },
  /** When set, replaces currency-formatted total in the center (e.g. journal entry counts). */
  centerText: { type: String, default: '' },
})

const colors = [
  '#2563eb',
  '#7c3aed',
  '#ea580c',
  '#0d9488',
  '#64748b',
  '#db2777',
  '#ca8a04',
  '#16a34a',
]

const hasRows = computed(() => (props.rows || []).length > 0)

const chartData = computed(() => {
  const list = props.rows || []
  const data = list.map((r) => Number(r.pct) || 0)
  const bg = list.map((_, i) => colors[i % colors.length])
  return {
    labels: list.map((r) => r.name),
    datasets: [
      {
        data,
        backgroundColor: bg,
        borderWidth: 2,
        borderColor: '#ffffff',
        hoverOffset: 6,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '66%',
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label(ctx) {
          const row = props.rows[ctx.dataIndex]
          const pct = row?.pct ?? ctx.parsed
          const val = row?.value
          if (val != null && Number(val)) {
            try {
              const m = new Intl.NumberFormat(undefined, {
                style: 'currency',
                currency: props.currency || 'USD',
                maximumFractionDigits: 0,
              }).format(Number(val))
              return `${ctx.label}: ${pct}% (${m})`
            } catch {
              /* fall through */
            }
          }
          return `${ctx.label}: ${pct}%`
        },
      },
    },
  },
}))

const totalMoney = computed(() => {
  const t = (props.rows || []).reduce((s, r) => s + Number(r.value || 0), 0)
  if (!t) return '—'
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: props.currency || 'USD',
      maximumFractionDigits: 0,
    }).format(t)
  } catch {
    return t.toLocaleString(undefined, { maximumFractionDigits: 0 })
  }
})

const centerLabel = computed(() =>
  props.centerText ? props.centerText : totalMoney.value,
)
</script>
