import { useState } from 'react'

export default function Upload() {
  const [fileName, setFileName] = useState('')
  const [status, setStatus] = useState('idle')

  const onPick = (event) => {
    const file = event.target.files?.[0]
    if (file) {
      setFileName(file.name)
      setStatus('idle')
    }
  }

  const onProcess = () => {
    if (!fileName) return
    setStatus('pending')
  }

  return (
    <section>
      <h2>Subir base de datos</h2>
      <p className="lead">
        Pasa la base de transacciones en bruto para que el sistema la procese
        y genere la segmentación de clientes.
      </p>

      <div className="card dropzone">
        <div className="dropzone-icon" aria-hidden="true">+</div>
        <label className="dropzone-label">
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            onChange={onPick}
            aria-label="Archivo de base de datos"
          />
          <span>
            {fileName
              ? `Archivo seleccionado: ${fileName}`
              : 'Arrastra tu archivo aquí o haz clic para elegirlo (CSV, Excel, JSON)'}
          </span>
        </label>
      </div>

      <div className="actions">
        <button
          className="primary"
          onClick={onProcess}
          disabled={!fileName || status === 'pending'}
        >
          {status === 'pending' ? 'Procesando…' : 'Procesar base de datos'}
        </button>
      </div>

      {status === 'pending' && (
        <p className="placeholder">
          El envío al servicio de clustering quedará conectado cuando el equipo
          de backend publique el contrato de API. Esta demo no envía datos.
        </p>
      )}
    </section>
  )
}
