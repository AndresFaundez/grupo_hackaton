// Datos de demostración para maquetar la interfaz.
// NO es la capa de API: cuando el backend publique su contrato, esta fuente
// se reemplaza por llamadas reales en src/api/ y este archivo desaparece.

export const dataset = {
  fileName: 'ventas_tienda_aurora_2025.csv',
  totalCustomers: 4860,
  totalSales: 312_400_000,
  clusterCount: 4,
}

// Puntos del gráfico de dispersión (frecuencia compras/año, gasto promedio $).
const pts = (base, spread, n) =>
  Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2
    const jx = ((i * 7919) % 97) / 97 - 0.5
    const jy = ((i * 104729) % 89) / 89 - 0.5
    return {
      x: Math.max(0.2, base.x + Math.cos(a) * spread.x + jx * spread.x),
      y: Math.max(2000, base.y + Math.sin(a) * spread.y + jy * spread.y),
    }
  })

export const clusters = [
  {
    id: 'leales',
    name: 'Clientes leales',
    color: '#3538cd',
    characterization: ['Frecuencia alta', 'Ticket medio', 'Recurrente'],
    description:
      'Compran con regularidad y responden bien a novedades de la marca.',
    traits: ['Compra cada 28 días', '5,2 pedidos al año', 'Prefiere hogar y cocina'],
    customers: 1340,
    share: 0.276,
    avgSpend: 98500,
    frequency: '5,2 compras al año',
    frequencyPerYear: 5.2,
    topProducts: ['Hogar y cocina', 'Abarrotes', 'Limpieza'],
    representativeCustomer: {
      name: 'María Fernández',
      age: 42,
      profile:
        'Compra online cada semana, valora la calidad sobre el precio y responde bien a preventa personalizada.',
    },
    suggestedObjective: 'fidelizar',
    strategies: [
      'Programa de recompensas por antigüedad',
      'Acceso anticipado a lanzamientos',
      'Sugerencias de reposición según su ciclo',
    ],
    points: pts({ x: 5.2, y: 98500 }, { x: 1.1, y: 14000 }, 14),
  },
  {
    id: 'alto-valor',
    name: 'Alto valor',
    color: '#0e9384',
    characterization: ['Ticket alto', 'Pocos clientes', 'Premium'],
    description:
      'Pocos clientes con tickets altos que concentran gran parte de los ingresos.',
    traits: ['Gasta 4x el promedio', '2,8 pedidos al año', 'Prefiere marcas premium'],
    customers: 520,
    share: 0.107,
    avgSpend: 342000,
    frequency: '2,8 compras al año',
    frequencyPerYear: 2.8,
    topProducts: ['Vinos reserva', 'Quesos gourmet', 'Café de especialidad'],
    representativeCustomer: {
      name: 'Ignacio Rojas',
      age: 47,
      profile:
        'Directivo. Compra poco pero muy caro, prioriza exclusividad y atención personalizada.',
    },
    suggestedObjective: 'ticket',
    strategies: [
      'Atención personalizada vía ejecutivo de cuenta',
      'Ediciones limitadas y catálogo premium',
      'Invitaciones a eventos exclusivos',
    ],
    points: pts({ x: 2.8, y: 342000 }, { x: 0.9, y: 52000 }, 9),
  },
  {
    id: 'reactivar',
    name: 'Clientes por reactivar',
    color: '#e04f2f',
    characterization: ['Sin compras recientes', 'Riesgo de fuga', 'Eran frecuentes'],
    description:
      'Compraban con cierta regularidad, pero llevan meses sin volver a comprar.',
    traits: ['Sin compras hace 4 meses', 'Compraba cada 40 días', 'Sensible a ofertas'],
    customers: 1610,
    share: 0.331,
    avgSpend: 41500,
    frequency: '2,1 compras al año',
    frequencyPerYear: 2.1,
    topProducts: ['Ropa de temporada', 'Electrónica en oferta', 'Packs promocionales'],
    representativeCustomer: {
      name: 'Carolina Muñoz',
      age: 37,
      profile:
        'Compraba en cada campaña, pero la última experiencia de envío la decepcionó.',
    },
    suggestedObjective: 'reactivar',
    strategies: [
      'Cupón de bienvenida de vuelta con expiración corta',
      'Encuesta breve para detectar la causa de fuga',
      'Oferta personalizada sobre su última categoría comprada',
    ],
    points: pts({ x: 2.1, y: 41500 }, { x: 0.8, y: 9000 }, 12),
  },
  {
    id: 'ocasionales',
    name: 'Compradores ocasionales',
    color: '#b54708',
    characterization: ['Baja frecuencia', 'Sensible a ofertas', 'Ticket variable'],
    description:
      'Aparecen en promociones y fechas claves; compran poco el resto del año.',
    traits: ['Solo en eventos y ofertas', '1,2 pedidos al año', 'Compara precios'],
    customers: 1390,
    share: 0.286,
    avgSpend: 28900,
    frequency: '1,2 compras al año',
    frequencyPerYear: 1.2,
    topProducts: ['Electrónica en oferta', 'Packs promocionales', 'Regalos'],
    representativeCustomer: {
      name: 'Diego Herrera',
      age: 28,
      profile:
        'Espera descuentos para comprar en volumen y compara precios entre tiendas.',
    },
    suggestedObjective: 'recompra',
    strategies: [
      'Ofertas flash segmentadas por categoría de interés',
      'Envío gratis condicionado a monto mínimo',
      'Campañas de temporada con recordatorio previo',
    ],
    points: pts({ x: 1.2, y: 28900 }, { x: 0.5, y: 7000 }, 11),
  },
]

