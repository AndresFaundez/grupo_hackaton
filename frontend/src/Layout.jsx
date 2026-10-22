import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { Fragment, useEffect, useState } from 'react'
import ChatPanel from './components/ChatPanel.jsx'
import Icon, { BrandMark } from './components/Icon.jsx'
import { useSegmentation } from './context/Segmentation.jsx'

const steps = [
  { to: '/', label: 'Tus datos', end: true },
  { to: '/procesando', label: 'Análisis' },
  { to: '/clusters', label: 'Segmentos' },
  { to: '/explorar', label: 'Explorar' },
  { to: '/campana', label: 'Campaña' },
]

export default function Layout() {
  const [chatOpen, setChatOpen] = useState(false)
  const { pathname } = useLocation()
  const current = steps.findIndex((s) => s.to === pathname)
  const { dataset, status } = useSegmentation()
  const badge = dataset ? dataset.fileName : status === 'processing' ? 'Analizando…' : null

  useEffect(() => {
    if (!chatOpen) return
    const onKey = (event) => event.key === 'Escape' && setChatOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [chatOpen])

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [pathname])

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <NavLink to="/" className="brand-link" aria-label="Segmenta, inicio">
            <BrandMark />
            <span className="brand">Segmenta</span>
            {badge && (
              <span className="data-pill" title={badge}>
                {badge}
              </span>
            )}
          </NavLink>

          <nav className="stepper" aria-label="Recorrido">
            {steps.map((step, index) => (
              <Fragment key={step.to}>
                {index > 0 && (
                  <span
                    className={'step-line' + (index <= current ? ' filled' : '')}
                    aria-hidden="true"
                  />
                )}
                <NavLink
                  to={step.to}
                  end={step.end}
                  className={({ isActive }) =>
                    'step' + (isActive ? ' active' : index < current ? ' done' : '')
                  }
                >
                  <span className="step-dot">
                    {index < current ? <Icon name="check" size={12} strokeWidth={2.4} /> : index + 1}
                  </span>
                  <span className="step-label">{step.label}</span>
                </NavLink>
              </Fragment>
            ))}
          </nav>

          <button
            className="ask-ai"
            onClick={() => setChatOpen(true)}
            aria-expanded={chatOpen}
          >
            <Icon name="sparkle" size={16} />
            <span>Pregúntale a la IA</span>
          </button>
        </div>
      </header>

      <main className="content">
        <Outlet />
      </main>

      {chatOpen && (
        <div className="chat-drawer-backdrop" onClick={() => setChatOpen(false)}>
          <aside
            className="chat-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Asistente IA"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="chat-drawer-head">
              <span className="ai-avatar" aria-hidden="true">
                <Icon name="sparkle" size={18} />
              </span>
              <div>
                <strong>Asistente IA</strong>
                <span className="muted small d-block">
                  Conoce tus segmentos y te ayuda a decidir
                </span>
              </div>
              <button
                className="icon-button"
                onClick={() => setChatOpen(false)}
                aria-label="Cerrar asistente"
              >
                <Icon name="close" size={20} />
              </button>
            </div>
            <ChatPanel />
          </aside>
        </div>
      )}
    </div>
  )
}
