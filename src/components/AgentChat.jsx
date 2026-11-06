import { useState } from 'react'
import { askAgent } from '../api'

const SUGGESTIONS = [
  'Combien de contacts ?',
  'Quels sont les doublons ?',
  'Les contacts sans email',
  'Répartition par entreprise',
]

const WELCOME = {
  role: 'agent',
  text: "Salut, je suis ton superagent. Importe tes contacts et pose-moi une question : je réponds à partir de tes données.",
}

export default function AgentChat({ contactCount }) {
  const [messages, setMessages] = useState([WELCOME])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)

  const send = async (text) => {
    const question = (text ?? draft).trim()
    if (!question || busy) return
    setDraft('')
    setMessages((current) => [...current, { role: 'user', text: question }])
    setBusy(true)
    try {
      const result = await askAgent(question)
      setMessages((current) => [...current, { role: 'agent', text: result.answer, mode: result.mode }])
    } catch (error) {
      setMessages((current) => [...current, { role: 'agent', text: error.message, error: true }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel panel--agent">
      <div className="agent-head">
        <div>
          <h2>Superagent</h2>
          <p className="muted">
            {contactCount > 0 ? `${contactCount} contact(s) dans son contexte` : 'En attente de contacts'}
          </p>
        </div>
        <span className="badge">connecté</span>
      </div>

      <div className="chat">
        {messages.map((message, index) => (
          <div key={index} className={`bubble bubble--${message.role}${message.error ? ' bubble--error' : ''}`}>
            <p className="bubble-text">{message.text}</p>
            {message.mode && <span className="bubble-tag">{message.mode === 'llm' ? 'modèle externe' : 'moteur local'}</span>}
          </div>
        ))}
        {busy && <div className="bubble bubble--agent bubble--typing">Le superagent réfléchit…</div>}
      </div>

      <div className="suggestions">
        {SUGGESTIONS.map((suggestion) => (
          <button key={suggestion} type="button" className="chip" disabled={busy} onClick={() => send(suggestion)}>
            {suggestion}
          </button>
        ))}
      </div>

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault()
          send()
        }}
      >
        <input
          className="input"
          value={draft}
          placeholder="Demande quelque chose sur tes contacts…"
          onChange={(event) => setDraft(event.target.value)}
          aria-label="Question au superagent"
        />
        <button type="submit" className="button" disabled={busy || !draft.trim()}>
          Envoyer
        </button>
      </form>
    </section>
  )
}
