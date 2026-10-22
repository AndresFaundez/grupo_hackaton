import { useState } from 'react'
import Icon from './Icon.jsx'

// Nombre propuesto por la IA, editable por el usuario.
export default function EditableName({ name, onRename, as: Tag = 'strong' }) {
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
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit()
            if (e.key === 'Escape') setEditing(false)
          }}
          onBlur={commit}
          autoFocus
          aria-label="Nuevo nombre del segmento"
        />
      </span>
    )
  }

  return (
    <span className="editable">
      <Tag className="editable-name">{name}</Tag>
      <button
        className="edit-button"
        title="Cambiar nombre"
        aria-label={`Cambiar nombre de ${name}`}
        onClick={() => {
          setDraft(name)
          setEditing(true)
        }}
      >
        <Icon name="pencil" size={15} />
      </button>
    </span>
  )
}
