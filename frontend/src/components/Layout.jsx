import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import SoftlineLogo from './SoftlineLogo'

const navItems = [
  { to: '/',           icon: '🏠', label: 'Inicio' },
  { section: 'Modelos ML' },
  { to: '/demand',     icon: '📈', label: 'Demanda' },
  { to: '/inventory',  icon: '📦', label: 'Inventario' },
  { to: '/analytics',  icon: '💰', label: 'Analítica' },
  { to: '/products',   icon: '🛍️', label: 'Productos' },
  { to: '/stores',     icon: '🏪', label: 'Tiendas' },
]

const titles = {
  '/':          { title: 'Dashboard',         subtitle: 'Resumen ejecutivo de la cadena de suministro' },
  '/demand':    { title: 'Demanda & Pronósticos', subtitle: 'Prophet · LightGBM' },
  '/inventory': { title: 'Inventario & Riesgo',   subtitle: 'Anomalías · EOQ · Monte Carlo' },
  '/analytics': { title: 'Analítica de Negocio',  subtitle: 'Rentabilidad · Rotación · Eficiencia' },
  '/products':  { title: 'Productos',              subtitle: 'Segmentación ABC · Market Basket' },
  '/stores':    { title: 'Tiendas',                subtitle: 'Catálogo y segmentación de tiendas' },
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const current = titles[location.pathname] || { title: 'Go Retail', subtitle: '' }

  const handleLogout = () => { logout(); navigate('/login') }
  const initials = user?.username?.slice(0, 2).toUpperCase() || 'GR'

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>Go Retail</h1>
          <span>Supply Chain Intelligence</span>
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <SoftlineLogo size="sm" />
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item, i) =>
            item.section ? (
              <div key={i} className="nav-section">{item.section}</div>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </NavLink>
            )
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{initials}</div>
            <div>
              <div className="user-name">{user?.username}</div>
              <div className="user-role">{user?.rol}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout}>Cerrar sesión</button>
        </div>
      </aside>

      <div className="main-content">
        <div className="topbar">
          <div>
            <div className="page-title">{current.title}</div>
            {current.subtitle && <div className="page-subtitle">{current.subtitle}</div>}
          </div>
        </div>
        <div className="page-content">{children}</div>
      </div>
    </div>
  )
}
