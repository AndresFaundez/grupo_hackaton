// Cliente HTTP del backend (ver backend/README.md para el contrato completo).
// La URL base se configura con VITE_API_URL; por defecto, el backend local.

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, form } = {}) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: form ?? (body ? JSON.stringify(body) : undefined),
    })
  } catch {
    throw new ApiError(0, `No se pudo conectar con el backend en ${BASE_URL}. ¿Está corriendo?`)
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : detail?.problems?.join('; ') ?? `Error ${response.status} en ${path}`
    throw new ApiError(response.status, message)
  }
  return data
}

export const api = {
  health: () => request('/health'),

  uploadDataset: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/datasets', { method: 'POST', form })
  },
  sampleDataset: () => request('/datasets/sample', { method: 'POST' }),
  createClustering: (datasetId, options = {}) =>
    request(`/datasets/${datasetId}/clusterings`, { method: 'POST', body: options }),
  getClustering: (clusteringId) => request(`/clusterings/${clusteringId}`),

  renameCluster: (clusteringId, clusterId, name) =>
    request(`/clusterings/${clusteringId}/clusters/${clusterId}`, { method: 'PATCH', body: { name } }),

  // payload: { message, session_id?, cluster_ids?, mode?, persona_cluster_id? }
  chat: (clusteringId, payload) =>
    request(`/clusterings/${clusteringId}/chat`, { method: 'POST', body: payload }),

  // payload: { objective, channel, instructions?, previous_message? }
  campaignDraft: (clusteringId, clusterId, payload) =>
    request(`/clusterings/${clusteringId}/clusters/${clusterId}/campaign-draft`, { method: 'POST', body: payload }),

  audienceUrl: (clusteringId, clusterId) =>
    `${BASE_URL}/clusterings/${clusteringId}/clusters/${clusterId}/customers?format=csv`,
  resultUrl: (handle) => `${BASE_URL}/results/${handle}?format=csv`,
}
