import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client.js'
import { toUiSegmentation } from '../api/adapter.js'

// Estado de la segmentación actual: origen de los datos, procesamiento y clusters.
const SegmentationContext = createContext(null)
const STORAGE_KEY = 'segmenta.clusteringId'

const readStoredId = () => {
  try {
    return sessionStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

const storeId = (id) => {
  try {
    if (id) sessionStorage.setItem(STORAGE_KEY, id)
    else sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // sin almacenamiento disponible: la segmentación vive solo en memoria
  }
}

export function SegmentationProvider({ children }) {
  const [source, setSource] = useState(null) // { file } | { sample: true }
  const [status, setStatus] = useState('idle') // idle | processing | ready | error
  const [step, setStep] = useState(0) // 0: subiendo y leyendo, 1: clusterizando y nombrando
  const [error, setError] = useState(null)
  const [segmentation, setSegmentation] = useState(null)
  const inFlight = useRef(false)

  // Al recargar la página, recupera la última segmentación si el backend la sigue teniendo.
  useEffect(() => {
    const id = readStoredId()
    if (!id) return
    api
      .getClustering(id)
      .then((result) => {
        setSegmentation(toUiSegmentation(result))
        setStatus('ready')
      })
      .catch(() => storeId(null))
  }, [])

  const start = useCallback((nextSource) => {
    setSource(nextSource)
    setSegmentation(null)
    setError(null)
    setStatus('idle')
    storeId(null)
  }, [])

  const process = useCallback(async () => {
    if (!source || inFlight.current) return
    inFlight.current = true
    setStatus('processing')
    setError(null)
    setStep(0)
    try {
      const dataset = source.sample ? await api.sampleDataset() : await api.uploadDataset(source.file)
      setStep(1)
      const result = await api.createClustering(dataset.dataset_id)
      const ui = toUiSegmentation(result)
      setSegmentation(ui)
      storeId(ui.clusteringId)
      setStatus('ready')
    } catch (e) {
      setError(e.message)
      setStatus('error')
    } finally {
      inFlight.current = false
    }
  }, [source])

  const rename = useCallback(
    (id, name) => {
      const trimmed = name.trim()
      const cluster = segmentation?.clusters.find((c) => c.id === id)
      if (!cluster || !trimmed || cluster.name === trimmed) return
      setSegmentation((prev) => ({
        ...prev,
        clusters: prev.clusters.map((c) => (c.id === id ? { ...c, name: trimmed } : c)),
      }))
      api
        .renameCluster(segmentation.clusteringId, cluster.clusterId, trimmed)
        .catch((e) => console.warn('No se pudo guardar el nombre en el backend:', e.message))
    },
    [segmentation],
  )

  const value = useMemo(
    () => ({
      source,
      status,
      step,
      error,
      clusteringId: segmentation?.clusteringId ?? null,
      dataset: segmentation?.dataset ?? null,
      scatter: segmentation?.scatter ?? null,
      clusters: segmentation?.clusters ?? [],
      start,
      process,
      rename,
    }),
    [source, status, step, error, segmentation, start, process, rename],
  )

  return <SegmentationContext.Provider value={value}>{children}</SegmentationContext.Provider>
}

export function useSegmentation() {
  return useContext(SegmentationContext)
}

export function useCluster(id) {
  const { clusters } = useSegmentation()
  return clusters.find((c) => c.id === id) ?? clusters[0] ?? null
}
