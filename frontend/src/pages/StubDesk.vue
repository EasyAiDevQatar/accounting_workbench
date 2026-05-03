<template>
  <div class="flex flex-1 flex-col bg-slate-50">
    <header class="border-b border-slate-200 bg-white px-8 py-6">
      <p class="text-xs font-semibold uppercase tracking-wide text-blue-600">
        Accounting Workbench
      </p>
      <h1 class="mt-1 text-2xl font-bold text-slate-900">{{ title }}</h1>
      <p class="mt-2 max-w-2xl text-sm text-slate-600">{{ subtitle }}</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button variant="solid" @click="openDesk"> Open in Desk </Button>
        <Button @click="$router.push('/')"> Back to dashboard </Button>
      </div>
    </header>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'

const props = defineProps({
  title: String,
  subtitle: String,
  deskRoute: String,
})

function openDesk() {
  window.location.href = `${window.location.origin}${props.deskRoute || '/app'}`
}
</script>
