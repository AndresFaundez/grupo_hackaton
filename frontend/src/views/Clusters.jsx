import { useState } from 'react'
import { clusters } from '../data/demoClusters.js'
import { formatCLP, formatNumber } from '../lib/format.js'
import ChatPanel from '../components/ChatPanel.jsx'

export default function Clusters() {
  const [selectedId, setSelectedId] = useState(clusters[0].id)
  const selected = clusters.find((c) => c.id === selectedId)

  return (
    <section>
      <h2>Clusters</h2>
      <p className="lead">
        Los clusters más importantes de la segmentación. Selecciona uno para
        ver su detalle y conversa con la IA sobre él.
      </p>

      {/* Zona grande: tarjetas de clusters */}
      <div className="cluster-row">
        {clusters.map((cluster) => (
          <button
            key={cluster.id}
            className={
              cluster.id === selectedId
                ? 'card cluster-pick selected'
                : 'card cluster-pick'
            }
            onClick={() => setSelectedId(cluster.id)}
          >
            <span
              className="cluster-dot"
              style={{ background: cluster.color }}
              aria-hidden="true"
            />
            <span className="cluster-pick-body">
              <strong>{cluster.name}</strong>
              <span className="muted">
                {formatNumber(cluster.customers)} clientes ·{' '}
                {formatCLP(cluster.sales)}
              </span>
            </span>
          </button>
        ))}
      </div>

      {/* Paneles inferiores: detalle (izq) + chat (der) */}
      <div className="workspace">
        <article className="card detail">
          <div className="cluster-head">
            <span
              className="cluster-dot"
              style={{ background: selected.color }}
              aria-hidden="true"
            />
            <h3>{selected.name}</h3>
          </div>
          <div className="badges">
            {selected.characterization.map((tag) => (
              <span className="badge" key={tag}>{tag}</span>
            ))}
          </div>

          <p className="cluster-desc">{selected.description}</p>

          <div className="detail-grid">
            <div className="detail-item">
              <h4>Cliente más representativo</h4>
              <p>
                <strong>{selected.representativeCustomer.name}</strong>,{' '}
                {selected.representativeCustomer.age} años
              </p>
              <p className="muted">{selected.representativeCustomer.profile}</p>
            </div>
            <div className="detail-item">
              <h4>Tamaño de ventas</h4>
              <p className="stat-value">{formatCLP(selected.sales)}</p>
              <p className="muted">
                {formatNumber(selected.customers)} clientes en el cluster
              </p>
            </div>
            <div className="detail-item">
              <h4>Frecuencia de compra</h4>
              <p className="stat-value">{selected.frequency}</p>
            </div>
            <div className="detail-item">
              <h4>Qué compran en general</h4>
              <ul className="chip-list">
                {selected.topProducts.map((product) => (
                  <li className="chip" key={product}>{product}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="detail-item">
            <h4>Estrategias de marketing sugeridas</h4>
            <ul className="strategy-list">
              {selected.strategies.map((strategy) => (
                <li key={strategy}>{strategy}</li>
              ))}
            </ul>
          </div>
        </article>

        <div className="chat-dock">
          <div className="chat-dock-title">Chat IA sobre los clusters</div>
          <ChatPanel
            compact
            intro={`Pregúntame por el cluster "${selected.name}" o por cualquier otro segmento. Puedo darte estrategias y más información.`}
          />
        </div>
      </div>
    </section>
  )
}
