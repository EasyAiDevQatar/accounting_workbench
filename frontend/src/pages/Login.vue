<template>
  <div class="flex min-h-screen flex-col bg-[#f4f6fb] text-slate-900 antialiased">
    <div class="flex flex-1 flex-col items-center justify-center px-4 py-12">
      <div class="w-full max-w-[420px] rounded-2xl border border-slate-200/80 bg-white p-8 shadow-[0_8px_30px_rgba(15,23,42,0.08)]">
        <div class="text-center">
          <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-blue-600">Accounting Workbench</p>
          <h1 class="mt-2 text-2xl font-bold tracking-tight">Sign in</h1>
          <p class="mt-1 text-sm text-slate-600">Use your ERPNext user email and password.</p>
        </div>

        <form class="mt-8 space-y-4" @submit.prevent="submit">
          <div>
            <label class="block text-xs font-semibold text-slate-600" for="wb-email">Email / Username</label>
            <input
              id="wb-email"
              v-model="usr"
              type="text"
              autocomplete="username"
              required
              class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none ring-blue-500/20 transition focus:border-blue-400 focus:bg-white focus:ring-4"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600" for="wb-password">Password</label>
            <input
              id="wb-password"
              v-model="pwd"
              type="password"
              autocomplete="current-password"
              required
              class="mt-1 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none ring-blue-500/20 transition focus:border-blue-400 focus:bg-white focus:ring-4"
            />
          </div>

          <p v-if="error" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{{ error }}</p>

          <button
            type="submit"
            :disabled="busy"
            class="w-full rounded-xl bg-blue-600 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition hover:bg-blue-700 disabled:opacity-60"
          >
            {{ busy ? 'Signing in…' : 'Sign in' }}
          </button>
        </form>

        <div class="mt-6 flex flex-col gap-2 border-t border-slate-100 pt-6 text-center text-sm">
          <button type="button" class="text-blue-600 hover:underline" @click="openForgot">
            Forgot password?
          </button>
          <a href="/app" class="text-slate-500 hover:text-slate-700 hover:underline">Open ERPNext Desk</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loginWithPassword, ensureCsrfToken } from '@/auth'

const route = useRoute()
const router = useRouter()

const usr = ref('')
const pwd = ref('')
const error = ref('')
const busy = ref(false)

function openForgot() {
  window.location.href = '/login#forgot'
}

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await loginWithPassword(usr.value, pwd.value)
    await ensureCsrfToken()
    let safe = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    if (!safe.startsWith('/') || safe.startsWith('//')) safe = '/'
    if (safe.startsWith('/login')) safe = '/'
    await router.replace(safe)
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    busy.value = false
  }
}
</script>
