import { clusters, summary } from '../data/demoClusters.js'
import { formatCLP, formatNumber, formatPercent } from '../lib/format.js'

export default function Dashboard() {
  const bySales = [...clusters].sort((a, b) => b.sales - a.sales)

  return (
    <section>
      <h2>Dashboard</h2>
      <p className="lead">
        Los clusters más importantes detectados en la base de datos, con su
        caracterización.
      </p>

      <div className="kpis">
        <div className="card kpi">
          <span className="kpi-label">Clientes</span>
          <span className="kpi-value">{formatNumber(summary.totalCustomers)}</span>
        </div>
        <div className="card kpi">
          <span className="kpi-label">Ventas totales</span>
          <span className="kpi-value">{formatCLP(summary.totalSales)}</span>
        </div>
        <div className="card kpi">
          <span className="kpi-label">Clusters</span>
          <span className="kpi-value">{summary.clusterCount}</span>
        </div>
      </div>

      <div className="cluster-grid">
        {bySales.map((cluster) => {
          const share = cluster.sales / summary.totalSales
          return (
            <article className="card cluster-card" key={cluster.id}>
              <div className="cluster-head">
                <span
                  className="cluster-dot"
                  style={{ background: cluster.color }}
                  aria-hidden="true"
                />
                <h3>{cluster.name}</h3>
              </div>
              <div className="badges">
                {cluster.characterization.map((tag) => (
                  <span className="badge" key={tag}>{tag}</span>
                ))}
              </div>
              <p className="cluster-desc">{cluster.description}</p>
              <div className="cluster-stats">
                <div>
                  <span className="stat-label">Ventas</span>
                  <span className="stat-value">{formatCLP(cluster.sales)}</span>
                </div>
                <div>
                  <span className="stat-label">Participación</span>
                  <span className="stat-value">{formatPercent(share)}</span>
                </div>
                <div>
                  <span className="stat-label">Clientes</span>
                  <span className="stat-value">{formatNumber(cluster.customers)}</span>
                </div>
              </div>
              <div className="bar" aria-hidden="true">
                <span style={{ width: `${share * 100}%`, background: cluster.color }} />
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
