/**
 * Frappe session auth for the standalone SPA (same users as ERPNext).
 */

let csrfPromise = null

export async function fetchAuthUser() {
  try {
    const res = await fetch('/api/method/accounting_workbench.api.auth_status', {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    const data = await res.json()
    if (!res.ok) return 'Guest'
    return data.message ?? 'Guest'
  } catch {
    return 'Guest'
  }
}

export async function loginWithPassword(usr, pwd) {
  const body = new URLSearchParams()
  body.set('cmd', 'login')
  body.set('usr', (usr || '').trim())
  body.set('pwd', pwd || '')

  const res = await fetch('/login', {
    method: 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  })

  let data = {}
  try {
    data = await res.json()
  } catch {
    throw new Error('Invalid response from server')
  }

  const msg = data.message
  const okMessages = ['Logged In', 'No App']
  if (res.ok && okMessages.includes(msg)) {
    return true
  }

  let err = 'Login failed'
  if (data._server_messages) {
    try {
      const parts = JSON.parse(data._server_messages || '[]')
      const texts = parts.map((p) => {
        try {
          return JSON.parse(p).message
        } catch {
          return p
        }
      })
      if (texts.length) err = texts.join(' ')
    } catch {
      /* ignore */
    }
  } else if (data.exc_type) {
    err = data.exc_type
  }

  throw new Error(err)
}

export async function ensureCsrfToken() {
  if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') return
  if (window.frappe?.csrf_token) {
    window.csrf_token = window.frappe.csrf_token
    return
  }
  if (csrfPromise) return csrfPromise
  csrfPromise = fetch('/api/method/accounting_workbench.api.session_bootstrap', {
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })
    .then(async (res) => {
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data.exc_type || data._error_message || 'Session bootstrap failed')
      }
      const token = data.message?.csrf_token
      if (token) window.csrf_token = token
    })
    .finally(() => {
      csrfPromise = null
    })
  return csrfPromise
}

export async function logoutSession() {
  try {
    await ensureCsrfToken()
  } catch {
    /* Guest or bootstrap failed */
  }
  try {
    await fetch('/api/method/logout', {
      method: 'POST',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...(window.csrf_token ? { 'X-Frappe-CSRF-Token': window.csrf_token } : {}),
      },
      body: '{}',
    })
  } finally {
    window.csrf_token = ''
  }
}
