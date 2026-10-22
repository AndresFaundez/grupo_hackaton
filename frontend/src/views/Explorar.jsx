import { Link, useSearchParams } from 'react-router-dom'
import { formatCLP, formatDecimal, formatNumber, formatPercent } from '../lib/format.js'
import { useCluster, useSegmentation } from '../context/Segmentation.jsx'
import EditableName from '../components/EditableName.jsx'
import NeedsData from '../components/NeedsData.jsx'
import Scatter from '../components/Scatter.jsx'
import ChatPanel from '../components/ChatPanel.jsx'

export default function Explorar() {
  return (
    <NeedsData>
      <ClusterDetail />
    </NeedsData>
  )
}

function ClusterDetail() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { clusters, rename } = useSegmentation()
  const id = searchParams.get('segmento') ?? clusters[0].id
  const cluster = useCluster(id)
  const rep = cluster.representativeCustomer

  const select = (cid) => setSearchParams({ segmento: cid })

  return (
    <section className="explore">
      <div className="explore-side">
        <div className="side-title">CLUSTERS</div>
        <ul className="side-list">
          {clusters.map((c) => (
            <li key={c.id}>
              <button
                className={c.id === cluster.id ? 'side-item selected' : 'side-item'}
                onClick={() => select(c.id)}
              >
                <span className="cluster-dot" style={{ background: c.color }} aria-hidden="true" />
                <span className="side-item-body">
                  <strong>{c.name}</strong>
                  <span className="muted">
                    {formatNumber(c.customers)} clientes · {formatPercent(c.share)}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        <div className="card scatter-card small">
          <Scatter highlight={cluster.id} onPointClick={select} />
        </div>
      </div>

      <div className="explore-main">
        <article className="card detail">
          <p className="muted small">
            Nombre y descripción propuestos por la IA · editables
          </p>
          <div className="cluster-head">
            <span className="cluster-dot" style={{ background: cluster.color }} aria-hidden="true" />
            <EditableName name={cluster.name} onRename={(name) => rename(cluster.id, name)} />
          </div>
          <div className="badges">
            {cluster.characterization.map((tag) => (
              <span className="badge" key={tag}>{tag}</span>
            ))}
          </div>
          <p className="cluster-desc">{cluster.description}</p>

          <h3 className="detail-heading">Características que distinguen al grupo</h3>
          <ul className="chip-list">
            {cluster.traits.map((trait) => (
              <li className="chip" key={trait}>{trait}</li>
            ))}
          </ul>

          <div className="detail-grid">
            <div className="detail-item">
              <h4>Tamaño del segmento</h4>
              <p className="stat-value">{formatNumber(cluster.customers)}</p>
              <p className="muted">
                {formatPercent(cluster.share)} de la base
                {cluster.revenueShare != null && <> · {formatPercent(cluster.revenueShare)} de las ventas</>}
              </p>
            </div>
            <div className="detail-item">
              <h4>Gasto promedio</h4>
              <p className="stat-value">{formatCLP(cluster.avgSpend)}</p>
              <p className="muted">por cliente{cluster.avgTicket != null && <> · ticket {formatCLP(cluster.avgTicket)}</>}</p>
            </div>
            <div className="detail-item">
              <h4>Frecuencia</h4>
              <p className="stat-value">{formatDecimal(cluster.frequencyPerYear)}</p>
              <p className="muted">
                compras al año
                {cluster.daysSinceLastPurchase != null && (
                  <> · última hace {Math.round(cluster.daysSinceLastPurchase)} días</>
                )}
              </p>
            </div>
            <div className="detail-item">
              <h4>Qué compran en general</h4>
              <ul className="chip-list">
                {cluster.topProducts.length ? (
                  cluster.topProducts.map((p) => (
                    <li className="chip" key={p}>{p}</li>
                  ))
                ) : (
                  <li className="muted">Sin categorías en los datos</li>
                )}
              </ul>
            </div>
            {rep && (
              <div className="detail-item wide">
                <h4>Cliente más representativo</h4>
                <p>
                  <strong>{rep.name}</strong>
                  {rep.facts && <span className="muted"> · {rep.facts}</span>}
                </p>
                {rep.profile && <p className="muted">{rep.profile}</p>}
              </div>
            )}
          </div>

          <h3 className="detail-heading">Estrategias de marketing sugeridas</h3>
          <ul className="strategy-list">
            {cluster.strategies.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>

          <Link className="primary campaign-link" to={`/campana?segmento=${cluster.id}`}>
            Preparar campaña para este segmento
          </Link>
        </article>

        <div className="chat-dock">
          <div className="chat-dock-title">Chat con los datos · {cluster.name}</div>
          <ChatPanel
            key={cluster.id}
            compact
            clusterId={cluster.clusterId}
            suggestions={cluster.suggestedQuestions}
            intro={`Pregúntame por el cluster "${cluster.name}" o por cualquier otro segmento. Puedo darte estrategias y más información.`}
          />
        </div>
      </div>
    </section>
  )
}
