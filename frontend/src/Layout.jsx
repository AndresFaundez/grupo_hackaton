import { NavLink, Outlet } from 'react-router-dom'

const tabs = [
  { to: '/upload', label: 'Subir datos' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/clusters', label: 'Clusters' },
  { to: '/chat', label: 'Chat IA' },
]

export default function Layout() {
  return (
    <div className="app">
      <header className="header">
        <h1 className="brand">Segmentación de Clientes</h1>
        <nav className="tabs">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) => (isActive ? 'tab active' : 'tab')}
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
