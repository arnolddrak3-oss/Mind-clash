const request = async (response) => {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || 'Une erreur est survenue.')
  }
  return data
}

export const listContacts = () => fetch('/api/contacts').then(request)

export const importContacts = (file) => {
  const body = new FormData()
  body.append('file', file)
  return fetch('/api/contacts/import', { method: 'POST', body }).then(request)
}

export const deleteContact = (id) => fetch(`/api/contacts/${id}`, { method: 'DELETE' }).then(request)

export const askAgent = (message) =>
  fetch('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  }).then(request)
