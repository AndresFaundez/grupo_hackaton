import { useNavigate } from 'react-router-dom'
import { useSegmentation } from '../context/Segmentation.jsx'

const W = 460
const H = 320
const PAD = { top: 18, right: 16, bottom: 36, left: 36 }
const gridX = [0.25, 0.5, 0.75, 1].map((t) => PAD.left + t * (W - PAD.left - PAD.right))
const gridY = [0, 0.25, 0.5, 0.75].map((t) => PAD.top + t * (H - PAD.top - PAD.bottom))

// Recorta los extremos para que unos pocos clientes no aplasten el gráfico.
const quantile = (values, q) => {
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))] ?? 1
}

// Mapa de clientes (por defecto: frecuencia de compra vs gasto).
// Sin onPointClick, un clic lleva al detalle del segmento.
export default function Scatter({ highlight, onPointClick, showLegend = true }) {
  const navigate = useNavigate()
  const { clusters, scatter } = useSegmentation()
  const open = (id) => (onPointClick ? onPointClick(id) : navigate(`/explorar?segmento=${id}`))
  const isDimmed = (id) => highlight && highlight !== id

  const allPoints = clusters.flatMap((c) =>
    c.points.map((p) => ({ ...p, cluster: c.id, color: c.color, name: c.name })),
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

  const xLabel = scatter?.xLabel ?? 'Frecuencia de compra'
  const yLabel = scatter?.yLabel ?? 'Gasto'

  return (
    <figure className="scatter-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="scatter"
        role="img"
        aria-label={`Mapa de clientes por segmento: ${yLabel} según ${xLabel}`}
      >
        {gridX.map((x) => (
          <line key={`x${x}`} x1={x} x2={x} y1={PAD.top} y2={H - PAD.bottom} className="grid" />
        ))}
        {gridY.map((y) => (
          <line key={`y${y}`} x1={PAD.left} x2={W - PAD.right} y1={y} y2={y} className="grid" />
        ))}
        <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} className="axis" />
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} className="axis" />
        <text x={W - PAD.right} y={H - 10} textAnchor="end" className="axis-label">
          {xLabel} →
        </text>
        <text
          x={14}
          y={H - PAD.bottom}
          className="axis-label"
          transform={`rotate(-90 14 ${H - PAD.bottom})`}
        >
          {yLabel}
          {logY ? ' (escala log)' : ''} →
        </text>
        {allPoints.map((p, i) => {
          const dimmed = isDimmed(p.cluster)
          return (
            <circle
              key={i}
              cx={sx(p.x + jitter(i))}
              cy={sy(p.y)}
              r={dimmed ? 2.5 : dense ? 3.2 : 6}
              fill={p.color}
              opacity={dimmed ? 0.18 : dense ? 0.65 : 0.9}
              className={'scatter-point' + (dense ? ' dense' : '')}
              onClick={() => open(p.cluster)}
            >
              <title>{p.name}</title>
            </circle>
          )
        })}
      </svg>
      {showLegend && (
        <figcaption className="legend">
          {clusters.map((c) => (
            <button
              key={c.id}
              type="button"
              className={'legend-item' + (isDimmed(c.id) ? ' dim' : '')}
              onClick={() => open(c.id)}
            >
              <span className="legend-dot" style={{ background: c.color }} aria-hidden="true" />
              {c.name}
            </button>
          ))}
        </figcaption>
      )}
    </figure>
  )
}
