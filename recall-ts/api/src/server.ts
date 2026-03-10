import Fastify from 'fastify';

import { AppContext, createAppContext } from './app-context.js';
import { JsonValue } from './types/json.js';

interface BuildServerOptions {
  context?: AppContext;
}

function isJsonObject(value: unknown): value is Record<string, JsonValue> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function buildServer(options: BuildServerOptions = {}) {
  const ownsContext = !options.context;
  const context = options.context ?? createAppContext();
  const app = Fastify({ logger: true });

  app.get('/health', async () => {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      dbPath: context.dbPath
    };
  });

  app.get('/config', async () => {
    return {
      settings: context.configService.getAll()
    };
  });

  app.get('/resource-status', async () => {
    return context.resourceMonitor.getSnapshot();
  });

  app.post('/config', async (request, reply) => {
    if (!isJsonObject(request.body)) {
      return reply.code(400).send({
        error: 'invalid_body',
        message: 'Body must be a JSON object'
      });
    }

    context.configService.setMany(request.body);
    return {
      settings: context.configService.getAll()
    };
  });

  app.addHook('onClose', async () => {
    if (ownsContext) {
      context.close();
    }
  });

  return app;
}
