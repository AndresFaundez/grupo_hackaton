import { Link } from 'react-router-dom'
import {
  daysBetweenPurchases,
  formatCLP,
  formatDecimal,
  formatMillions,
  formatNumber,
  formatPercent,
} from '../lib/format.js'
import { salesOf, standoutSegment } from '../lib/segments.js'
import { useSegmentation } from '../context/Segmentation.jsx'
import EditableName from '../components/EditableName.jsx'
import NeedsData from '../components/NeedsData.jsx'
import Scatter from '../components/Scatter.jsx'
import Icon from '../components/Icon.jsx'

export default function Clusters() {
  return (
    <NeedsData>
      <ClusterList />
    </NeedsData>
  )
}

function ClusterList() {
  const { clusters, dataset, rename } = useSegmentation()
  const star = standoutSegment(clusters)

  return (
    <section className="segments-page">
      <header className="page-head">
        <span className="eyebrow">
          <Icon name="users" size={14} /> Resultados · {dataset.fileName}
        </span>
        <h1 className="display">
          Encontramos <em>{dataset.clusterCount} tipos</em> de clientes
        </h1>
        <p className="lead">
          Analizamos {formatNumber(dataset.totalCustomers)} clientes
          {dataset.totalSales != null && <> y {formatMillions(dataset.totalSales)} en ventas</>}, y
          los agrupamos según cómo compran. A cada grupo lo llamamos{' '}
          <strong>segmento</strong>: personas parecidas a las que les puedes
          hablar con el mismo mensaje.
        </p>
      </header>

      {star && (
        <aside className="insight">
          <span className="insight-icon" aria-hidden="true">
            <Icon name="bulb" size={20} />
          </span>
          <p>
            <span className="insight-kicker">Lo más importante</span>
            <strong>{star.name}</strong> son el <strong>{formatPercent(star.share)}</strong> de
            tus clientes, pero generan el <strong>{formatPercent(star.revenueShare)}</strong> de
            tus ventas. Cuidarlos es prioridad.
          </p>
          <Link className="secondary" to={`/explorar?segmento=${star.id}`}>
            Ver este segmento
          </Link>
        </aside>
      )}

      <div className="segments-layout">
        <div className="cluster-grid">
          {clusters.map((cluster) => {
            const days = daysBetweenPurchases(cluster.frequencyPerYear)
            return (
              <article className="card cluster-card" key={cluster.id} style={{ '--seg': cluster.color }}>
                <div className="cluster-head">
                  <span className="cluster-swatch" aria-hidden="true" />
                  <EditableName name={cluster.name} onRename={(name) => rename(cluster.id, name)} />
                </div>
                <p className="cluster-desc">{cluster.description}</p>

                <div className="share-row">
                  <div className="share-label">
                    <span>{formatNumber(cluster.customers)} clientes</span>
                    <span className="muted">{formatPercent(cluster.share)} del total</span>
                  </div>
                  <div className="bar" aria-hidden="true">
                    <span style={{ width: `${(cluster.share ?? 0) * 100}%` }} />
                  </div>
                </div>

                <dl className="mini-stats">
                  <div>
                    <dt>Ventas</dt>
                    <dd>{formatMillions(salesOf(cluster, dataset))}</dd>
                    <dd className="muted small">{formatPercent(cluster.revenueShare)} del total</dd>
                  </div>
                  <div>
                    <dt>Gasto por cliente</dt>
                    <dd>{formatCLP(cluster.avgSpend)}</dd>
                    <dd className="muted small">promedio</dd>
                  </div>
                  <div>
                    <dt>Compra cada</dt>
                    <dd>{days != null ? `~${days} días` : '—'}</dd>
                    <dd className="muted small">{formatDecimal(cluster.frequencyPerYear)} al año</dd>
                  </div>
                </dl>

                <Link className="card-cta" to={`/explorar?segmento=${cluster.id}`}>
                  Conocer a este grupo <Icon name="arrowRight" size={16} />
                </Link>
              </article>
            )
          })}
        </div>

        <div className="card map-card">
          <h2 className="card-title">
            <Icon name="map" size={18} /> Mapa de tus clientes
          </h2>
          <p className="muted small map-help">
            Cada punto es un cliente. Más a la derecha, compra más seguido; más
            arriba, gasta más.
          </p>
          <Scatter />
        </div>
      </div>

      <p className="fineprint left">
        Nombres propuestos por la IA. Puedes cambiarlos con el lápiz junto a cada nombre.
      </p>
    </section>
  )
}
