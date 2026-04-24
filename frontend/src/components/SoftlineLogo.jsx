export default function SoftlineLogo({ size = 'md' }) {
  const fontSize = size === 'sm' ? 14 : size === 'lg' ? 22 : 17
  const subSize  = size === 'sm' ? 9  : size === 'lg' ? 12 : 10
  const tagSize  = size === 'sm' ? 8  : size === 'lg' ? 10 : 9

  return (
    <div style={{ lineHeight: 1.2 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
        <span style={{
          fontSize,
          fontWeight: 700,
          color: '#c8c8c8',
          letterSpacing: '0.2px',
          fontFamily: 'Arial, sans-serif',
        }}>
          Softline
        </span>
        <span style={{
          fontSize: subSize,
          fontWeight: 500,
          color: '#999',
        }}>
          s.a.
        </span>
      </div>
      <div style={{
        fontSize: tagSize,
        color: '#7cb87c',
        letterSpacing: '0.3px',
        marginTop: 1,
        fontStyle: 'italic',
        fontFamily: 'Arial, sans-serif',
      }}>
        We do IT simple
      </div>
    </div>
  )
}
