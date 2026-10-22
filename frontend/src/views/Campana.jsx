import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { channels, objectives } from '../lib/campaign.js'
import { formatNumber, formatPercent } from '../lib/format.js'
import { useCluster, useSegmentation } from '../context/Segmentation.jsx'
import CampaignChat from '../components/CampaignChat.jsx'
import NeedsData from '../components/NeedsData.jsx'
import Icon from '../components/Icon.jsx'

export default function Campana() {
  return (
    <NeedsData>
      <CampaignBuilder />
    </NeedsData>
  )
}

function CampaignBuilder() {
  const [searchParams, setSearchParams] = useSearchParams()
  const segmentoId = searchParams.get('segmento')
  const { clusters } = useSegmentation()
  const cluster = useCluster(segmentoId ?? clusters[0].id)
  const [progress, setProgress] = useState({})
  const onProgress = useCallback((p) => setProgress(p), [])

  const choose = (id) => setSearchParams(id ? { segmento: id } : {})

  if (!segmentoId) {
    return (
      <section className="campaign">
        <header className="page-head">
          <span className="eyebrow">
            <Icon name="megaphone" size={14} /> Nueva campaña
          </span>
          <h1 className="display">
            ¿A quién le <em>hablamos</em> hoy?
          </h1>
          <p className="lead">
            Elige el segmento que recibirá la campaña. Después definimos el
            objetivo, el canal y el mensaje conversando con la IA.
          </p>
        </header>
        <div className="segment-grid">
          {clusters.map((c) => {
            const objective = objectives.find((o) => o.id === c.suggestedObjective)
            return (
              <button
                key={c.id}
                className="segment-pick"
                style={{ '--seg': c.color }}
                onClick={() => choose(c.id)}
              >
                <span className="cluster-swatch" aria-hidden="true" />
                <strong className="segment-pick-name">{c.name}</strong>
                <span className="muted small">
                  {formatNumber(c.customers)} clientes · {formatPercent(c.share)} de tu base
                </span>
                {objective && (
                  <span className="segment-pick-goal">
                    <Icon name="sparkle" size={13} /> Ideal para: {objective.label.toLowerCase()}
                  </span>
                )}
                <span className="segment-pick-go" aria-hidden="true">
                  <Icon name="arrowRight" size={18} />
                </span>
              </button>
            )
          })}
        </div>
      </section>
    )
  }

  const objective = objectives.find((o) => o.id === progress.objetivo)
  const channel = channels.find((c) => c.id === progress.canal)
  const checklist = [
    { label: 'Segmento', value: cluster.name, done: true },
    { label: 'Objetivo', value: objective?.label, done: Boolean(objective) },
    { label: 'Canal', value: channel?.label, done: Boolean(channel) },
    {
      label: 'Mensaje',
      value: progress.draft ? 'Borrador listo' : progress.pending ? 'Escribiendo…' : null,
      done: Boolean(progress.draft),
    },
  ]

  return (
    <section className="campaign">
      <header className="page-head row">
        <div>
          <span className="eyebrow">
            <Icon name="megaphone" size={14} /> Nueva campaña
          </span>
          <h1 className="display">
            Campaña para <em>{cluster.name}</em>
          </h1>
        </div>
        <button className="secondary" onClick={() => choose(null)}>
          <Icon name="arrowLeft" size={16} /> Cambiar segmento
        </button>
      </header>

      <div className="campaign-layout">
        <div className="card campaign-chat-card">
          <CampaignChat key={cluster.id} cluster={cluster} onProgress={onProgress} />
        </div>

        <aside className="card campaign-summary-card" style={{ '--seg': cluster.color }}>
          <h2 className="card-title">Tu campaña</h2>
          <p className="muted small">{formatNumber(cluster.customers)} clientes la recibirán</p>
          <ol className="checklist">
            {checklist.map((item) => (
              <li key={item.label} className={item.done ? 'done' : ''}>
                <span className="check-mark" aria-hidden="true">
                  {item.done && <Icon name="check" size={12} strokeWidth={2.6} />}
                </span>
                <span>
                  <span className="check-label">{item.label}</span>
                  <span className="check-value">{item.value ?? 'Por definir'}</span>
                </span>
              </li>
            ))}
          </ol>
          {progress.draft && (
            <blockquote className="preview-message">
              {progress.draft.subject && <strong className="d-block">{progress.draft.subject}</strong>}
              {progress.draft.message}
            </blockquote>
          )}
          {progress.launched && (
            <p className="launched-note">
              <Icon name="check" size={16} strokeWidth={2.4} /> Campaña lista (simulación)
            </p>
          )}
        </aside>
      </div>
    </section>
  )
}
