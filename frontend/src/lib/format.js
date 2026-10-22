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
