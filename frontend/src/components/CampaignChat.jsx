import { useState } from 'react'
import { campaignDrafts, channels, objectives } from '../data/demoClusters.js'

// Ventana conversacional para definir y lanzar una campaña sobre un segmento.
// La conversación está guionizada en demo; el LLM real reemplazará las
// respuestas cuando el backend publique su contrato.
export default function CampaignChat({ cluster }) {
  const [messages, setMessages] = useState(() => [
    {
      role: 'assistant',
      text: `Prepararemos una campaña para «${cluster.name}» (${cluster.customers.toLocaleString('es-CL')} clientes). ¿Cuál es el objetivo?`,
      chips: objectives.map((o) => ({
        id: o.id,
        label: o.label,
        suggested: cluster.suggestedObjective === o.id,
      })),
    },
  ])
  const [draftIndex, setDraftIndex] = useState(0)
  const [input, setInput] = useState('')
  const [selection, setSelection] = useState({ objetivo: null, canal: null })

  const push = (msg) => setMessages((prev) => [...prev, msg])
  const pushUser = (text) => push({ role: 'user', text })
  const clearChips = () =>
    setMessages((prev) =>
      prev.map((m, i) => (i === prev.length - 1 && m.chips ? { ...m, chips: null } : m)),
    )

  const pickObjective = (o) => {
    clearChips()
    pushUser(o.label)
    setSelection((s) => ({ ...s, objetivo: o.id }))
    push({
      role: 'assistant',
      text: '¿Y por cuál canal la enviamos?',
      chips: channels.map((c) => ({ id: c.id, label: c.label })),
    })
  }

  const pickChannel = (c) => {
    clearChips()
    pushUser(c.label)
    setSelection((s) => ({ ...s, canal: c.id }))
    showDraft()
  }

  const showDraft = () => {
    const draft = campaignDrafts[selection.objetivo][draftIndex]
    push({ role: 'assistant', text: 'Este es el borrador del mensaje:', draft })
    push({
      role: 'assistant',
      text: '¿Lo lanzamos o genero otra versión?',
      chips: [
        { id: 'lanzar', label: 'Lanzar campaña' },
        { id: 'regenerar', label: 'Generar otra versión' },
      ],
    })
  }

  const launch = () => {
    clearChips()
    pushUser('Lanzar campaña')
    const canalLabel = channels.find((c) => c.id === selection.canal)?.label
    const objetivoLabel = objectives.find((o) => o.id === selection.objetivo)?.label
    push({
      role: 'assistant',
      text: `Campaña lanzada a los ${cluster.customers.toLocaleString('es-CL')} clientes de «${cluster.name}» por ${canalLabel}. Te aviso cuando tengamos los primeros resultados.`,
      card: {
        segmento: cluster.name,
        objetivo: objetivoLabel,
        canal: canalLabel,
        mensaje: campaignDrafts[selection.objetivo][draftIndex],
      },
    })
  }

  const regenerate = () => {
    clearChips()
    pushUser('Generar otra versión')
    const next = draftIndex + 1
    setDraftIndex(next)
    const draft = campaignDrafts[selection.objetivo][next % campaignDrafts[selection.objetivo].length]
    push({ role: 'assistant', text: 'Aquí va otra versión:', draft })
    push({
      role: 'assistant',
      text: '¿La lanzamos?',
      chips: [
        { id: 'lanzar', label: 'Lanzar campaña' },
        { id: 'regenerar', label: 'Generar otra versión' },
      ],
    })
  }

  const onChip = (chip) => {
    if (chip.id === 'lanzar') return launch()
    if (chip.id === 'regenerar') return regenerate()
    if (selection.objetivo === null) return pickObjective(objectives.find((o) => o.id === chip.id))
    if (selection.canal === null) return pickChannel(channels.find((c) => c.id === chip.id))
  }

  const send = (text) => {
    const trimmed = text.trim()
    if (!trimmed) return
    pushUser(trimmed)
    push({
      role: 'assistant',
      text: 'En la versión conectada al LLM podré ajustar el mensaje con tus indicaciones. Por ahora usa las opciones rápidas de abajo.',
    })
    setInput('')
  }

  return (
    <div className="chat campaign-chat">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} style={{ display: 'contents' }}>
            <div className={`bubble ${message.role}`}>
              {message.text}
              {message.draft && <blockquote className="draft-message">{message.draft}</blockquote>}
              {message.card && (
                <div className="campaign-summary">
                  <p><span className="review-label">Segmento</span> {message.card.segmento}</p>
                  <p><span className="review-label">Objetivo</span> {message.card.objetivo}</p>
                  <p><span className="review-label">Canal</span> {message.card.canal}</p>
                  <blockquote className="review-message">{message.card.mensaje}</blockquote>
                  <p className="sim-note">SIMULACIÓN — el envío real quedará conectado al backend.</p>
                </div>
              )}
            </div>
            {message.chips && (
              <div className="chat-suggestions">
                {message.chips.map((chip) => (
                  <button
                    key={chip.id}
                    className="chip chip-button"
                    onClick={() => onChip(chip)}
                  >
                    {chip.label}
                    {chip.suggested && <span className="suggested">SUGERIDO</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        className="chat-input"
        onSubmit={(event) => {
          event.preventDefault()
          send(input)
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Escribe una indicación para la campaña…"
          aria-label="Mensaje"
        />
        <button className="primary" type="submit">Enviar</button>
      </form>
    </div>
  )
}
