import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { formatNumber, formatPercent } from '../lib/format.js'
import { useCluster, useSegmentation } from '../context/Segmentation.jsx'
import CampaignChat from '../components/CampaignChat.jsx'
import NeedsData from '../components/NeedsData.jsx'

export default function Campana() {
  return (
    <NeedsData>
      <CampaignBuilder />
    </NeedsData>
  )
}

function CampaignBuilder() {
  const [searchParams] = useSearchParams()
  const { clusters } = useSegmentation()
  const [segmentoId, setSegmentoId] = useState(searchParams.get('segmento'))
  const cluster = useCluster(segmentoId ?? clusters[0].id)

  return (
    <section>
      <h2>Preparar campaña</h2>

      {!segmentoId ? (
        <>
          <p className="lead">
            Elige el segmento al que va dirigida la campaña. Luego definimos
            el resto conversando con la IA.
          </p>
          <div className="segment-grid">
            {clusters.map((c) => (
              <button
                key={c.id}
                className="segment-pick"
                onClick={() => setSegmentoId(c.id)}
              >
                <span className="cluster-dot" style={{ background: c.color }} aria-hidden="true" />
                <span>
                  <strong>{c.name}</strong>
                  <span className="muted d-block">
                    {formatNumber(c.customers)} clientes · {formatPercent(c.share)}
                  </span>
                </span>
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <div className="campaign-head">
            <p className="lead">
              Campaña para <strong>{cluster.name}</strong> ·{' '}
              {formatNumber(cluster.customers)} clientes
            </p>
            <button className="secondary" onClick={() => setSegmentoId(null)}>
              ← Cambiar de segmento
            </button>
          </div>
          <div className="card chat-wrap">
            <CampaignChat key={segmentoId} cluster={cluster} />
          </div>
        </>
      )}
    </section>
  )
}
