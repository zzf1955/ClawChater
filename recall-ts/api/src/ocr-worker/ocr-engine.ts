import { createRequire } from 'node:module';
import { isAbsolute, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { ConfigService } from '../config/config-service.js';
import { ScreenshotRecord } from '../db/repositories/screenshot-repository.js';
import { JsonValue } from '../types/json.js';

export interface OcrInput {
  screenshot: ScreenshotRecord;
  absoluteFilePath: string;
  image: Uint8Array;
  runtimeRootDir: string;
}

export interface OcrResult {
  text: string;
}

export interface OcrEngine {
  isAvailable?: () => boolean | Promise<boolean>;
  recognize: (input: OcrInput) => Promise<OcrResult>;
  close?: () => void | Promise<void>;
}

interface OcrPipeline {
  recognize: (input: OcrInput) => Promise<OcrResult | string> | OcrResult | string;
  close?: () => void | Promise<void>;
}

interface OcrPipelineFactoryContext {
  ort: unknown;
  runtimeRootDir: string;
  settings: Record<string, JsonValue>;
}

interface OcrPipelineModule {
  createOcrPipeline?: (
    context: OcrPipelineFactoryContext
  ) => Promise<OcrPipeline> | OcrPipeline;
}

export class OnnxRuntimeOcrEngine implements OcrEngine {
  private readonly require = createRequire(import.meta.url);
  private pipeline?: OcrPipeline;
  private pipelinePromise?: Promise<OcrPipeline>;

  constructor(
    private readonly configService: ConfigService,
    private readonly runtimeRootDir: string
  ) {}

  isAvailable(): boolean {
    return this.hasPipelineModule() && this.canLoadOnnxRuntime();
  }

  async recognize(input: OcrInput): Promise<OcrResult> {
    const pipeline = await this.loadPipeline();
    const result = await pipeline.recognize(input);
    return typeof result === 'string' ? { text: result } : result;
  }

  async close(): Promise<void> {
    if (this.pipeline?.close) {
      await this.pipeline.close();
    }
    this.pipeline = undefined;
    this.pipelinePromise = undefined;
  }

  private hasPipelineModule(): boolean {
    const pipelineModule = this.configService.get('OCR_PIPELINE_MODULE');
    return typeof pipelineModule === 'string' && pipelineModule.trim().length > 0;
  }

  private canLoadOnnxRuntime(): boolean {
    try {
      this.require('onnxruntime-node');
      return true;
    } catch {
      return false;
    }
  }

  private async loadPipeline(): Promise<OcrPipeline> {
    if (this.pipeline) {
      return this.pipeline;
    }

    if (!this.pipelinePromise) {
      this.pipelinePromise = this.createPipeline();
    }

    this.pipeline = await this.pipelinePromise;
    return this.pipeline;
  }

  private async createPipeline(): Promise<OcrPipeline> {
    const modulePath = this.configService.get('OCR_PIPELINE_MODULE');
    if (typeof modulePath !== 'string' || modulePath.trim().length === 0) {
      throw new Error('OCR_PIPELINE_MODULE is not configured');
    }

    let ort: unknown;
    try {
      ort = this.require('onnxruntime-node');
    } catch (error) {
      throw new Error(
        `Failed to load onnxruntime-node: ${toErrorMessage(error)}`
      );
    }

    const resolvedModulePath = isAbsolute(modulePath)
      ? modulePath
      : resolve(this.runtimeRootDir, modulePath);
    const module = (await import(pathToFileURL(resolvedModulePath).href)) as OcrPipelineModule;
    if (typeof module.createOcrPipeline !== 'function') {
      throw new Error('OCR pipeline module must export createOcrPipeline(context)');
    }

    const pipeline = await module.createOcrPipeline({
      ort,
      runtimeRootDir: this.runtimeRootDir,
      settings: this.configService.getAll()
    });

    if (!pipeline || typeof pipeline.recognize !== 'function') {
      throw new Error('OCR pipeline module returned an invalid pipeline instance');
    }

    return pipeline;
  }
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.length > 0) {
    return error.message;
  }

  return String(error);
}
