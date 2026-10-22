import { Link } from 'react-router-dom'
import { useSegmentation } from '../context/Segmentation.jsx'
import Icon from './Icon.jsx'

// Envuelve las vistas que necesitan una segmentación lista.
export default function NeedsData({ children }) {
  const { status, clusters } = useSegmentation()
  if (clusters.length) return children

  const processing = status === 'processing'
  return (
    <section className="empty-state card">
      <span className="empty-icon" aria-hidden="true">
        <Icon name={processing ? 'sparkle' : 'upload'} size={26} />
      </span>
      <h1 className="display">
        {processing ? (
          <>Estamos analizando <em>tus datos</em></>
        ) : (
          <>Aún no hay <em>segmentos</em></>
        )}
      </h1>
      <p className="lead">
        {processing
          ? 'En unos segundos tendrás a tus clientes agrupados.'
          : 'Sube tu historial de ventas o prueba con los datos de ejemplo para empezar.'}
      </p>
      <Link className="primary large" to={processing ? '/procesando' : '/'}>
        {processing ? 'Ver el análisis' : 'Cargar mis ventas'} <Icon name="arrowRight" size={18} />
      </Link>
    </section>
  )
}
