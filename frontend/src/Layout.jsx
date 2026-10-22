import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState } from 'react'
import ChatPanel from './components/ChatPanel.jsx'

const steps = [
  { to: '/', label: 'Datos', end: true },
  { to: '/procesando', label: 'Procesamiento' },
  { to: '/clusters', label: 'Clusters' },
  { to: '/explorar', label: 'Exploración' },
  { to: '/campana', label: 'Campaña' },
]

export default function Layout() {
  const [chatOpen, setChatOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <NavLink to="/" className="brand-link">
            <span className="brand">Segmenta</span>
          </NavLink>
          <span className="proto-badge">PROTOTIPO · DATOS DE DEMOSTRACIÓN</span>
          <button
            className="ask-ai"
            onClick={() => setChatOpen(true)}
            aria-expanded={chatOpen}
          >
            Preguntar a la IA
          </button>
        </div>
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
