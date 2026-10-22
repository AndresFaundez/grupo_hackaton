import ChatPanel from '../components/ChatPanel.jsx'

export default function Chat() {
  return (
    <section className="chat-section">
      <h2>Chat IA</h2>
      <p className="lead">
        Conversa sobre los clusters para pedir estrategias y más información.
      </p>
      <div className="card chat-wrap">
        <ChatPanel />
      </div>
    </section>
  )
}
