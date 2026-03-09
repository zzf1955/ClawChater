export type CaptureReason = 'initial' | 'change' | 'force';

export interface CaptureFrame {
  image: Uint8Array;
  timestamp?: Date | string;
  windowTitle?: string;
  processName?: string;
}

export interface CaptureRequestEvent {
  requestedAt: string;
  timestamp: string;
  reason: CaptureReason;
  changeScore: number;
  frame: {
    image: Uint8Array;
    windowTitle?: string;
    processName?: string;
  };
}

export interface CaptureCompletedEvent {
  screenshotId: number;
  filePath: string;
  timestamp: string;
  phash: string;
  windowTitle: string | null;
  processName: string | null;
  reason: CaptureReason;
  changeScore: number;
}

export type ResourceBusyReason = 'cpu' | 'gpu';
export type ResourceState = 'idle' | 'busy';

export interface ResourceStatusSnapshot {
  cpuUsage: number;
  gpuUsage: number;
  state: ResourceState;
  busyReasons: ResourceBusyReason[];
  sampledAt: string;
}

export interface AppEvents {
  'capture.requested': CaptureRequestEvent;
  'capture.completed': CaptureCompletedEvent;
  'resource.status.changed': ResourceStatusSnapshot;
}
