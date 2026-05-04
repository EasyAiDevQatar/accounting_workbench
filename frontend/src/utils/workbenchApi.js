import { frappeRequest } from 'frappe-ui'

export async function callWorkbench(method, params = {}) {
  return frappeRequest({
    url: `/api/method/accounting_workbench.api.${method}`,
    method: 'POST',
    params,
  })
}

export function formatMoney(value, currency = 'USD') {
  const num = Number(value || 0)
  if (!Number.isFinite(num)) return String(value ?? '')
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num)
  } catch {
    return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }
}
