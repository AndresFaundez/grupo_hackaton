import { useRef, useState } from 'react'

const defaultIntro =
  'Hola. Tengo la información de la segmentación de clientes: puedo contarte sobre los clusters, sus patrones de compra y ayudarte a definir estrategias de marketing. ¿Qué quieres saber?'

export default function ChatPanel({ intro = defaultIntro, compact = false }) {
  const [messages, setMessages] = useState([{ role: 'assistant', text: intro }])
  const [input, setInput] = useState('')
  const listRef = useRef(null)

  const suggestions = [
    '¿Qué cluster genera más ingresos?',
    'Dame una estrategia para clientes infrecuentes',
    '¿Qué compran los clientes premium?',
  ]

  const send = (text) => {
    const trimmed = text.trim()
    if (!trimmed) return
    setMessages((prev) => [
      ...prev,
      { role: 'user', text: trimmed },
      {
        role: 'assistant',
        text: 'Esta demo aún no está conectada al LLM. Cuando el backend publique su contrato, esta conversación consultará la información de los clusters y, cuando haga falta, la base de datos filtrada por el cluster del que se hable.',
      },
    ])
    setInput('')
    requestAnimationFrame(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
    })
  }

  return (
    <div className="chat">
      <div className="chat-messages" ref={listRef}>
        {messages.map((message, index) => (
          <div className={`bubble ${message.role}`} key={index}>
            {message.text}
          </div>
        ))}
      </div>

      {!compact && (
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button className="chip chip-button" key={s} onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

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
          placeholder="Pregunta sobre tus clientes…"
          aria-label="Mensaje"
        />
        <button className="primary" type="submit">Enviar</button>
      </form>
    </div>
  )
}
