import { Link } from 'react-router-dom'
import { clusters, dataset } from '../data/demoClusters.js'
import { formatCLP, formatNumber, formatPercent } from '../lib/format.js'
import { useClusterNames } from '../context/ClusterNames.jsx'
import EditableName from '../components/EditableName.jsx'
import Scatter from '../components/Scatter.jsx'

export default function Clusters() {
  const { names, rename } = useClusterNames()

  return (
    <section>
      <h2>Tus clusters</h2>
      <p className="cluster-summary">
        <strong>{dataset.clusterCount}</strong> grupos encontrados en{' '}
        <strong>{formatNumber(dataset.totalCustomers)}</strong> clientes ·{' '}
        {dataset.fileName}
      </p>
      <p className="muted small">
        Nombres propuestos por la IA según las métricas · editables
      </p>

      <div className="card scatter-card">
        <Scatter />
      </div>

      <div className="cluster-grid">
        {clusters.map((cluster) => (
          <article className="card cluster-card" key={cluster.id}>
            <div className="cluster-head">
              <span className="cluster-dot" style={{ background: cluster.color }} aria-hidden="true" />
              <EditableName name={names[cluster.id]} onRename={(name) => rename(cluster.id, name)} />
            </div>
            <p className="cluster-desc">{cluster.description}</p>
            <p className="cluster-size">
              {formatNumber(cluster.customers)} clientes ·{' '}
              {formatPercent(cluster.share)} de la base
            </p>
            <div className="cluster-stats">
              <div>
                <span className="stat-label">Gasto promedio</span>
                <span className="stat-value">{formatCLP(cluster.avgSpend)}</span>
              </div>
              <div>
                <span className="stat-label">Frecuencia</span>
                <span className="stat-value">{cluster.frequency}</span>
              </div>
            </div>
            <Link className="link-button strong" to={`/explorar?segmento=${cluster.id}`}>
              Explorar segmento →
            </Link>
          </article>
        ))}
      </div>
    </section>
  )
}
