// Iconos de trazo simples (24×24) para no depender de una librería externa.
const paths = {
  sparkle:
    'M12 3c.7 4.4 2.6 6.3 7 7-4.4.7-6.3 2.6-7 7-.7-4.4-2.6-6.3-7-7 4.4-.7 6.3-2.6 7-7z M19 16.5c.3 1.5.9 2.2 2.5 2.5-1.6.3-2.2 1-2.5 2.5-.3-1.5-.9-2.2-2.5-2.5 1.6-.3 2.2-1 2.5-2.5z',
  upload: 'M12 15V4 M7.5 8.5 12 4l4.5 4.5 M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15',
  file: 'M14 3H7.5A1.5 1.5 0 0 0 6 4.5v15A1.5 1.5 0 0 0 7.5 21h9a1.5 1.5 0 0 0 1.5-1.5V7z M14 3v4h4 M9 13h6 M9 17h4',
  users:
    'M15.5 20v-1.5a3.5 3.5 0 0 0-3.5-3.5H7a3.5 3.5 0 0 0-3.5 3.5V20 M9.5 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M20.5 20v-1.5a3.5 3.5 0 0 0-2.6-3.4 M15.5 4.6a3.5 3.5 0 0 1 0 6.8',
  coins: 'M12 3v18 M16.5 7H10a3 3 0 0 0 0 6h4a3 3 0 0 1 0 6H7',
  ticket:
    'M4 7.5A1.5 1.5 0 0 1 5.5 6h13A1.5 1.5 0 0 1 20 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 16.5V14a2 2 0 0 0 0-4z M14 6v12',
  repeat: 'M17 2.5 20.5 6 17 9.5 M3.5 11V9.5A3.5 3.5 0 0 1 7 6h13.5 M7 21.5 3.5 18 7 14.5 M20.5 13v1.5A3.5 3.5 0 0 1 17 18H3.5',
  bag: 'M5.5 8h13l-1 12.5h-11z M9 8V6.5a3 3 0 0 1 6 0V8',
  target:
    'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z M12 12.6a.6.6 0 1 0 0-1.2.6.6 0 0 0 0 1.2z',
  megaphone:
    'M3.5 10v4a1 1 0 0 0 1 1H7l5.5 4.5v-15L7 9H4.5a1 1 0 0 0-1 1z M16 9a4 4 0 0 1 0 6 M18.5 6.5a7.5 7.5 0 0 1 0 11',
  bulb: 'M9.5 18h5 M10.5 21h3 M12 3a6 6 0 0 0-3.6 10.8c.7.5 1.1 1.3 1.1 2.2h5c0-.9.4-1.7 1.1-2.2A6 6 0 0 0 12 3z',
  chat: 'M5 4.5h14A1.5 1.5 0 0 1 20.5 6v9.5A1.5 1.5 0 0 1 19 17h-8.5L6 20.5V17H5a1.5 1.5 0 0 1-1.5-1.5V6A1.5 1.5 0 0 1 5 4.5z',
  arrowRight: 'M4.5 12h15 M13.5 6l6 6-6 6',
  arrowLeft: 'M19.5 12h-15 M10.5 6l-6 6 6 6',
  check: 'M5 12.5 9.5 17 19 7.5',
  send: 'M20.5 3.5 10 14 M20.5 3.5 14 20.5l-4-6.5-6.5-4z',
  close: 'M6 6l12 12 M18 6 6 18',
  pencil: 'M4 20h4L19 9a2.1 2.1 0 0 0-4-4L4 16z M13.5 6.5l4 4',
  map: 'M4 6.5 9 4l6 2.5L20 4v13.5L15 20l-6-2.5L4 20z M9 4v13.5 M15 6.5V20',
  download: 'M12 4v11 M7.5 10.5 12 15l4.5-4.5 M4 17v1.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V17',
  alert: 'M12 3.5 21.5 20h-19z M12 10v4.5 M12 17.2v.3',
  shield: 'M12 3 19.5 6v5.5c0 4.5-3.2 8.2-7.5 9.5-4.3-1.3-7.5-5-7.5-9.5V6z M9 12l2 2 4-4',
}

export default function Icon({ name, size = 18, className = '', strokeWidth = 1.7 }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={paths[name]} />
    </svg>
  )
}

// Marca de Segmenta: tres grupos que se superponen.
export function BrandMark({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <circle cx="12" cy="13" r="8" fill="#7433e6" />
      <circle cx="21" cy="13" r="6" fill="#c4a8ff" fillOpacity=".9" />
      <circle cx="17" cy="22" r="5" fill="#2f0f66" fillOpacity=".85" />
    </svg>
  )
}
