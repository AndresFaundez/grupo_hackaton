import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import { useSegmentation } from '../context/Segmentation.jsx'

const howItWorks = [
  {
    icon: 'upload',
    title: 'Sube tus ventas',
    text: 'Un archivo con quién compró, cuándo y cuánto. Sirve una exportación de Excel o CSV.',
  },
  {
    icon: 'users',
    title: 'La IA agrupa a tus clientes',
    text: 'Junta a quienes compran parecido: los fieles, los que gastan mucho, los que se están yendo…',
  },
  {
    icon: 'megaphone',
    title: 'Lanza campañas a la medida',
    text: 'Para cada grupo recibes ideas de campaña y un mensaje listo para enviar.',
  },
]

export default function Datos() {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const { start } = useSegmentation()
  const navigate = useNavigate()
  const fileName = file?.name ?? ''

  const onPick = (event) => {
    const picked = event.target.files?.[0]
    if (picked) setFile(picked)
  }

  const onDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    const dropped = event.dataTransfer.files?.[0]
    if (dropped) setFile(dropped)
  }

  const run = (source) => {
    start(source)
    navigate('/procesando')
  }

  return (
    <section className="welcome">
      <div className="welcome-hero">
        <span className="orb o1" aria-hidden="true" />
        <span className="orb o2" aria-hidden="true" />
        <span className="orb o3" aria-hidden="true" />

        <span className="eyebrow">
          <Icon name="sparkle" size={14} /> Segmentación de clientes con IA
        </span>
        <h1 className="display hero-title">
          Descubre <em>quiénes</em> son tus clientes
        </h1>
        <p className="lead hero-lead">
          Sube tu historial de ventas. Agrupamos a tus clientes según cómo
          compran y te decimos qué campaña funciona mejor con cada grupo.
        </p>

        <label
          className={'dropzone' + (dragging ? ' dragging' : '') + (fileName ? ' ready' : '')}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={onPick}
            aria-label="Archivo de ventas"
          />
          <span className="dropzone-icon" aria-hidden="true">
            <Icon name={fileName ? 'file' : 'upload'} size={26} />
          </span>
          {fileName ? (
            <>
              <strong className="dropzone-title">{fileName}</strong>
              <span className="muted small">Listo para analizar · haz clic para cambiarlo</span>
            </>
          ) : (
            <>
              <strong className="dropzone-title">Arrastra tu archivo de ventas aquí</strong>
              <span className="muted small">
                o haz clic para buscarlo · CSV o Excel con cliente, fecha y monto
              </span>
            </>
          )}
        </label>

        <div className="hero-actions">
          {fileName && (
            <button className="primary large" onClick={() => run({ file })}>
              Analizar mis clientes <Icon name="arrowRight" size={18} />
            </button>
          )}
          <button
            className={fileName ? 'link-button' : 'secondary large'}
            onClick={() => run({ sample: true })}
          >
            {fileName ? 'o usar datos de ejemplo' : 'Probar con datos de ejemplo'}
          </button>
        </div>

        <p className="fineprint privacy">
          <Icon name="shield" size={14} />
          Los datos personales (nombres, emails, teléfonos, RUT) nunca se envían
          a la IA: solo estadísticas de cada segmento.
        </p>
      </div>

      <ol className="how-it-works" aria-label="Cómo funciona">
        {howItWorks.map((item, index) => (
          <li className="how-item" key={item.title} style={{ animationDelay: `${0.15 + index * 0.1}s` }}>
            <span className="how-icon" aria-hidden="true">
              <Icon name={item.icon} size={20} />
            </span>
            <span className="how-step">Paso {index + 1}</span>
            <h3>{item.title}</h3>
            <p>{item.text}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
