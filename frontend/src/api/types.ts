export interface DatasetUploadResult {
  dataset_id: string;
  yaml_path: string;
  classes: Record<number, string>;
}

export interface DatasetInfo {
  dataset_id: string;
  yaml_path: string;
  total_images: number;
  data: Record<string, unknown>;
}

export interface ImageProcessingSettings {
  brightness: number;
  contrast: number;
  saturation: number;
  hue: number;
  blur: number;
  sharpness: number;
  rotation: number;
  flipHorizontal: boolean;
  flipVertical: boolean;
  grayscale: boolean;
  applyToCount: number;
  applyToAll: boolean;
}

export interface ProcessingResult {
  processed_images: number;
  total_requested: number;
  output_dir: string;
  errors: string[];
}

export interface ModelConfig {
  model: string;
  dataset_id: string;
  epochs?: number;
  batch?: number;
  imgsz?: number;
  lr0?: number;
  hyperparams?: Record<string, unknown>;
}

export type JobStatus = "pending" | "running" | "succeeded" | "failed" | "cancelled";

export interface JobProgress {
  stage?: string;
  status?: string;
  epoch?: number;
  total_epochs?: number;
  batch?: number;
  device?: { type: string; name: string; memory_gb: number; display: string };
  metrics?: { box_loss: number; cls_loss: number; dfl_loss: number; instances: number };
  gpu_memory_used?: number;
  validation?: { precision: number; recall: number; mAP50: number; mAP50_95: number };
  last_epoch_metrics?: { box_loss: number; cls_loss: number; dfl_loss: number };
  live_data?: unknown[];
  done?: boolean;
}

export interface JobRecord {
  id: string;
  kind: "training" | "processing" | "cvat_lifecycle";
  status: JobStatus;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  progress: JobProgress;
  error: string | null;
  result: Record<string, unknown> | null;
}

export interface User {
  id: string;
  username: string;
  created_at: string;
}

export interface TrainedModel {
  name: string;
  created_at: string;
  size_bytes: number;
}

export type CvatState = "stopped" | "starting" | "running" | "stopping" | "error";

export interface CvatStatus {
  state: CvatState;
  url: string | null;
  job_id: string | null;
  detail: string | null;
}
