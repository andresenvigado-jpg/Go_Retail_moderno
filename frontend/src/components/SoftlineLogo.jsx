export default function SoftlineLogo({ size = 'md' }) {
  const fontSize   = size === 'sm' ? 14 : size === 'lg' ? 24 : 18
  const subSize    = size === 'sm' ? 8  : size === 'lg' ? 11 : 9
  const tagSize    = size === 'sm' ? 8  : size === 'lg' ? 10 : 9

  return (
    <div style={{ lineHeight: 1.2, textAlign: 'left' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 3 }}>
        <span style={{
          fontSize,
          fontWeight: 800,
          color: '#e8e8e8',
          letterSpacing: '-0.5px',
          fontFamily: 'Georgia, serif',
        }}>
          Softline
        </span>
        <span style={{
          fontSize: subSize,
          fontWeight: 600,
          color: '#aaa',
          letterSpacing: '0.5px',
        }}>
          S.A.
        </span>
      </div>
      <div style={{
        fontSize: tagSize,
        color: '#5cb85c',
        letterSpacing: '0.8px',
        marginTop: 2,
        fontStyle: 'italic',
      }}>
        We do IT simple
      </div>
    </div>
  )
}
