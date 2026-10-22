import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSegmentation } from '../context/Segmentation.jsx'

export default function Datos() {
  const [file, setFile] = useState(null)
  const { start } = useSegmentation()
  const navigate = useNavigate()

  const onPick = (event) => {
    const picked = event.target.files?.[0]
    if (picked) setFile(picked)
  }

  const run = (source) => {
    start(source)
    navigate('/procesando')
  }

  return (
    <section className="hero">
      <div className="hero-gradient">
        <span className="floating-dot d1" aria-hidden="true" />
        <span className="floating-dot d2" aria-hidden="true" />
        <span className="floating-dot d3" aria-hidden="true" />
        <span className="floating-dot d4" aria-hidden="true" />
        <h1 className="hero-title">Descubre quiénes son tus clientes</h1>
        <p className="lead center">
          Sube tu historial de transacciones. Agruparemos a tus clientes según
          cuándo compran, con qué frecuencia y cuánto gastan.
        </p>

        <div className="card dropzone">
        <div className="dropzone-icon" aria-hidden="true">+</div>
        <label className="dropzone-label">
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={onPick}
            aria-label="Archivo de transacciones"
          />
          <span>
            {file
              ? `Archivo seleccionado: ${file.name}`
              : 'Arrastra tu archivo CSV o Excel aquí'}
          </span>
          <span className="muted small">
            o haz clic para seleccionarlo · id de cliente, fecha y monto como mínimo
          </span>
        </label>
      </div>

      <div className="upload-alt">
        <span className="muted">o</span>
        <button className="primary" onClick={() => run({ sample: true })}>
          Usar datos de ejemplo
        </button>
      </div>

      {file && (
        <div className="actions center">
          <button className="primary" onClick={() => run({ file })}>
            Procesar base de datos
          </button>
        </div>
      )}

      <p className="fineprint">
        Los datos personales (nombres, emails, teléfonos, RUT) nunca se envían a
        la IA: solo estadísticas agregadas de cada segmento.
      </p>
      </div>
    </section>
  )
}
