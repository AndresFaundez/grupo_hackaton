import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'
import { useSegmentation } from '../context/Segmentation.jsx'
import Markdown from './Markdown.jsx'
import Icon from './Icon.jsx'

const defaultIntro =
  'Hola. Conozco a todos tus segmentos de clientes: qué compran, cada cuánto y cuánto gastan. Pregúntame lo que necesites para decidir tu próxima campaña.'

const defaultSuggestions = [
  '¿Qué segmento me deja más ventas?',
  '¿Qué clientes valiosos están dejando de comprar?',
  '¿En qué se diferencian mis dos segmentos más grandes?',
]

const TOOL_LABELS = {
  describe_cluster: 'Perfil del segmento',
  compare_clusters: 'Comparación de segmentos',
  query_data: 'Consulta a tus datos',
  explain_customer: 'Explicación de un cliente',
  list_customers: 'Lista de clientes',
}

function ToolTrace({ calls }) {
  if (!calls?.length) return null
  return (
    <details className="chat-tools">
      <summary>Cómo lo calculé ({calls.length})</summary>
      <ul>
        {calls.map((call, i) => (
          <li key={i}>
            <strong>{TOOL_LABELS[call.name] ?? call.name}</strong>
            {call.error && <span className="tool-error"> · error: {call.error}</span>}
            {call.result_preview?.sql ? (
              <code className="d-block">{call.result_preview.sql}</code>
            ) : (
              <span className="muted"> {JSON.stringify(call.args)}</span>
            )}
          </li>
        ))}
      </ul>
    </details>
  )
}

function Attachments({ items }) {
  const lists = (items ?? []).filter((a) => a.type === 'customer_list')
  if (!lists.length) return null
  return (
    <div className="chat-attachments">
      {lists.map((a) => (
        <a key={a.handle} className="download-link" href={api.resultUrl(a.handle)}>
          <Icon name="download" size={16} />
          Descargar {a.title ?? 'lista'} ({a.count} clientes)
        </a>
      ))}
    </div>
  )
}

// Chat con la segmentación. `clusterId` acota la conversación al segmento seleccionado.
export default function ChatPanel({ intro = defaultIntro, clusterId = null, suggestions }) {
  const { clusteringId, aiEnabled } = useSegmentation()
  const [messages, setMessages] = useState([{ role: 'assistant', text: intro }])
  const disabled = aiEnabled === false
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [pending, setPending] = useState(false)
  const listRef = useRef(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, pending])

  const send = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || pending) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: trimmed }])

    if (!clusteringId) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Primero carga tus ventas para que pueda responder sobre tus clientes.' },
      ])
      return
    }

    setPending(true)
    try {
      const response = await api.chat(clusteringId, {
        message: trimmed,
        session_id: sessionId,
        cluster_ids: clusterId != null ? [clusterId] : [],
      })
      setSessionId(response.session_id)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: response.answer, tools: response.tool_calls, attachments: response.attachments },
      ])
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', text: e.message, error: true }])
    } finally {
      setPending(false)
    }
  }

  const chips = suggestions?.length ? suggestions : defaultSuggestions
  const asked = messages.some((m) => m.role === 'user')

  return (
    <div className="chat">
      <div className="chat-messages" ref={listRef} aria-live="polite">
        {messages.map((message, index) => (
          <div className={`bubble ${message.role}${message.error ? ' error' : ''}`} key={index}>
            {message.role === 'assistant' && !message.error ? <Markdown text={message.text} /> : message.text}
            <Attachments items={message.attachments} />
            <ToolTrace calls={message.tools} />
          </div>
        ))}
        {pending && (
          <div className="bubble assistant typing">
            <span className="typing-dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            Analizando tus datos…
          </div>
        )}
      </div>

      {disabled && (
        <p className="chat-notice">
          <Icon name="alert" size={16} />
          <span>
            El asistente necesita IA. Pega una clave gratuita de Gemini en <code>backend/.env</code>{' '}
            (<code>GEMINI_API_KEY</code>) y vuelve a abrir la página con «Abrir hackaton».
          </span>
        </p>
      )}

      {!asked && !disabled && (
        <div className="chat-suggestions">
          {chips.map((s) => (
            <button className="chip-button" key={s} onClick={() => send(s)} disabled={pending}>
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
          placeholder={disabled ? 'Asistente desactivado' : 'Escribe tu pregunta…'}
          aria-label="Mensaje"
          disabled={disabled}
        />
        <button className="send-button" type="submit" aria-label="Enviar" disabled={disabled || pending || !input.trim()}>
          <Icon name="send" size={18} />
        </button>
      </form>
    </div>
  )
}
