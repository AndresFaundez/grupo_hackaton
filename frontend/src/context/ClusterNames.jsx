import { createContext, useContext, useMemo, useState } from 'react'
import { clusters } from '../data/demoClusters.js'

const ClusterNamesContext = createContext(null)

export function ClusterNamesProvider({ children }) {
  const [names, setNames] = useState(() =>
    Object.fromEntries(clusters.map((c) => [c.id, c.name])),
  )
  const value = useMemo(
    () => ({
      names,
      rename: (id, name) =>
        setNames((prev) => ({ ...prev, [id]: name.trim() || prev[id] })),
    }),
    [names],
  )
  return (
    <ClusterNamesContext.Provider value={value}>
      {children}
    </ClusterNamesContext.Provider>
  )
}

export function useClusterNames() {
  return useContext(ClusterNamesContext)
}

export function useCluster(id) {
  const { names } = useClusterNames()
  const cluster = clusters.find((c) => c.id === id) ?? clusters[0]
  return { ...cluster, name: names[cluster.id] ?? cluster.name }
}
