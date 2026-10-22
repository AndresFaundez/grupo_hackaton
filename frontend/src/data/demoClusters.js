// Datos de demostración para maquetar la interfaz.
// NO es la capa de API: cuando el backend publique su contrato, esta fuente
// se reemplaza por llamadas reales en src/api/ y este archivo desaparece.

export const summary = {
  totalCustomers: 8450,
  totalSales: 412_600_000,
  clusterCount: 4,
}

export const clusters = [
  {
    id: 1,
    name: 'Premium frecuente',
    color: '#3538cd',
    characterization: ['Alta frecuencia', 'Ticket alto', 'Marcas premium'],
    description:
      'Clientes leales que compran varias veces al mes, con ticket promedio alto y clara preferencia por productos de gama alta. Son el segmento que sostiene la mayor parte de los ingresos.',
    representativeCustomer: {
      name: 'María Fernández',
      age: 42,
      profile: 'Directora de marketing. Compra online cada semana, valora la calidad sobre el precio y responde bien a preventa personalizada.',
    },
    customers: 1240,
    sales: 186_400_000,
    frequency: '4,2 compras/mes',
    topProducts: ['Vinos reserva', 'Quesos gourmet', 'Café de especialidad'],
    strategies: [
      'Programa de fidelización con recompensas por antigüedad',
      'Acceso anticipado a lanzamientos y ediciones limitadas',
      'Atención personalizada vía ejecutivo de cuenta',
    ],
  },
  {
    id: 2,
    name: 'Oportunista puntual',
    color: '#e04f2f',
    characterization: ['Baja frecuencia', 'Sensible a ofertas', 'Ticket variable'],
    description:
      'Clientes que aparecen en promociones y fechas claves (Black Friday, Navidad). Compran poco el resto del año y su ticket depende del descuento disponible.',
    representativeCustomer: {
      name: 'Ignacio Rojas',
      age: 28,
      profile: 'Estudiante de postgrado. Espera descuentos para comprar en volumen y compara precios entre tiendas antes de decidir.',
    },
    customers: 3210,
    sales: 98_700_000,
    frequency: '1,1 compras/mes',
    topProducts: ['Electrónica en oferta', 'Packs promocionales', 'Ropa de temporada'],
    strategies: [
      'Campañas de reactivación con cupones de expiración corta',
      'Ofertas flash segmentadas por categoría de interés',
      'Envío gratis condicionado a monto mínimo para subir el ticket',
    ],
  },
  {
    id: 3,
    name: 'Familiar planificador',
    color: '#0e9384',
    characterization: ['Compra regular', 'Listas repetidas', 'Precio estable'],
    description:
      'Hogares que reponen productos de uso cotidiano en ciclos fijos. Repiten listas de compra, priorizan precio-conveniencia y valoran la eficiencia del envío.',
    representativeCustomer: {
      name: 'Carolina Muñoz',
      age: 37,
      profile: 'Madre de tres hijos. Planifica la compra semanal del hogar, suscribe productos de aseo y compara por unidad de medida.',
    },
    customers: 2450,
    sales: 84_200_000,
    frequency: '2,6 compras/mes',
    topProducts: ['Abarrotes', 'Productos de aseo', 'Pan y lácteos'],
    strategies: [
      'Suscripciones con descuento para compra recurrente',
      'Sugerencias de reposición basadas en su ciclo de compra',
      'Combos de despensa con precio fijo mensual',
    ],
  },
  {
    id: 4,
    name: 'Explorador de nicho',
    color: '#b54708',
    characterization: ['Intereses específicos', 'Prueba productos', 'Ticket medio'],
    description:
      'Clientes que exploran categorías particulares (hobbies, salud, tecnología) y prueban novedades. Compran por interés más que por necesidad.',
    representativeCustomer: {
      name: 'Diego Herrera',
      age: 33,
      profile: 'Desarrollador y aficionado al running. Investiga antes de comprar, sigue reseñas especializadas y prueba marcas nuevas.',
    },
    customers: 1550,
    sales: 43_300_000,
    frequency: '1,8 compras/mes',
    topProducts: ['Suplementos deportivos', 'Gadgets', 'Libros técnicos'],
    strategies: [
      'Contenido y guías de compra para categorías de nicho',
      'Programa de prueba de novedades con descuento de early adopter',
      'Colaboraciones con micro-influencers del rubro',
    ],
  },
]
