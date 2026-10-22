// Traduce la respuesta del backend (ClusteringResult) a la forma que usan las vistas.
import { formatCLP, formatDecimal } from '../lib/format.js'

const PALETTE = ['#3538cd', '#0e9384', '#e04f2f', '#ca8504', '#dd2590', '#7a5af8', '#1570ef', '#4e5ba6']

export const clusterColor = (index) => PALETTE[index % PALETTE.length]

function representative(summary) {
  const rep = summary.representative
  if (!rep) return null
  const f = rep.features ?? {}
  const facts = [
    f.frequency != null && `${formatDecimal(f.frequency)} compras`,
    f.monetary != null && `gasto ${formatCLP(f.monetary)}`,
    f.recency_days != null && `última compra hace ${Math.round(f.recency_days)} días`,
    f.comuna,
  ].filter(Boolean)
  return {
    name: rep.name ?? `Cliente ${rep.customer_id}`,
    customerId: rep.customer_id,
    facts: facts.join(' · '),
    profile: summary.label.persona,
  }
}

export function toUiCluster(summary, index, points) {
  const { profile, label } = summary
  const perYear = profile.metrics?.purchases_per_year
  const topProducts = profile.top_products?.length
    ? profile.top_products.map((p) => p.name)
    : Object.keys(profile.categorical?.top_category ?? {})
  return {
    id: String(profile.cluster_id),
    clusterId: profile.cluster_id,
    name: label.name,
    color: clusterColor(index),
    characterization: label.tags ?? [],
    description: label.description,
    traits: label.key_traits ?? [],
    customers: profile.size,
    share: profile.share,
    revenueShare: profile.revenue_share,
    avgSpend: profile.metrics?.avg_spend,
    avgTicket: profile.metrics?.avg_ticket,
    frequencyPerYear: perYear,
    frequency: perYear != null ? `${formatDecimal(perYear)} compras al año` : '—',
    daysSinceLastPurchase: profile.metrics?.days_since_last_purchase,
    topProducts,
    representativeCustomer: representative(summary),
    suggestedObjective: label.suggested_objective,
    strategies: label.strategies ?? [],
    suggestedQuestions: label.suggested_questions ?? [],
    rules: summary.rules?.map((r) => r.text) ?? [],
    points,
  }
}

export function toUiSegmentation(result) {
  const pointsByCluster = {}
  for (const p of result.scatter.points) {
    ;(pointsByCluster[p.cluster_id] ??= []).push({ x: p.x, y: p.y })
  }
  return {
    clusteringId: result.clustering_id,
    dataset: {
      fileName: result.filename,
      totalCustomers: result.n_customers,
      totalSales: result.total_revenue,
      clusterCount: result.k,
    },
    scatter: { xLabel: result.scatter.x_label, yLabel: result.scatter.y_label },
    clusters: result.clusters.map((summary, index) =>
      toUiCluster(summary, index, pointsByCluster[summary.profile.cluster_id] ?? []),
    ),
  }
}
