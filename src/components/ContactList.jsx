export default function ContactList({ contacts, total, query, onQueryChange, onDelete }) {
  return (
    <section className="card card--grow">
      <div className="card-head">
        <h2>Mes contacts</h2>
        <span className="count">{total}</span>
      </div>

      <input
        className="input"
        type="search"
        placeholder="Rechercher un nom, une entreprise, un email…"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
      />

      {total === 0 && (
        <p className="empty">
          Aucun contact pour l'instant. Importe un fichier CSV ou vCard pour les connecter au superagent.
        </p>
      )}

      {total > 0 && contacts.length === 0 && <p className="empty">Aucun contact ne correspond à cette recherche.</p>}

      <ul className="contact-list">
        {contacts.map((contact) => (
          <li key={contact.id} className="contact">
            <div className="avatar">{(contact.name || contact.email || '?').slice(0, 1).toUpperCase()}</div>
            <div className="contact-body">
              <p className="contact-name">{contact.name || 'Sans nom'}</p>
              <p className="contact-meta">
                {[contact.company, contact.email, contact.phone].filter(Boolean).join(' · ') || 'Aucune coordonnée'}
              </p>
            </div>
            <button
              type="button"
              className="icon-button"
              title="Retirer ce contact"
              aria-label={`Retirer ${contact.name || 'ce contact'}`}
              onClick={() => onDelete(contact.id)}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
