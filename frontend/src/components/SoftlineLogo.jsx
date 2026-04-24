export default function SoftlineLogo({ size = 'md' }) {
  const scale = size === 'sm' ? 0.7 : size === 'lg' ? 1.3 : 1

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8 * scale,
      transform: `scale(${scale})`,
      transformOrigin: 'left center',
    }}>
      {/* Ícono — dos cuadrados superpuestos estilo Softline */}
      <div style={{ position: 'relative', width: 36, height: 36, flexShrink: 0 }}>
        {/* Cuadrado trasero (verde oscuro) */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 24,
          height: 24,
          borderRadius: 4,
          background: '#2d7a2d',
        }} />
        {/* Cuadrado delantero (verde claro) */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          right: 0,
          width: 24,
          height: 24,
          borderRadius: 4,
          background: '#5cb85c',
          opacity: 0.92,
        }} />
      </div>

      {/* Texto */}
      <div style={{ lineHeight: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
          <span style={{
            fontSize: 22,
            fontWeight: 800,
            color: '#e8e8e8',
            letterSpacing: '-0.5px',
            fontFamily: 'Georgia, serif',
          }}>
            Softline
          </span>
          <span style={{
            fontSize: 9,
            fontWeight: 600,
            color: '#aaa',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            s.a.
          </span>
        </div>
        <div style={{
          fontSize: 9,
          color: '#5cb85c',
          letterSpacing: '0.8px',
          marginTop: 2,
          fontStyle: 'italic',
        }}>
          We do IT simple
        </div>
      </div>
    </div>
  )
}
