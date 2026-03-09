import { buildServer } from './server.js';

const PORT = Number(process.env.PORT ?? 3000);
const HOST = process.env.HOST ?? '127.0.0.1';

async function start() {
  const app = buildServer();

  try {
    await app.listen({ port: PORT, host: HOST });
  } catch (error) {
    app.log.error(error);
    process.exit(1);
  }
}

void start();
