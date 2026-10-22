import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'
import { channels, objectives } from '../lib/campaign.js'
import { useSegmentation } from '../context/Segmentation.jsx'

const nextStepChips = [
  { id: 'lanzar', label: 'Lanzar campaña' },
  { id: 'regenerar', label: 'Generar otra versión' },
]

// Ventana conversacional para definir y lanzar una campaña sobre un segmento.
// Los borradores los genera la IA con los datos agregados del segmento.
export default function CampaignChat({ cluster }) {
  const { clusteringId } = useSegmentation()
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
  const [input, setInput] = useState('')
  const [selection, setSelection] = useState({ objetivo: null, canal: null })
  const [draft, setDraft] = useState(null)
  const [pending, setPending] = useState(false)
  const listRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, pending])

  const push = (msg) => setMessages((prev) => [...prev, msg])
  const pushUser = (text) => push({ role: 'user', text })
  const clearChips = () =>
    setMessages((prev) =>
      prev.map((m, i) => (i === prev.length - 1 && m.chips ? { ...m, chips: null } : m)),
    )

  const requestDraft = async ({ objetivo, canal, instructions, previous }) => {
    setPending(true)
    try {
      const result = await api.campaignDraft(clusteringId, cluster.clusterId, {
        objective: objetivo,
        channel: canal,
        instructions: instructions ?? null,
        previous_message: previous ?? null,
      })
      setDraft(result)
      push({
        role: 'assistant',
        text: previous || instructions ? 'Aquí va otra versión:' : 'Este es el borrador del mensaje:',
        draft: result,
      })
      push({ role: 'assistant', text: '¿Lo lanzamos o genero otra versión? También puedes escribirme ajustes.', chips: nextStepChips })
    } catch (e) {
      push({ role: 'assistant', text: e.message, error: true, chips: nextStepChips.slice(1) })
    } finally {
      setPending(false)
    }
  }

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
    const next = { ...selection, canal: c.id }
    setSelection(next)
    requestDraft(next)
  }

  const launch = () => {
    clearChips()
    pushUser('Lanzar campaña')
    const canalLabel = channels.find((c) => c.id === selection.canal)?.label
    const objetivoLabel = objectives.find((o) => o.id === selection.objetivo)?.label
    push({
      role: 'assistant',
      text: `Campaña lista para los ${cluster.customers.toLocaleString('es-CL')} clientes de «${cluster.name}» por ${canalLabel}.`,
      card: {
        segmento: cluster.name,
        objetivo: objetivoLabel,
        canal: canalLabel,
        asunto: draft?.subject,
        mensaje: draft?.message,
      },
    })
  }

  const regenerate = (instructions) => {
    clearChips()
    pushUser(instructions ?? 'Generar otra versión')
    requestDraft({ ...selection, instructions, previous: draft?.message })
  }

  const onChip = (chip) => {
    if (pending) return
    if (chip.id === 'lanzar') return launch()
    if (chip.id === 'regenerar') return regenerate()
    if (selection.objetivo === null) return pickObjective(objectives.find((o) => o.id === chip.id))
    if (selection.canal === null) return pickChannel(channels.find((c) => c.id === chip.id))
  }

  const send = (text) => {
    const trimmed = text.trim()
    if (!trimmed || pending) return
    setInput('')
    if (!selection.objetivo || !selection.canal) {
      pushUser(trimmed)
      push({ role: 'assistant', text: 'Primero elige el objetivo y el canal con las opciones de arriba; después ajusto el mensaje como me digas.' })
      return
    }
    regenerate(trimmed)
  }

  return (
    <div className="chat campaign-chat">
      <div className="chat-messages" ref={listRef}>
        {messages.map((message, index) => (
          <div key={index} style={{ display: 'contents' }}>
            <div className={`bubble ${message.role}${message.error ? ' error' : ''}`}>
              {message.text}
              {message.draft && (
                <blockquote className="draft-message">
                  {message.draft.subject && <strong className="d-block">Asunto: {message.draft.subject}</strong>}
                  {message.draft.message}
                </blockquote>
              )}
              {message.draft?.rationale && <p className="muted small draft-rationale">{message.draft.rationale}</p>}
              {message.card && (
                <div className="campaign-summary">
                  <p><span className="review-label">Segmento</span> {message.card.segmento}</p>
                  <p><span className="review-label">Objetivo</span> {message.card.objetivo}</p>
                  <p><span className="review-label">Canal</span> {message.card.canal}</p>
                  {message.card.asunto && <p><span className="review-label">Asunto</span> {message.card.asunto}</p>}
                  <blockquote className="review-message">{message.card.mensaje}</blockquote>
                  <a className="link-button strong" href={api.audienceUrl(clusteringId, cluster.clusterId)}>
                    Descargar audiencia (CSV)
                  </a>
                  <p className="sim-note">SIMULACIÓN — el envío real se conectará a la herramienta de mensajería.</p>
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
                    disabled={pending}
                  >
                    {chip.label}
                    {chip.suggested && <span className="suggested">SUGERIDO</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {pending && <div className="bubble assistant typing">Escribiendo el mensaje…</div>}
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
        <button className="primary" type="submit" disabled={pending}>Enviar</button>
      </form>
    </div>
  )
}