export const objectives = [
  { id: 'recompra', label: 'Impulsar recompra', description: 'Que vuelvan a comprar pronto' },
  { id: 'fidelizar', label: 'Fidelizar', description: 'Premiar y retener' },
  { id: 'reactivar', label: 'Reactivar', description: 'Recuperar clientes inactivos' },
  { id: 'ticket', label: 'Aumentar ticket', description: 'Venta cruzada o premium' },
]

export const channels = [
  { id: 'email', label: 'Email' },
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'sms', label: 'SMS' },
]

// Borradores de mensaje por objetivo (simulan lo que generará la IA).
export const campaignDrafts = {  recompra: [
    '¡Te espera lo que te gusta! Volviste a estar entre nuestras novedades de la semana. Usa el código VUELVE15 y obtén 15% en tu próxima compra.',
    'Nuevas novedades llegaron a tu categoría favorita. Compra esta semana con 15% de descuento con el código VUELVE15.',
  ],
  fidelizar: [
    'Como cliente leal, tienes acceso anticipado a nuestro próximo lanzamiento antes que nadie. Gracias por acompañarnos.',
    'Eres parte de los que siempre están. Estrena nuestra colección antes que nadie: acceso preferente activo en tu cuenta.',
  ],
  reactivar: [
    'Te extrañamos. Tu opinión es valiosa: cuéntanos qué pasó y recibe un cupón de 20% para tu próxima compra.',
    'Hace un tiempo no nos visitas. Volvemos con algo para ti: 20% de descuento en tu próxima compra, válido esta semana.',
  ],
  ticket: [
    'Gracias por elegirnos. Como miembro preferente, estrena nuestra línea premium con envío gratis en compras sobre $150.000.',
    'Elección premium: productos seleccionados y envío gratis sobre $150.000, solo para clientes como tú.',
  ],
}

// Clientes de demostración para el explorador de la base de datos.
// Deterministas: mismo archivo, mismos clientes.
const firstNames = ['Ana', 'Luis', 'Camila', 'Javier', 'Fernanda', 'Mateo', 'Josefa', 'Tomás', 'Valentina', 'Cristóbal', 'Isidora', 'Nicolás']
const lastNames = ['Soto', 'Muñoz', 'Rojas', 'Silva', 'Pérez', 'Contreras', 'Morales', 'Fuentes', 'Herrera', 'Álvarez', 'Castro', 'Navarro']

export const customers = clusters.flatMap((c, ci) =>
  Array.from({ length: 12 }, (_, i) => {
    const r = ((i * 37 + ci * 11) % 100) / 100
    return {
      id: `CLI-${String(ci * 12 + i + 101).padStart(4, '0')}`,
      name: `${firstNames[(i + ci * 5) % 12]} ${lastNames[(i * 3 + ci * 7) % 12]}`,
      cluster: c.id,
      spend: Math.round(c.avgSpend * (0.7 + r * 0.6)),
      frequency: +(c.frequencyPerYear * (0.7 + r * 0.6)).toFixed(1),
      lastPurchase: Math.round(1 + r * 90),
    }
  }),
)
