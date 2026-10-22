import { useState } from 'react'

// Nombre propuesto por la IA, editable por el usuario.
export default function EditableName({ name, onRename }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(name)

  const commit = () => {
    onRename(draft)
    setEditing(false)
  }

  if (editing) {
    return (
      <span className="editable editing">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && commit()}
          onBlur={commit}
          autoFocus
          aria-label="Nuevo nombre del cluster"
        />
      </span>
    )
  }

  return (
    <span className="editable">
      <strong>{name}</strong>
      <button
        className="link-button"
        onClick={() => {
          setDraft(name)
          setEditing(true)
        }}
      >
        Editar nombre
      </button>
    </span>
  )
}
