const clp = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

const number = new Intl.NumberFormat('es-CL')
const decimal = new Intl.NumberFormat('es-CL', { maximumFractionDigits: 1 })

export const formatCLP = (value) => (value == null ? '—' : clp.format(value))
export const formatNumber = (value) => (value == null ? '—' : number.format(value))
export const formatDecimal = (value) => (value == null ? '—' : decimal.format(value))
export const formatPercent = (value) => (value == null ? '—' : `${Math.round(value * 100)}%`)

// Montos grandes en lenguaje de negocio: "$177,8 millones".
export const formatMillions = (value) => {
  if (value == null) return '—'
  return value >= 1_000_000 ? `$${decimal.format(value / 1_000_000)} millones` : clp.format(value)
}

// "Cada cuántos días compra" a partir de compras al año.
export const daysBetweenPurchases = (perYear) => (perYear > 0 ? Math.round(365 / perYear) : null)
