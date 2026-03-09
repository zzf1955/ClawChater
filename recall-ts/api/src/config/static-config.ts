import { existsSync, readFileSync } from 'node:fs';
import { isAbsolute, join, resolve } from 'node:path';

import { JsonValue } from '../types/json.js';
import { DEFAULT_SETTINGS } from './default-settings.js';

export interface LoadedStaticConfig {
  configPath: string;
  settings: Record<string, JsonValue>;
}

function isJsonObject(value: unknown): value is Record<string, JsonValue> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function resolveApiRoot(cwd: string): string {
  const workspaceApiPath = join(cwd, 'api', 'package.json');
  if (existsSync(workspaceApiPath)) {
    return join(cwd, 'api');
  }

  return cwd;
}

function resolveConfigPath(configPath?: string): string {
  if (configPath) {
    return isAbsolute(configPath) ? configPath : resolve(process.cwd(), configPath);
  }

  const apiRoot = resolveApiRoot(process.cwd());
  return join(apiRoot, 'config.json');
}

export function loadStaticConfig(configPath?: string): LoadedStaticConfig {
  const finalConfigPath = resolveConfigPath(configPath);
  if (!existsSync(finalConfigPath)) {
    return {
      configPath: finalConfigPath,
      settings: { ...DEFAULT_SETTINGS }
    };
  }

  const raw = readFileSync(finalConfigPath, 'utf-8');
  const parsed = JSON.parse(raw) as unknown;

  if (!isJsonObject(parsed)) {
    throw new Error(`Static config must be a JSON object: ${finalConfigPath}`);
  }

  return {
    configPath: finalConfigPath,
    settings: {
      ...DEFAULT_SETTINGS,
      ...parsed
    }
  };
}
