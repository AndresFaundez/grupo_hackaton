import { Link } from 'react-router-dom'
import { useSegmentation } from '../context/Segmentation.jsx'

// Envuelve las vistas que necesitan una segmentación lista.
export default function NeedsData({ children }) {
  const { status, clusters } = useSegmentation()
  if (clusters.length) return children

  const processing = status === 'processing'
  return (
    <section className="empty-state card">
      <h3>{processing ? 'Estamos procesando tus datos' : 'Aún no hay una segmentación'}</h3>
      <p className="muted">
        {processing
          ? 'En unos segundos tendrás tus clusters listos.'
          : 'Sube tu historial de transacciones o usa los datos de ejemplo para empezar.'}
      </p>
      <Link className="primary" to={processing ? '/procesando' : '/'}>
        {processing ? 'Ver el procesamiento' : 'Ir a cargar datos'}
      </Link>
    </section>
  )
}
