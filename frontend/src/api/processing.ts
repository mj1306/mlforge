import { request, requestBlob } from "./client";
import type { ImageProcessingSettings, ProcessingResult } from "./types";

export async function getProcessingInfo(
  datasetId: string,
): Promise<{ dataset_id: string; total_images: number }> {
  return request(`/datasets/${encodeURIComponent(datasetId)}/processing/info`);
}

export async function getRandomImage(datasetId: string): Promise<Blob> {
  return requestBlob(`/datasets/${encodeURIComponent(datasetId)}/processing/random-image`);
}

export async function applyProcessing(
  datasetId: string,
  settings: ImageProcessingSettings,
): Promise<ProcessingResult> {
  return request(`/datasets/${encodeURIComponent(datasetId)}/processing/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
}
