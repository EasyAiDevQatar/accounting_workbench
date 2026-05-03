<template>
  <div class="flex min-h-screen bg-[#f4f6fb] text-slate-900 antialiased">
    <aside
      class="flex w-60 flex-col border-r border-slate-200/80 bg-white shadow-[4px_0_24px_rgba(15,23,42,0.04)]"
    >
      <div class="border-b border-slate-100 px-5 py-5">
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="text-[11px] font-bold uppercase tracking-[0.14em] text-blue-600">
              Accounting
            </div>
            <div class="mt-1 text-xl font-bold tracking-tight text-slate-900">Workspace</div>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-lg px-2 py-1 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-800"
            @click="logout"
          >
            Sign out
          </button>
        </div>
      </div>
      <nav class="flex flex-1 flex-col gap-0.5 overflow-y-auto px-3 py-4">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
          active-class="!bg-blue-50 !text-blue-700 !shadow-sm ring-1 ring-blue-100"
        >
          <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-[15px]">
            {{ item.icon }}
          </span>
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="mx-3 mb-4 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-white p-4 shadow-sm">
        <div class="text-2xl" aria-hidden="true">🚀</div>
        <div class="mt-2 text-sm font-semibold text-slate-900">Work smarter</div>
        <p class="mt-1 text-xs leading-relaxed text-slate-600">
          {{ clicksSaved }} clicks saved since yesterday.
        </p>
      </div>
    </aside>
    <div class="flex min-h-screen min-w-0 flex-1 flex-col">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { logoutSession } from '@/auth'

const router = useRouter()
const clicksSaved = ref(3)

async function logout() {
  await logoutSession()
  router.push({ name: 'login' })
}

const nav = [
  { to: { name: 'dashboard' }, label: 'Dashboard', icon: '◉' },
  { to: { name: 'journal' }, label: 'Journal Entries', icon: '≡' },
  { to: { name: 'invoices' }, label: 'Invoices', icon: '▤' },
  { to: { name: 'bills' }, label: 'Bills', icon: '▥' },
  { to: { name: 'payments' }, label: 'Payments', icon: '¤' },
  { to: { name: 'bank' }, label: 'Bank Reconciliation', icon: '⌁' },
  { to: { name: 'coa' }, label: 'Chart of Accounts', icon: '▦' },
  { to: { name: 'budget' }, label: 'Budget', icon: '▧' },
  { to: { name: 'reports' }, label: 'Reports', icon: '▨' },
  { to: { name: 'period-close' }, label: 'Period Close', icon: '◷' },
  { to: { name: 'settings' }, label: 'Settings', icon: '⚙' },
]
</script>
