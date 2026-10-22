import { useMemo, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { channels, clusters, objectives } from '../data/demoClusters.js'
import { formatCLP, formatNumber, formatPercent } from '../lib/format.js'
import { useCluster } from '../context/ClusterNames.jsx'

const wizardSteps = ['Segmento', 'Objetivo y canal', 'Mensaje', 'Revisión']

const drafts = {
  recompra:
    '¡Te espera lo que te gusta! Volviste a estar entre nuestras novedades de la semana. Usa el código VUELVE15 y obtén 15% en tu próxima compra.',
  fidelizar:
    'Como cliente leal, tienes acceso anticipado a nuestro próximo lanzamiento antes que nadie. Gracias por acompañarnos.',
  reactivar:
    'Te extrañamos. Tu opinión es valiosa: cuéntanos qué pasó y recibe un cupón de 20% para tu próxima compra.',
  ticket:
    'Gracias por elegirnos. Como miembro preferente, estrena nuestra línea premium con envío gratis en compras sobre $150.000.',
}

export default function Campana() {
  const [searchParams] = useSearchParams()
  const initialSegmento = searchParams.get('segmento')
  const [step, setStep] = useState(initialSegmento ? 1 : 0)
  const [segmentoId, setSegmentoId] = useState(initialSegmento ?? null)
  const [objetivo, setObjetivo] = useState(null)
  const [canal, setCanal] = useState(null)
  const [mensaje, setMensaje] = useState('')

  const cluster = useCluster(segmentoId ?? clusters[0].id)
  const objetivoDef = useMemo(() => objectives.find((o) => o.id === objetivo), [objetivo])
  const canalDef = useMemo(() => channels.find((c) => c.id === canal), [canal])

  const canNext = [Boolean(segmentoId), Boolean(objetivo && canal), mensaje.trim().length > 0, true][step]

  const pickSegmento = (id) => {
    setSegmentoId(id)
    setObjetivo(clusters.find((c) => c.id === id)?.suggestedObjective ?? null)
  }

  const generate = () => setMensaje(drafts[objetivo] ?? '')

  return (
    <section>
      <div className="wizard-head">
        <h2>Preparar campaña</h2>
        <ol className="wizard-steps">
          {wizardSteps.map((label, index) => (
            <li key={label} className={index === step ? 'current' : index < step ? 'done' : ''}>
              <span className="step-number">{index + 1}</span>. {label}
            </li>
          ))}
        </ol>
      </div>

      <div className="card wizard-body">
        {step === 0 && (
          <>
            <h3 className="detail-heading">1. Segmento</h3>
            <div className="segment-grid">
              {clusters.map((c) => (
                <button
                  key={c.id}
                  className={segmentoId === c.id ? 'segment-pick selected' : 'segment-pick'}
                  onClick={() => pickSegmento(c.id)}
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
        )}

        {step === 1 && (
          <>
            <h3 className="detail-heading">2. Objetivo y canal</h3>
            <div className="option-grid">
              {objectives.map((o) => (
                <button
                  key={o.id}
                  className={objetivo === o.id ? 'option-pick selected' : 'option-pick'}
                  onClick={() => setObjetivo(o.id)}
                >
                  <strong>
                    {o.label}
                    {cluster.suggestedObjective === o.id && (
                      <span className="suggested">SUGERIDO</span>
                    )}
                  </strong>
                  <span className="muted d-block">{o.description}</span>
                </button>
              ))}
            </div>
            <div className="channel-row">
              {channels.map((c) => (
                <button
                  key={c.id}
                  className={canal === c.id ? 'option-pick selected' : 'option-pick'}
                  onClick={() => setCanal(c.id)}
                >
                  {c.label}
                </button>
              ))}
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h3 className="detail-heading">3. Mensaje</h3>
            <textarea
              className="message-box"
              rows={4}
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
              placeholder="Escribe el mensaje de la campaña o genera un borrador con IA…"
              aria-label="Mensaje de la campaña"
            />
            <div className="actions">
              <button className="secondary" onClick={generate} disabled={!objetivo}>
                Generar borrador con IA
              </button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h3 className="detail-heading">4. Revisión</h3>
            <div className="review">
              <p><span className="review-label">Segmento</span> {cluster.name} · {formatNumber(cluster.customers)} clientes</p>
              <p><span className="review-label">Objetivo</span> {objetivoDef?.label}</p>
              <p><span className="review-label">Canal</span> {canalDef?.label}</p>
              <blockquote className="review-message">{mensaje}</blockquote>
              <p className="sim-note">SIMULACIÓN — el envío real quedará conectado al backend.</p>
            </div>
          </>
        )}

        <div className="wizard-nav">
          <button className="secondary" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}>
            ← Atrás
          </button>
          {step < wizardSteps.length - 1 ? (
            <button className="primary" onClick={() => setStep((s) => s + 1)} disabled={!canNext}>
              Continuar →
            </button>
          ) : (
            <button className="primary">Lanzar campaña (demo)</button>
          )}
        </div>
      </div>

      {segmentoId && (
        <p className="muted small">
          Trabajando con el segmento{' '}
          <Link to={`/explorar?segmento=${segmentoId}`}>{cluster.name}</Link>
        </p>
      )}
    </section>
  )
}
