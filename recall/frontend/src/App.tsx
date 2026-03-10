const cards = [
  "Screenshot timeline",
  "Settings panel",
  "Summary explorer",
];

export default function App() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-amber-50 to-slate-100 p-8 text-slate-800">
      <section className="mx-auto max-w-4xl rounded-2xl bg-white p-8 shadow-lg">
        <h1 className="text-4xl font-semibold tracking-tight">Recall</h1>
        <p className="mt-3 text-slate-600">React + Vite + Tailwind scaffold is ready for feature delivery.</p>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {cards.map((card) => (
            <article key={card} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h2 className="text-sm font-medium text-slate-700">{card}</h2>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
