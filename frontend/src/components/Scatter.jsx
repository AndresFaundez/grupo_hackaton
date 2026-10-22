import { clusters } from '../data/demoClusters.js'

// Gráfico de dispersión: eje X = frecuencia de compra, eje Y = gasto promedio.
export default function Scatter({ highlight, onPointClick }) {
  const W = 460
  const H = 320
  const PAD = { top: 16, right: 16, bottom: 40, left: 56 }

  const allPoints = clusters.flatMap((c) =>
    c.points.map((p) => ({ ...p, cluster: c.id, color: c.color })),
  )
  const maxX = Math.max(...allPoints.map((p) => p.x)) * 1.08
  const maxY = Math.max(...allPoints.map((p) => p.y)) * 1.08

  const sx = (x) => PAD.left + (x / maxX) * (W - PAD.left - PAD.right)
  const sy = (y) => H - PAD.bottom - (y / maxY) * (H - PAD.top - PAD.bottom)

  return (
    <figure className="scatter-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="scatter"
        role="img"
        aria-label="Clientes agrupados por segmento: gasto versus frecuencia de compra"
      >
        {/* ejes */}
        <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} className="axis" />
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} className="axis" />
        {/* etiquetas */}
        <text x={W - PAD.right} y={H - 12} textAnchor="end" className="axis-label">
          Frecuencia de compra →
        </text>
        <text x={12} y={PAD.top} className="axis-label">↑ Gasto</text>
        {/* puntos */}
        {allPoints.map((p, i) => (
          <circle
            key={i}
            cx={sx(p.x)}
            cy={sy(p.y)}
            r={highlight && highlight !== p.cluster ? 3 : 6}
            fill={p.color}
            opacity={highlight && highlight !== p.cluster ? 0.25 : 0.85}
            className="scatter-point"
            onClick={() => onPointClick?.(p.cluster)}
          />
        ))}
      </svg>
      <figcaption>Haz clic en un punto para explorar su grupo.</figcaption>
    </figure>
  )
}
