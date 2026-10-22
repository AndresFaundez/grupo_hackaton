import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import ClusterAnimation from '../components/ClusterAnimation.jsx'
import { useSegmentation } from '../context/Segmentation.jsx'

const phases = [
  'Leyendo transacciones…',
  'Calculando métricas de recencia, frecuencia y gasto…',
  'Agrupando clientes con similitudes de compra…',
  'Interpretando y nombrando los clusters con IA…',
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
      <h2 className="sr-only">Procesamiento</h2>
      <div className="card processing-card">
        <div className="processing-spinner" aria-hidden="true">
          {done ? '✓' : failed ? '!' : '…'}
        </div>
        <h3>{done ? 'Segmentación lista' : failed ? 'No pudimos procesar tus datos' : 'Procesando tus datos'}</h3>
        {failed ? (
          <p className="error-box">{error}</p>
        ) : (
          <div className="anim-stage">
            <ClusterAnimation />
          </div>
        )}
        <ul className="phase-list">
          {phases.map((label, index) => (
            <li
              key={label}
              className={
                index < phase ? 'done' : index === phase && !failed ? 'current' : 'pending'
              }
            >
              {label}
            </li>
          ))}
        </ul>
        <div className="bar" aria-hidden="true">
          <span
            style={{ width: `${done ? 100 : progress}%`, background: failed ? '#e04f2f' : '#3538cd' }}
          />
        </div>
        <div className="actions center">
          {failed ? (
            <>
              <button className="secondary" onClick={() => navigate('/')}>Volver</button>
              <button className="primary" onClick={process}>Reintentar</button>
            </>
          ) : (
            <button className="primary" disabled={!done} onClick={() => navigate('/clusters')}>
              {done ? 'Ver mis clusters' : 'Procesando…'}
            </button>
          )}
        </div>
        <p className="fineprint">
          El clustering y la interpretación con IA corren en el backend; suele tardar entre 10 y 20 segundos.
        </p>
      </div>
    </section>
  )
}
