import ChatPanel from '../components/ChatPanel.jsx'

export default function ChatIA() {
  return (
    <section className="chat-page">
      <h2>Chat IA</h2>
      <p className="lead">
        Conversa con la IA sobre tus clientes: clusters, patrones de compra y
        estrategias. Tiene la información de la segmentación y puede consultar
        la base de datos filtrada por cluster.
      </p>
      <div className="card chat-wrap tall">
        <ChatPanel />
      </div>
    </section>
  )
}
