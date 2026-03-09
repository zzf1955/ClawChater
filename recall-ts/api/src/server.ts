import Fastify from 'fastify';

export function buildServer() {
  const app = Fastify({ logger: true });

  app.get('/health', async () => {
    return {
      status: 'ok',
      timestamp: new Date().toISOString()
    };
  });

  return app;
}
