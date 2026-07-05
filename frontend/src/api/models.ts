import { BASE_URL, request } from "./client";
import type { JobRecord, TrainedModel } from "./types";

export async function listModels(): Promise<TrainedModel[]> {
  return request<TrainedModel[]>("/models");
}

export function modelWeightsUrl(modelName: string): string {
  return `${BASE_URL}/models/${encodeURIComponent(modelName)}/weights`;
}

export async function listJobs(): Promise<JobRecord[]> {
  const { jobs } = await request<{ jobs: JobRecord[] }>("/jobs");
  return jobs;
}
