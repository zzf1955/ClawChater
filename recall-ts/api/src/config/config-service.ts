import { SettingsRepository } from '../db/repositories/settings-repository.js';
import { JsonValue } from '../types/json.js';

export type ConfigChangeListener = (
  next: Readonly<Record<string, JsonValue>>,
  changedKeys: string[]
) => void;

export class ConfigService {
  private readonly listeners = new Set<ConfigChangeListener>();
  private mergedSettings: Record<string, JsonValue>;

  constructor(
    private readonly staticSettings: Record<string, JsonValue>,
    private readonly settingsRepository: SettingsRepository
  ) {
    this.mergedSettings = { ...staticSettings };
  }

  load(): void {
    const dbSettings = this.settingsRepository.getAll();
    this.mergedSettings = {
      ...this.staticSettings,
      ...dbSettings
    };
  }

  get<T extends JsonValue>(key: string, fallback?: T): JsonValue | T | undefined {
    if (Object.hasOwn(this.mergedSettings, key)) {
      return this.mergedSettings[key];
    }
    return fallback;
  }

  getAll(): Record<string, JsonValue> {
    return { ...this.mergedSettings };
  }

  set(key: string, value: JsonValue): void {
    this.settingsRepository.set(key, value);
    this.mergedSettings[key] = value;
    this.notify([key]);
  }

  setMany(settings: Record<string, JsonValue>): void {
    const keys = Object.keys(settings);
    if (keys.length === 0) {
      return;
    }

    this.settingsRepository.setMany(settings);
    Object.assign(this.mergedSettings, settings);
    this.notify(keys);
  }

  onDidChange(listener: ConfigChangeListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(changedKeys: string[]): void {
    const snapshot = this.getAll();
    for (const listener of this.listeners) {
      listener(snapshot, changedKeys);
    }
  }
}
