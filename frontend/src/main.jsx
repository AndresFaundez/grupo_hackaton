import { NavLink, Routes, Route, Navigate, BrowserRouter } from 'react-router-dom'
import React from 'react'
import ReactDOM from 'react-dom/client'
import Layout from './Layout.jsx'
import { SegmentationProvider } from './context/Segmentation.jsx'
import Datos from './views/Datos.jsx'
import Procesando from './views/Procesando.jsx'
import Clusters from './views/Clusters.jsx'
import Explorar from './views/Explorar.jsx'
import Campana from './views/Campana.jsx'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SegmentationProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Datos />} />
            <Route path="/procesando" element={<Procesando />} />
            <Route path="/clusters" element={<Clusters />} />
            <Route path="/explorar" element={<Explorar />} />
            <Route path="/campana" element={<Campana />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </SegmentationProvider>
  </React.StrictMode>,
)
