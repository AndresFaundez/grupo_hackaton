import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { clusters, customers } from '../data/demoClusters.js'
import { formatCLP, formatNumber } from '../lib/format.js'
import { useClusterNames } from '../context/ClusterNames.jsx'

const columns = [
  { key: 'id', label: 'Cliente' },
  { key: 'cluster', label: 'Cluster' },
  { key: 'spend', label: 'Gasto total', sortable: true },
  { key: 'frequency', label: 'Frecuencia/año', sortable: true },
  { key: 'lastPurchase', label: 'Última compra', sortable: true },
]

export default function BaseDatos() {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [sort, setSort] = useState({ key: 'spend', dir: 'desc' })
  const [selectedId, setSelectedId] = useState(null)
  const { names } = useClusterNames()

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return customers
      .filter((c) => filter === 'all' || c.cluster === filter)
      .filter((c) => !q || c.name.toLowerCase().includes(q) || c.id.toLowerCase().includes(q))
      .sort((a, b) => (sort.dir === 'asc' ? 1 : -1) * (a[sort.key] > b[sort.key] ? 1 : a[sort.key] < b[sort.key] ? -1 : 0))
  }, [query, filter, sort])

  const selected = customers.find((c) => c.id === selectedId) || rows[0]
  const selectedCluster = clusters.find((c) => c.id === selected?.cluster)
  const totalSpend = rows.reduce((s, c) => s + c.spend, 0)

  const toggleSort = (key) => {
    setSort((s) =>
      s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' },
    )
  }

  return (
    <section>
      <h2>Base de datos</h2>
      <p className="lead">
        Explora los clientes con la segmentación ya integrada: cada fila
        muestra a qué cluster pertenece y su contexto de compra.
      </p>

      <div className="db-toolbar">
        <input
          type="search"
          className="db-search"
          placeholder="Buscar por nombre o id de cliente…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Buscar cliente"
        />
        <div className="db-filters">
          <button
            className={filter === 'all' ? 'chip chip-button selected' : 'chip chip-button'}
            onClick={() => setFilter('all')}
          >
            Todos
          </button>
          {clusters.map((c) => (
            <button
              key={c.id}
              className={filter === c.id ? 'chip chip-button selected' : 'chip chip-button'}
              onClick={() => setFilter(c.id)}
            >
              <span className="cluster-dot" style={{ background: c.color }} aria-hidden="true" />
              {names[c.id]}
            </button>
          ))}
        </div>
      </div>

      <p className="db-count">
        {formatNumber(rows.length)} clientes · gasto agregado {formatCLP(totalSpend)}
      </p>

      <div className="db-layout">
        <div className="card db-table-wrap">
          <table className="db-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key}>
                    {col.sortable ? (
                      <button
                        className={
                          sort.key === col.key ? 'sort-head active' : 'sort-head'
                        }
                        onClick={() => toggleSort(col.key)}
                      >
                        {col.label}
                        <span className="sort-arrow" aria-hidden="true">
                          {sort.key === col.key ? (sort.dir === 'asc' ? '↑' : '↓') : '↕'}
                        </span>
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => {
                const cluster = clusters.find((x) => x.id === c.cluster)
                return (
                  <tr
                    key={c.id}
                    className={selected?.id === c.id ? 'selected' : ''}
                    onClick={() => setSelectedId(c.id)}
                  >
                    <td>
                      <strong>{c.id}</strong>
                      <span className="muted d-block">{c.name}</span>
                    </td>
                    <td>
                      <span className="cluster-dot" style={{ background: cluster.color }} aria-hidden="true" />{' '}
                      {names[c.cluster]}
                    </td>
                    <td>{formatCLP(c.spend)}</td>
                    <td>{c.frequency.toString().replace('.', ',')}</td>
                    <td>hace {c.lastPurchase} días</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {rows.length === 0 && <p className="db-empty">Sin resultados para esa búsqueda.</p>}
        </div>

        {selected && selectedCluster && (
          <aside className="card db-detail">
            <h3>
              {selected.id} · {selected.name}
            </h3>
            <div className="badges">
              <span className="badge" style={{ color: selectedCluster.color }}>
                <span className="cluster-dot" style={{ background: selectedCluster.color }} aria-hidden="true" />{' '}
                {names[selected.cluster]}
              </span>
            </div>
            <div className="detail-grid">
              <div className="detail-item">
                <h4>Gasto total</h4>
                <p className="stat-value">{formatCLP(selected.spend)}</p>
              </div>
              <div className="detail-item">
                <h4>Frecuencia</h4>
                <p className="stat-value">
                  {selected.frequency.toString().replace('.', ',')} compras/año
                </p>
              </div>
              <div className="detail-item">
                <h4>Última compra</h4>
                <p className="stat-value">hace {selected.lastPurchase} días</p>
              </div>
            </div>
            <p className="muted">{selectedCluster.description}</p>
            <Link className="link-button strong" to={`/recorrido/explorar?segmento=${selected.cluster}`}>
              Ver su segmento →
            </Link>
          </aside>
        )}
      </div>
    </section>
  )
}
