import { clusterColor } from '../api/adapter.js'

const W = 800
const H = 400
const PAD = 40

// Animación decorativa: los clientes "caen" al lienzo y se agrupan en
// clusters que emergen con su halo. No son datos reales.
const groups = [
  { x: 0.25, y: 0.7, n: 14 },
  { x: 0.72, y: 0.25, n: 9 },
  { x: 0.6, y: 0.68, n: 12 },
  { x: 0.2, y: 0.3, n: 11 },
]

const centers = groups.map((g, i) => ({
  id: i,
  color: clusterColor(i),
  x: PAD + g.x * (W - 2 * PAD),
  y: PAD + g.y * (H - 2 * PAD),
  label: `Grupo ${i + 1}`,
}))

const flat = groups.flatMap((g, gi) =>
  Array.from({ length: g.n }, (_, i) => {
    const a = (i / g.n) * Math.PI * 2
    const jx = ((i * 7919) % 97) / 97 - 0.5
    const jy = ((i * 104729) % 89) / 89 - 0.5
    return {
      x: centers[gi].x + Math.cos(a) * 38 + jx * 30,
      y: centers[gi].y + Math.sin(a) * 30 + jy * 24,
      color: centers[gi].color,
    }
  }),
)

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
          cx={p.x}
          cy={p.y}
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
          {c.label}
        </text>
      ))}
    </svg>
  )
}
