<template>
  <div class="w-full">
    <!-- Fixed height: Chart.js + maintainAspectRatio:false inside a stretching grid row causes runaway layout -->
    <div class="relative h-[220px] w-full overflow-hidden">
      <Line v-if="hasData" :data="chartData" :options="chartOptions" />
      <p v-else class="flex h-full items-center justify-center text-center text-xs text-slate-400">
        No cash movement in range.
      </p>
    </div>
    <div class="mt-2 flex justify-center gap-4 text-[11px] text-slate-600">
      <span class="inline-flex items-center gap-1.5"
        ><i class="inline-block h-2 w-4 rounded-sm bg-emerald-500" /> Cash In</span
      >
      <span class="inline-flex items-center gap-1.5"
        ><i class="inline-block h-2 w-4 rounded-sm bg-rose-500" /> Cash Out</span
      >
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  inflow: { type: Array, default: () => [] },
  outflow: { type: Array, default: () => [] },
  currency: { type: String, default: 'USD' },
})

function shortLabel(raw) {
  const s = String(raw || '')
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[2]}/${m[3]}`
  return s.length > 8 ? s.slice(5, 10) : s
}

function fmtMoney(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '—'
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: props.currency || 'USD',
      maximumFractionDigits: 0,
    }).format(n)
  } catch {
    return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
  }
}

const hasData = computed(() => (props.labels?.length || 0) > 0)

const chartData = computed(() => {
  const labels = (props.labels || []).map(shortLabel)
  const ins = (props.inflow || []).map((x) => Number(x) || 0)
  const outs = (props.outflow || []).map((x) => Number(x) || 0)
  return {
    labels,
    datasets: [
      {
        label: 'Cash In',
        data: ins,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34, 197, 94, 0.12)',
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
      {
        label: 'Cash Out',
        data: outs,
        borderColor: '#ef4444',
        backgroundColor: 'rgba(239, 68, 68, 0.06)',
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
    ],
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        title(items) {
          const i = items[0]?.dataIndex
          const full = props.labels?.[i]
          return full != null ? String(full) : ''
        },
        label(ctx) {
          const v = ctx.parsed?.y
          return `${ctx.dataset.label}: ${fmtMoney(v)}`
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { maxRotation: 0, font: { size: 10 }, color: '#94a3b8' },
    },
    y: {
      grid: { color: 'rgba(226, 232, 240, 0.9)' },
      ticks: {
        font: { size: 10 },
        color: '#94a3b8',
        callback(value) {
          return fmtMoney(value)
        },
      },
    },
  },
}))
</script>
