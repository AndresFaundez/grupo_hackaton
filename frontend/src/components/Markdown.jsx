// Render mínimo del markdown que devuelve el LLM (títulos, listas, negritas, separadores).
// Construye elementos de React: nunca inyecta HTML.

function inline(text, keyPrefix) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g)
  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={key}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) return <code key={key}>{part.slice(1, -1)}</code>
    if (part.startsWith('*') && part.endsWith('*') && part.length > 2) return <em key={key}>{part.slice(1, -1)}</em>
    return part
  })
}

export default function Markdown({ text }) {
  const lines = (text ?? '').split('\n')
  const blocks = []
  let list = null

  const flushList = () => {
    if (list) blocks.push(list)
    list = null
  }

  lines.forEach((raw) => {
    const line = raw.trimEnd()
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/)
    if (bullet || numbered) {
      const type = bullet ? 'ul' : 'ol'
      if (!list || list.type !== type) {
        flushList()
        list = { type, items: [] }
      }
      list.items.push((bullet ?? numbered)[1])
      return
    }
    flushList()
    if (!line.trim()) return
    const heading = line.match(/^#{1,6}\s+(.*)$/)
    if (heading) blocks.push({ type: 'h', text: heading[1] })
    else if (/^(-{3,}|\*{3,})$/.test(line.trim())) blocks.push({ type: 'hr' })
    else blocks.push({ type: 'p', text: line })
  })
  flushList()

  return (
    <div className="md">
      {blocks.map((block, i) => {
        if (block.type === 'h') return <h4 key={i}>{inline(block.text, i)}</h4>
        if (block.type === 'hr') return <hr key={i} />
        if (block.type === 'p') return <p key={i}>{inline(block.text, i)}</p>
        const Tag = block.type
        return (
          <Tag key={i}>
            {block.items.map((item, j) => (
              <li key={j}>{inline(item, `${i}-${j}`)}</li>
            ))}
          </Tag>
        )
      })}
    </div>
  )
}
