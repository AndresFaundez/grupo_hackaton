const clp = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

const number = new Intl.NumberFormat('es-CL')

export const formatCLP = (value) => clp.format(value)
export const formatNumber = (value) => number.format(value)
export const formatPercent = (value) => `${Math.round(value * 100)}%`
