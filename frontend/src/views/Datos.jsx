import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Datos() {
  const [fileName, setFileName] = useState('')
  const navigate = useNavigate()

  const onPick = (event) => {
    const file = event.target.files?.[0]
    if (file) setFileName(file.name)
  }

  const start = () => {
    if (!fileName) return
    navigate('/procesando')
  }

  return (
    <section className="hero">
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
            accept=".csv,.xlsx,.xls,.json"
            onChange={onPick}
            aria-label="Archivo de transacciones"
          />
          <span>
            {fileName
              ? `Archivo seleccionado: ${fileName}`
              : 'Arrastra tu archivo CSV aquí'}
          </span>
          <span className="muted small">
            o haz clic para seleccionarlo · id de cliente, fecha y monto como mínimo
          </span>
        </label>
      </div>

      <div className="upload-alt">
        <span className="muted">o</span>
        <button className="primary" onClick={() => navigate('/procesando')}>
          Usar datos de ejemplo
        </button>
      </div>

      {fileName && (
        <div className="actions center">
          <button className="primary" onClick={start}>
            Procesar base de datos
          </button>
        </div>
      )}

      <p className="fineprint">
        El envío al servicio de clustering quedará conectado cuando el equipo de
        backend publique el contrato de API. Esta demo no envía datos.
      </p>
    </section>
  )
}
