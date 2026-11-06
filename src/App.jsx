import { useCallback, useEffect, useMemo, useState } from 'react'
import AgentChat from './components/AgentChat'
import ContactList from './components/ContactList'
import ImportCard from './components/ImportCard'
import { deleteContact, importContacts, listContacts } from './api'

export default function App() {
  const [contacts, setContacts] = useState([])
  const [query, setQuery] = useState('')
  const [notice, setNotice] = useState(null)
  const [importing, setImporting] = useState(false)

  const refresh = useCallback(async () => {
    const data = await listContacts()
    setContacts(data.contacts)
  }, [])

  useEffect(() => {
    refresh().catch(() => setNotice({ type: 'error', text: 'Impossible de charger les contacts.' }))
  }, [refresh])

  const handleImport = async (file) => {
    setImporting(true)
    setNotice(null)
    try {
      const result = await importContacts(file)
      await refresh()
      const parts = [`${result.imported} contact(s) importé(s)`]
      if (result.skipped) parts.push(`${result.skipped} doublon(s) ignoré(s)`)
      parts.push(`${result.total} au total`)
      setNotice({ type: 'success', text: parts.join(' · ') })
    } catch (error) {
      setNotice({ type: 'error', text: error.message })
    } finally {
      setImporting(false)
    }
  }

  const handleDelete = async (id) => {
    await deleteContact(id)
    await refresh()
  }

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return contacts
    return contacts.filter((contact) =>
      [contact.name, contact.email, contact.phone, contact.company, contact.tags]
        .join(' ')
        .toLowerCase()
        .includes(term),
    )
  }, [contacts, query])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">MC</span>
          <div>
            <h1>Mind Clasher</h1>
            <p>Tes contacts, branchés sur ton superagent.</p>
          </div>
        </div>
        <span className="pill">{contacts.length} contact(s) connecté(s)</span>
      </header>

      <main className="layout">
        <section className="panel">
          <ImportCard onImport={handleImport} busy={importing} notice={notice} />
          <ContactList
            contacts={filtered}
            total={contacts.length}
            query={query}
            onQueryChange={setQuery}
            onDelete={handleDelete}
          />
        </section>
        <AgentChat contactCount={contacts.length} />
      </main>
    </div>
  )
}
