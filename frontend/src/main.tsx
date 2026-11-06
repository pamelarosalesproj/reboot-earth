import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthContext.tsx'

const root = createRoot(document.getElementById('root')!)

if (import.meta.env.DEV && window.location.pathname.startsWith('/preview/')) {
  import('./preview/DesignPreview').then(({ default: DesignPreview }) => {
    root.render(<StrictMode><DesignPreview /></StrictMode>)
  })
} else root.render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
