import { useSegmentation } from '../context/Segmentation.jsx'

// Recorta los extremos para que unos pocos clientes no aplasten el gráfico.
const quantile = (values, q) => {
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))] ?? 1
}

// Gráfico de dispersión de clientes (por defecto: frecuencia de compra vs gasto).
export default function Scatter({ highlight, onPointClick }) {
  const { clusters, scatter } = useSegmentation()
  const W = 460
  const H = 320
  const PAD = { top: 16, right: 16, bottom: 40, left: 56 }

  const allPoints = clusters.flatMap((c) =>
    c.points.map((p) => ({ ...p, cluster: c.id, color: c.color })),
  )
  if (!allPoints.length) return null

  // El gasto suele tener cola larga: si abarca más de 1,5 órdenes de magnitud, eje Y logarítmico.
  const rawYs = allPoints.map((p) => p.y)
  const logY = rawYs.every((y) => y > 0) && quantile(rawYs, 0.98) / quantile(rawYs, 0.02) > 30
  const fy = (y) => (logY ? Math.log10(y) : y)

  const xs = allPoints.map((p) => p.x)
  const ys = allPoints.map((p) => fy(p.y))
  const minX = Math.min(0, ...xs)
  const minY = logY ? quantile(ys, 0.01) * 0.98 : Math.min(0, ...ys)
  const maxX = quantile(xs, 0.98) * 1.08 || 1
  const maxY = logY ? quantile(ys, 0.99) * 1.01 : quantile(ys, 0.98) * 1.08 || 1
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v))
  // Las frecuencias son casi enteras: un poco de dispersión horizontal evita columnas apiladas.
  const jitter = (i) => (((i * 7919) % 97) / 97 - 0.5) * (maxX - minX) * 0.025

  const sx = (x) => PAD.left + ((clamp(x, minX, maxX) - minX) / (maxX - minX)) * (W - PAD.left - PAD.right)
  const sy = (y) => H - PAD.bottom - ((clamp(fy(y), minY, maxY) - minY) / (maxY - minY)) * (H - PAD.top - PAD.bottom)
  const dense = allPoints.length > 300

  return (
    <figure className="scatter-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="scatter"
        role="img"
        aria-label={`Clientes agrupados por segmento: ${scatter?.yLabel ?? 'gasto'} versus ${scatter?.xLabel ?? 'frecuencia'}`}
      >
        {/* ejes */}
        <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} className="axis" />
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} className="axis" />
        {/* etiquetas */}
        <text x={W - PAD.right} y={H - 12} textAnchor="end" className="axis-label">
          {scatter?.xLabel ?? 'Frecuencia de compra'} →
        </text>
        <text x={12} y={PAD.top} className="axis-label">
          ↑ {scatter?.yLabel ?? 'Gasto'}{logY ? ' (escala log)' : ''}
        </text>
        {/* puntos */}
        {allPoints.map((p, i) => {
          const dimmed = highlight && highlight !== p.cluster
          return (
            <circle
              key={i}
              cx={sx(p.x + jitter(i))}
              cy={sy(p.y)}
              r={dimmed ? 2 : dense ? 3.2 : 6}
              fill={p.color}
              opacity={dimmed ? 0.18 : dense ? 0.6 : 0.85}
              className="scatter-point"
              onClick={() => onPointClick?.(p.cluster)}
            />
          )
        })}
      </svg>
      <figcaption>Haz clic en un punto para explorar su grupo.</figcaption>
    </figure>
  )
}
