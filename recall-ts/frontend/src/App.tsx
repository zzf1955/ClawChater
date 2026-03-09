import { useState } from 'react';

type HealthPayload = {
  status: string;
  timestamp: string;
};

function App() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setError(null);

    try {
      const response = await fetch('/health');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = (await response.json()) as HealthPayload;
      setHealth(data);
    } catch (err) {
      setHealth(null);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 px-6 text-slate-100">
      <h1 className="text-3xl font-bold">Recall TS Skeleton</h1>
      <p className="text-center text-slate-300">
        React + Vite + Tailwind frontend, connected to Fastify backend.
      </p>

      <button
        type="button"
        className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-900 hover:bg-cyan-400"
        onClick={() => {
          void checkHealth();
        }}
      >
        Check /health
      </button>

      {health && (
        <pre className="w-full rounded-lg bg-slate-900 p-4 text-sm text-cyan-200">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}

      {error && <p className="text-rose-400">Health check failed: {error}</p>}
    </main>
  );
}

export default App;
