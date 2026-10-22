import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const phases = [
  'Leyendo transacciones…',
  'Calculando métricas de recencia, frecuencia y gasto…',
  'Agrupando clientes con similitudes de compra…',
  'Interpretando y nombrando los clusters con IA…',
]

export default function Procesando() {
  const [phase, setPhase] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    if (phase >= phases.length) return
    const timer = setTimeout(() => setPhase((p) => p + 1), 1200)
    return () => clearTimeout(timer)
  }, [phase])

  const done = phase >= phases.length
  const progress = Math.min(100, Math.round((phase / phases.length) * 100))

  return (
    <section className="processing">
      <h2 className="sr-only">Procesamiento</h2>
      <div className="card processing-card">
        <div className="processing-spinner" aria-hidden="true">
          {done ? '✓' : '…'}
        </div>
        <h3>{done ? 'Segmentación lista' : 'Procesando tus datos'}</h3>
        <ul className="phase-list">
          {phases.map((label, index) => (
            <li
              key={label}
              className={
                index < phase ? 'done' : index === phase ? 'current' : 'pending'
              }
            >
              {label}
            </li>
          ))}
        </ul>
        <div className="bar" aria-hidden="true">
          <span
            style={{ width: `${done ? 100 : progress}%`, background: '#3538cd' }}
          />
        </div>
        <div className="actions center">
          <button className="primary" disabled={!done} onClick={() => navigate('/clusters')}>
            {done ? 'Ver mis clusters' : 'Procesando…'}
          </button>
        </div>
        <p className="fineprint">
          Simulación con datos de demostración; el procesamiento real correrá en
          el servicio de clustering.
        </p>
      </div>
    </section>
  )
}
