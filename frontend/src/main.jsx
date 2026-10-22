import { Navigate, Route, Routes, BrowserRouter } from 'react-router-dom'
import React from 'react'
import ReactDOM from 'react-dom/client'
import Layout from './Layout.jsx'
import { ClusterNamesProvider } from './context/ClusterNames.jsx'
import Datos from './views/Datos.jsx'
import Procesando from './views/Procesando.jsx'
import Clusters from './views/Clusters.jsx'
import Explorar from './views/Explorar.jsx'
import Campana from './views/Campana.jsx'
import BaseDatos from './views/BaseDatos.jsx'
import ChatIA from './views/ChatIA.jsx'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ClusterNamesProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/recorrido" replace />} />
            <Route path="/recorrido" element={<Datos />} />
            <Route path="/recorrido/procesando" element={<Procesando />} />
            <Route path="/recorrido/clusters" element={<Clusters />} />
            <Route path="/recorrido/explorar" element={<Explorar />} />
            <Route path="/recorrido/campana" element={<Campana />} />
            <Route path="/base-de-datos" element={<BaseDatos />} />
            <Route path="/chat" element={<ChatIA />} />
            <Route path="*" element={<Navigate to="/recorrido" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ClusterNamesProvider>
  </React.StrictMode>,
)
