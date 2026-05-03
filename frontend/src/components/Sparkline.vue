<template>
  <div class="sparkline-wrap h-10 w-full overflow-hidden">
    <Line v-if="showChart" :data="chartData" :options="chartOptions" />
    <div v-else class="h-full w-full rounded-lg bg-slate-50" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'

const props = defineProps({
  values: { type: Array, default: () => [] },
  /** Tailwind-style stroke e.g. emerald-600 → pass hex */
  color: { type: String, default: '#2563eb' },
})

const series = computed(() => (props.values || []).map(Number))

const showChart = computed(() => series.value.length > 1)

const chartData = computed(() => ({
  labels: series.value.map((_, i) => i),
  datasets: [
    {
      data: series.value,
      borderColor: props.color,
      backgroundColor: `${props.color}22`,
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 1.5,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { enabled: false },
  },
  scales: {
    x: { display: false },
    y: { display: false },
  },
  animation: { duration: 400 },
}))
</script>

<style scoped>
.sparkline-wrap {
  position: relative;
  min-height: 2.5rem;
}
</style>
