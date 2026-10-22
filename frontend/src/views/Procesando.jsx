import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import ClusterAnimation from '../components/ClusterAnimation.jsx'
import Icon from '../components/Icon.jsx'
import { useSegmentation } from '../context/Segmentation.jsx'

const phases = [
  'Leyendo tus ventas',
  'Midiendo cuánto gasta y cada cuánto compra cada cliente',
  'Juntando a los clientes que compran parecido',
  'Poniéndole nombre a cada grupo y buscando ideas de campaña',
]

export default function Procesando() {
  const { source, status, step, error, process, clusters } = useSegmentation()
  const [phase, setPhase] = useState(0)
  const navigate = useNavigate()

  // Arranca el procesamiento real al entrar con un origen de datos nuevo.
  useEffect(() => {
    if (status === 'idle' && source) process()
  }, [status, source, process])

  // El backend responde en dos pasos (subida y clustering); las fases intermedias
  // avanzan con el tiempo mientras se espera la respuesta del clustering.
  useEffect(() => {
    if (status === 'ready') {
      setPhase(phases.length)
      return
    }
    if (status !== 'processing') return
    if (step === 0) {
      setPhase(0)
      return
    }
    if (phase === 0) {
      setPhase(1)
      return
    }
    if (phase < phases.length - 1) {
      const timer = setTimeout(() => setPhase((p) => p + 1), 2500)
      return () => clearTimeout(timer)
    }
  }, [status, step, phase])

  if (status === 'idle' && !source && !clusters.length) return <Navigate to="/" replace />

  const done = status === 'ready'
  const failed = status === 'error'
  const progress = Math.min(100, Math.round((phase / phases.length) * 100))

  return (
    <section className="processing">
      <header className="page-head center">
        <span className={'eyebrow' + (failed ? ' danger' : '')}>
          <Icon name={failed ? 'alert' : 'sparkle'} size={14} />{' '}
          {done ? 'Análisis completo' : failed ? 'Algo salió mal' : 'Analizando'}
        </span>
        <h1 className="display">
          {done ? (
            <>Tus clientes ya tienen <em>grupo</em></>
          ) : failed ? (
            <>No pudimos analizar <em>tus datos</em></>
          ) : (
            <>Estamos conociendo a <em>tus clientes</em></>
          )}
        </h1>
        <p className="lead">
          {failed
            ? 'Revisa el detalle de abajo y vuelve a intentarlo, o prueba con otro archivo.'
            : 'Cada punto es un cliente. Los que compran de forma parecida se van juntando hasta formar un segmento.'}
        </p>
      </header>

      <div className="card processing-card">
        {failed ? (
          <div className="error-box">
            <Icon name="alert" size={18} />
            <span>{error}</span>
          </div>
        ) : (
          <div className="anim-stage">
            <ClusterAnimation />
          </div>
        )}

        <div className="processing-body">
          <ul className="phase-list">
            {phases.map((label, index) => {
              const state =
                index < phase ? 'done' : index === phase && !failed ? 'current' : 'pending'
              return (
                <li key={label} className={state}>
                  <span className="phase-mark" aria-hidden="true">
                    {state === 'done' && <Icon name="check" size={12} strokeWidth={2.6} />}
                  </span>
                  {label}
                </li>
              )
            })}
          </ul>

          <div
            className={'progress' + (failed ? ' failed' : '')}
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={done ? 100 : progress}
            aria-label="Avance del análisis"
          >
            <span style={{ width: `${done ? 100 : Math.max(progress, 6)}%` }} />
          </div>

          {failed ? (
            <div className="button-row">
              <button className="secondary large" onClick={() => navigate('/')}>
                <Icon name="arrowLeft" size={18} /> Volver
              </button>
              <button className="primary large" onClick={process}>
                Reintentar
              </button>
            </div>
          ) : (
            <button className="primary large" disabled={!done} onClick={() => navigate('/clusters')}>
              {done ? (
                <>Ver mis segmentos <Icon name="arrowRight" size={18} /></>
              ) : (
                'Analizando…'
              )}
            </button>
          )}
        </div>
      </div>

      <p className="fineprint">Suele tardar entre 10 y 20 segundos.</p>
    </section>
  )
}
