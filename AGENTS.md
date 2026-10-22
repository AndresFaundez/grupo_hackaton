# AGENTS.md — grupo_hackaton

Instrucciones y contexto compartido para los agentes de IA que trabajan en este
repositorio. Todos los equipos deben leer este archivo antes de contribuir.

---

## 1. Visión del producto

Estamos construyendo una plataforma de segmentación de clientes:

- El usuario sube bases de datos en bruto (transacciones de compra).
- El sistema corre un clustering de clientes según patrones de compra.
- Usamos IA para definir y delimitar claramente los clusters, categorizando
  los distintos segmentos de clientes.
- Con los clusters definidos e interpretados, el objetivo final es lanzar
  campañas de marketing particulares por segmento.
- Incluye una pestaña para "chatear" con la base de datos mediante IA,
  apoyándose en el clustering y su interpretación, para tomar decisiones
  de marketing.

## 1.1 Flujo del producto, en detalle

1. **Carga**: el usuario pasa la base de datos al sistema y este la
   procesa.
2. **Lista de clusters**: el sistema devuelve una lista con los clusters
   más importantes y una caracterización de cada uno.
3. **Detalle de cluster** (al hacer clic en uno): descripción e
   información del segmento, cliente más representativo, tamaño de
   ventas del cluster, frecuencia de compra, qué cosas compran en
   general y estrategias de marketing sugeridas.
4. **Chat LLM**: conversación sobre los clusters para pedir estrategias
   y más información. El chat tiene la información de los clusters y,
   si es necesario, puede acceder a la base de datos filtrada según el
   cluster del que se está hablando.

## 2. Organización del equipo

Varias personas trabajan en paralelo. Cada subequipo usa su propia rama y su
propio directorio; nadie trabaja fuera de su directorio asignado:

| Subequipo  | Rama       | Directorio   | Responsabilidad                        |
|------------|------------|--------------|----------------------------------------|
| Frontend   | `frontend` | `frontend/`  | Interfaz de la plataforma              |
| (otros)    | (por definir) | (por definir) | Servicio de clustering / IA, datos |

### Frontend (rama `frontend`)

- Stack: React 18 + Vite + react-router-dom.
- Vistas previstas: `Upload` (subir datos y lanzar el procesamiento),
  `Dashboard` (lista de clusters más importantes con su caracterización),
  `Clusters` (explorador: clic en un cluster abre su detalle con
  descripción, cliente más representativo, tamaño de ventas, frecuencia
  de compra, productos típicos y estrategias de marketing) y `Chat`
  (conversación con la base de datos, con acceso a los datos filtrados
  por cluster).
- La capa de API (`frontend/src/api/`) no se construye hasta tener el
  contrato de endpoints del equipo de backend. Hasta entonces, las vistas
  se mantienen como esqueleto sin lógica de datos.
- No modificar nada fuera de `frontend/`.

## 3. Convenciones de Git

- Mensajes de commit en formato **conventional commits**
  (`feat:`, `fix:`, `docs:`, `refactor:`, ...).
- La rama `main` solo recibe documentación acordada por el equipo; cada
  subequipo integra su trabajo por pull request cuando se acuerde.

## 4. Instrucciones para el uso de Chrome DevTools MCP en este entorno

Este archivo documenta la solución al problema de timeout al navegar con el
servidor MCP `chrome-devtools` en este sistema (Linux con Chromium ejecutado
vía Flatpak/sandbox).

### 4.1 Problema identificado

Al usar las herramientas estándar de navegación del MCP `chrome-devtools`:

- `new_page(url="...")`
- `navigate_page(pageId=..., type="url", url="...")`

La ejecución se congela hasta alcanzar el límite de tiempo (`Tool execution
was canceled` tras 2 minutos). Esto sucede porque el servidor MCP espera
internamente eventos de ciclo de vida (`load` o `networkidle`) que no
siempre se emiten o se interceptan a tiempo debido al entorno Flatpak
(`io.github.ungoogled_software.ungoogled_chromium`) o por conexiones
asíncronas persistentes (websockets, analytics, service workers) de la
página web.

### 4.2 Solución probada y recomendada

Para abrir o navegar a cualquier URL de manera inmediata y sin bloqueos:

**Paso 1: Listar las páginas abiertas**

Obtén el ID de la pestaña activa usando `list_pages`:

```json
// Tool: chrome-devtools / list_pages
{}
```

Retornará la lista de pestañas abiertas, por ejemplo:
`1: about:blank [selected]`

**Paso 2: Navegar usando `evaluate_script`**

En lugar de llamar a `navigate_page`, ejecuta una asignación de
`window.location.href` con `waitForStableDom: false`:

```json
// Tool: chrome-devtools / evaluate_script
{
  "pageId": 1,
  "format": "function",
  "function": "() => { window.location.href = \"<URL_OBJETIVO>\"; return window.location.href; }",
  "waitForStableDom": false
}
```

Esto dispara la navegación en el navegador inmediatamente y la llamada MCP
responde en menos de 1 segundo sin bloquearse.

**Paso 3: Confirmar navegación e interactuar**

1. **Verificar el estado de la página:** Llama nuevamente a `list_pages`
   para confirmar que el título y la URL hayan cambiado.
2. **Inspeccionar el árbol de accesibilidad:** Usa `take_snapshot` con
   `pageId: <id>` para leer los elementos del DOM y sus identificadores
   `uid`.
3. **Interacciones:** Usa `click`, `fill`, `evaluate_script`, etc. con los
   `uid` obtenidos.
