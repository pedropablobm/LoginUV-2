export function DashboardPage() {
  const machines = [
    { name: 'PC-001', status: 'occupied' },
    { name: 'PC-002', status: 'free' },
    { name: 'PC-003', status: 'occupied' },
    { name: 'PC-004', status: 'free' }
  ]

  return (
    <main className="layout">
      <header className="header">
        <h1>LoginUV - Panel Administrativo</h1>
        <p>Sede central | Estado en tiempo real</p>
      </header>

      <section className="stats">
        <article><strong>Conectados</strong><span>42</span></article>
        <article><strong>Ocupados</strong><span>42</span></article>
        <article><strong>Libres</strong><span>18</span></article>
        <article><strong>Alertas</strong><span>3</span></article>
      </section>

      <section className="grid">
        {machines.map((m) => (
          <div className={`machine ${m.status}`} key={m.name}>
            <span>{m.name}</span>
            <small>{m.status === 'occupied' ? 'Ocupado' : 'Libre'}</small>
          </div>
        ))}
      </section>
    </main>
  )
}
