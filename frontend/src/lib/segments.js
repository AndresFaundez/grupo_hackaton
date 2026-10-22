// Cálculos de negocio sobre los segmentos ya adaptados (ver api/adapter.js).

// Ventas del segmento a partir de su participación en el total.
export const salesOf = (cluster, dataset) =>
  cluster.revenueShare != null && dataset?.totalSales != null
    ? cluster.revenueShare * dataset.totalSales
    : null

// El segmento cuya participación en ventas más supera su peso en clientes:
// es el dato que más le sirve a alguien de marketing en un vistazo.
export const standoutSegment = (clusters) => {
  const ranked = clusters.filter((c) => c.revenueShare != null && c.share > 0)
  if (!ranked.length) return null
  const best = ranked.reduce((a, b) => (b.revenueShare / b.share > a.revenueShare / a.share ? b : a))
  return best.revenueShare > best.share ? best : null
}
