type EventListener<TPayload> = (payload: TPayload) => void;

export class EventBus<TEvents extends object> {
  private readonly listeners = new Map<string, Set<EventListener<unknown>>>();

  on<TKey extends keyof TEvents>(
    eventName: TKey,
    listener: EventListener<TEvents[TKey]>
  ): () => void {
    const key = String(eventName);
    const current = this.listeners.get(key) ?? new Set<EventListener<unknown>>();
    current.add(listener as EventListener<unknown>);
    this.listeners.set(key, current);

    return () => {
      current.delete(listener as EventListener<unknown>);
      if (current.size === 0) {
        this.listeners.delete(key);
      }
    };
  }

  emit<TKey extends keyof TEvents>(eventName: TKey, payload: TEvents[TKey]): void {
    const current = this.listeners.get(String(eventName));
    if (!current) {
      return;
    }

    for (const listener of current) {
      listener(payload);
    }
  }
}
