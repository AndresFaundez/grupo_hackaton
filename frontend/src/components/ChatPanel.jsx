import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client.js'
import { useSegmentation } from '../context/Segmentation.jsx'
import Markdown from './Markdown.jsx'

const defaultIntro =
  'Hola. Tengo la información de la segmentación de clientes: puedo contarte sobre los clusters, sus patrones de compra y ayudarte a definir estrategias de marketing. ¿Qué quieres saber?'

const defaultSuggestions = [
  '¿Qué cluster genera más ingresos?',
  '¿Qué clientes valiosos están dejando de comprar?',
  '¿En qué se diferencian los dos clusters más grandes?',
]

const TOOL_LABELS = {
  describe_cluster: 'Perfil del cluster',
  compare_clusters: 'Comparación de clusters',
  query_data: 'Consulta SQL',
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
        <a key={a.handle} className="link-button strong" href={api.resultUrl(a.handle)}>
          Descargar {a.title ?? 'lista'} ({a.count} clientes)
        </a>
      ))}
    </div>
  )
}

// Chat con la segmentación. `clusterId` acota la conversación al cluster seleccionado.
export default function ChatPanel({ intro = defaultIntro, compact = false, clusterId = null, suggestions }) {
  const { clusteringId } = useSegmentation()
  const [messages, setMessages] = useState([{ role: 'assistant', text: intro }])
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
        { role: 'assistant', text: 'Primero carga una base de datos para que pueda responder sobre tus clientes.' },
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

  return (
    <div className="chat">
      <div className="chat-messages" ref={listRef}>
        {messages.map((message, index) => (
          <div className={`bubble ${message.role}${message.error ? ' error' : ''}`} key={index}>
            {message.role === 'assistant' && !message.error ? <Markdown text={message.text} /> : message.text}
            <Attachments items={message.attachments} />
            <ToolTrace calls={message.tools} />
          </div>
        ))}
        {pending && (
          <div className="bubble assistant typing" aria-live="polite">
            Analizando tus datos…
          </div>
        )}
      </div>

      {(!compact || messages.length === 1) && (
        <div className="chat-suggestions">
          {chips.map((s) => (
            <button className="chip chip-button" key={s} onClick={() => send(s)} disabled={pending}>
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
        <button className="primary" type="submit" disabled={pending}>
          Enviar
        </button>
      </form>
    </div>
  )
}
