import { useRef, useState } from 'react'

export default function ImportCard({ onImport, busy, notice }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const pick = (files) => {
    const file = files && files[0]
    if (file) onImport(file)
  }

  return (
    <section className="card">
      <h2>Importer des contacts</h2>
      <div
        className={`dropzone${dragging ? ' dropzone--active' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          pick(event.dataTransfer.files)
        }}
      >
        <p className="dropzone-title">{busy ? 'Import en cours…' : 'Dépose ton fichier ici'}</p>
        <p className="dropzone-hint">CSV ou vCard (.vcf) · colonnes nom, email, téléphone, entreprise</p>
        <button type="button" className="button" disabled={busy} onClick={() => inputRef.current?.click()}>
          Choisir un fichier
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.vcf,.txt,.vcard,text/csv,text/vcard"
          hidden
          onChange={(event) => {
            pick(event.target.files)
            event.target.value = ''
          }}
        />
      </div>
      {notice && <p className={`notice notice--${notice.type}`}>{notice.text}</p>}
    </section>
  )
}
