import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import ChatPanel from './components/ChatPanel.jsx'

const mainScreens = [
  { to: '/recorrido', label: 'Recorrido' },
  { to: '/base-de-datos', label: 'Base de datos' },
  { to: '/chat', label: 'Chat IA' },
]

const steps = [
  { to: '/recorrido', label: 'Datos', end: true },
  { to: '/recorrido/procesando', label: 'Procesamiento' },
  { to: '/recorrido/clusters', label: 'Clusters' },
  { to: '/recorrido/explorar', label: 'Exploración' },
  { to: '/recorrido/campana', label: 'Campaña' },
]

export default function Layout() {
  const [chatOpen, setChatOpen] = useState(false)
  const { pathname } = useLocation()
  const inFlow = pathname.startsWith('/recorrido')

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <NavLink to="/recorrido" className="brand-link">
            <span className="brand">Segmenta</span>
          </NavLink>
          <span className="proto-badge">PROTOTIPO · DATOS DE DEMOSTRACIÓN</span>
          <nav className="main-nav" aria-label="Pantallas principales">
            {mainScreens.map((screen) => (
              <NavLink
                key={screen.to}
                to={screen.to}
                end={screen.to === '/recorrido' ? false : undefined}
                className={({ isActive }) =>
                  'main-tab' + (isActive ? ' active' : '')
                }
              >
                {screen.label}
              </NavLink>
            ))}
          </nav>
          <button
            className="ask-ai"
            onClick={() => setChatOpen(true)}
            aria-expanded={chatOpen}
          >
            Preguntar a la IA
          </button>
        </div>

        {inFlow && (
          <nav className="steps-nav" aria-label="Recorrido">
            {steps.map((step, index) => (
              <NavLink
                key={step.to}
                to={step.to}
                end={step.end}
                className={({ isActive }) =>
                  'step' + (isActive ? ' active' : '')
                }
              >
                <span className="step-number">{index + 1}</span>
                <span className="step-label">{step.label}</span>
              </NavLink>
            ))}
          </nav>
        )}
        <span className="sr-only" aria-live="polite">{pathname}</span>
      </header>

      <main className="content">
        <Outlet />
      </main>

      {chatOpen && (
        <div className="chat-drawer-backdrop" onClick={() => setChatOpen(false)}>
          <aside
            className="chat-drawer"
            role="dialog"
            aria-label="Chat con los datos"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="chat-drawer-head">
              <strong>Chat con los datos</strong>
              <button className="icon-button" onClick={() => setChatOpen(false)} aria-label="Cerrar chat">
                ×
              </button>
            </div>
            <ChatPanel compact />
          </aside>
        </div>
      )}
    </div>
  )
}
