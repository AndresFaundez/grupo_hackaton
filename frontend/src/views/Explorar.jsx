import { Link, useSearchParams } from 'react-router-dom'
import {
  daysBetweenPurchases,
  formatCLP,
  formatDecimal,
  formatMillions,
  formatNumber,
  formatPercent,
} from '../lib/format.js'
import { salesOf } from '../lib/segments.js'
import { useCluster, useSegmentation } from '../context/Segmentation.jsx'
import EditableName from '../components/EditableName.jsx'
import NeedsData from '../components/NeedsData.jsx'
import Scatter from '../components/Scatter.jsx'
import ChatPanel from '../components/ChatPanel.jsx'
import Icon from '../components/Icon.jsx'

const initials = (fullName) =>
  fullName
    .split(/\s+/)
    .filter((part) => /^\p{L}/u.test(part))
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase() || '★'

export default function Explorar() {
  return (
    <NeedsData>
      <ClusterDetail />
    </NeedsData>
  )
}

function ClusterDetail() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { clusters, dataset, rename } = useSegmentation()
  const id = searchParams.get('segmento') ?? clusters[0].id
  const cluster = useCluster(id)
  const rep = cluster.representativeCustomer
  const days = daysBetweenPurchases(cluster.frequencyPerYear)

  const select = (cid) => setSearchParams({ segmento: cid })

  const kpis = [
    {
      icon: 'users',
      label: 'Clientes',
      value: formatNumber(cluster.customers),
      note: `${formatPercent(cluster.share)} de tu base`,
    },
    {
      icon: 'coins',
      label: 'Ventas del grupo',
      value: formatMillions(salesOf(cluster, dataset)),
      note:
        cluster.revenueShare != null ? `${formatPercent(cluster.revenueShare)} de tus ventas` : 'del total',
    },
    {
      icon: 'ticket',
      label: 'Gasto por cliente',
      value: formatCLP(cluster.avgSpend),
      note: cluster.avgTicket != null ? `ticket promedio ${formatCLP(cluster.avgTicket)}` : 'promedio',
    },
    {
      icon: 'repeat',
      label: 'Frecuencia',
      value: days != null ? `Cada ~${days} días` : '—',
      note:
        cluster.daysSinceLastPurchase != null
          ? `última compra hace ${Math.round(cluster.daysSinceLastPurchase)} días`
          : `${formatDecimal(cluster.frequencyPerYear)} compras al año`,
    },
  ]

  return (
    <section className="explore">
      <aside className="explore-side">
        <h2 className="side-title">Tus segmentos</h2>
        <ul className="side-list">
          {clusters.map((c) => (
            <li key={c.id}>
              <button
                className={c.id === cluster.id ? 'side-item selected' : 'side-item'}
                style={{ '--seg': c.color }}
                onClick={() => select(c.id)}
                aria-current={c.id === cluster.id ? 'true' : undefined}
              >
                <span className="cluster-swatch" aria-hidden="true" />
                <span className="side-item-body">
                  <strong>{c.name}</strong>
                  <span className="muted small">
                    {formatNumber(c.customers)} clientes · {formatPercent(c.share)}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        <div className="card map-card compact">
          <Scatter highlight={cluster.id} onPointClick={select} showLegend={false} />
          <p className="muted small map-help">Toca un punto para cambiar de grupo.</p>
        </div>
      </aside>

      <div className="explore-main">
        <article className="detail" key={cluster.id} style={{ '--seg': cluster.color }}>
          <header className="detail-hero">
            <span className="eyebrow">
              <Icon name="sparkle" size={14} /> Perfil creado por la IA
            </span>
            <div className="detail-title">
              <EditableName as="h1" name={cluster.name} onRename={(name) => rename(cluster.id, name)} />
            </div>
            <p className="detail-desc">{cluster.description}</p>
            {cluster.characterization.length > 0 && (
              <ul className="tag-list" aria-label="Rasgos principales">
                {cluster.characterization.map((tag) => (
                  <li className="tag" key={tag}>{tag}</li>
                ))}
              </ul>
            )}
          </header>

          <dl className="kpi-grid">
            {kpis.map((kpi) => (
              <div className="kpi" key={kpi.label}>
                <dt>
                  <Icon name={kpi.icon} size={16} /> {kpi.label}
                </dt>
                <dd className="kpi-value">{kpi.value}</dd>
                <dd className="muted small">{kpi.note}</dd>
              </div>
            ))}
          </dl>

          <div className="detail-columns">
            <section className="card persona">
              <h3 className="card-title">
                <Icon name="target" size={18} /> Su cliente típico
              </h3>
              {rep ? (
                <>
                  <div className="persona-head">
                    <span className="persona-avatar" aria-hidden="true">
                      {initials(rep.name)}
                    </span>
                    <div>
                      <strong>{rep.name}</strong>
                      {rep.facts && <span className="muted small d-block">{rep.facts}</span>}
                    </div>
                  </div>
                  {rep.profile && <p className="persona-quote">{rep.profile}</p>}
                </>
              ) : (
                <p className="muted">Sin un cliente representativo en los datos.</p>
              )}
              {cluster.traits.length > 0 && (
                <>
                  <h4 className="mini-heading">Qué los distingue</h4>
                  <ul className="chip-list">
                    {cluster.traits.map((trait) => (
                      <li className="chip" key={trait}>{trait}</li>
                    ))}
                  </ul>
                </>
              )}
            </section>

            <section className="card">
              <h3 className="card-title">
                <Icon name="bag" size={18} /> Lo que más compran
              </h3>
              {cluster.topProducts.length ? (
                <ol className="rank-list">
                  {cluster.topProducts.map((product, index) => (
                    <li key={product}>
                      <span className="rank-num">{index + 1}</span>
                      {product}
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="muted">Tu archivo no trae productos ni categorías.</p>
              )}
            </section>
          </div>

          <section className="card ideas">
            <h3 className="card-title">
              <Icon name="bulb" size={18} /> Ideas de campaña para este grupo
            </h3>
            <ol className="idea-list">
              {cluster.strategies.map((strategy, index) => (
                <li key={strategy}>
                  <span className="idea-num">{String(index + 1).padStart(2, '0')}</span>
                  <span>{strategy}</span>
                </li>
              ))}
            </ol>
            <Link className="primary" to={`/campana?segmento=${cluster.id}`}>
              <Icon name="megaphone" size={18} /> Crear campaña para {cluster.name}
            </Link>
          </section>
        </article>

        <aside className="chat-dock">
          <div className="chat-dock-head">
            <span className="ai-avatar" aria-hidden="true">
              <Icon name="sparkle" size={16} />
            </span>
            <div>
              <strong>Pregúntale a la IA</strong>
              <span className="muted small d-block">sobre {cluster.name}</span>
            </div>
          </div>
          <ChatPanel
            key={cluster.id}
            clusterId={cluster.clusterId}
            suggestions={cluster.suggestedQuestions}
            intro={`Conozco a fondo a «${cluster.name}». Pregúntame qué les gusta, cómo hablarles o qué campaña lanzarles.`}
          />
        </aside>
      </div>
    </section>
  )
}
