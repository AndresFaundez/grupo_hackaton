import { clusters } from '../data/demoClusters.js'

const W = 800
const H = 400
const PAD = 40

// Animación decorativa: los clientes "caen" al lienzo y se agrupan en
// clusters que emergen con su halo y su nombre. No son datos reales.
const flat = clusters.flatMap((c) =>
  c.points.map((p) => ({ ...p, color: c.color })),
)
const maxX = Math.max(...flat.map((p) => p.x)) * 1.05
const maxY = Math.max(...flat.map((p) => p.y)) * 1.05
const sx = (x) => PAD + (x / maxX) * (W - 2 * PAD)
const sy = (y) => H - PAD - (y / maxY) * (H - 2 * PAD)

const centers = clusters.map((c) => {
  const cx = c.points.reduce((s, p) => s + p.x, 0) / c.points.length
  const cy = c.points.reduce((s, p) => s + p.y, 0) / c.points.length
  return { ...c, x: sx(cx), y: sy(cy) }
})

export default function ClusterAnimation() {
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="cluster-anim"
      role="img"
      aria-label="Animación de clientes agrupándose en clusters"
    >
      {centers.map((c, i) => (
        <g key={c.id}>
          <circle
            className="anim-halo"
            style={{ animationDelay: `${(1.4 + i * 0.18).toFixed(2)}s` }}
            cx={c.x}
            cy={c.y}
            r={62}
            fill={c.color}
          />
        </g>
      ))}
      {flat.map((p, i) => (
        <circle
          key={i}
          className="anim-point"
          style={{ animationDelay: `${(i * 0.05).toFixed(2)}s` }}
          cx={sx(p.x)}
          cy={sy(p.y)}
          r={5}
          fill={p.color}
        />
      ))}
      {centers.map((c, i) => (
        <text
          key={c.id}
          className="anim-label"
          style={{ animationDelay: `${(1.9 + i * 0.18).toFixed(2)}s` }}
          x={c.x}
          y={c.y - 70}
          textAnchor="middle"
          fill="#344054"
        >
          {c.name}
        </text>
      ))}
    </svg>
  )
}
