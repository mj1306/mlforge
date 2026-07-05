import { request } from "./client";
import type { JobRecord, ModelConfig } from "./types";

export async function startTraining(config: ModelConfig): Promise<{ job_id: string }> {
  return request("/training/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export async function getJob(jobId: string): Promise<JobRecord> {
  return request(`/jobs/${encodeURIComponent(jobId)}`);
}

export async function cancelJob(jobId: string): Promise<{ cancel_requested: boolean }> {
  return request(`/jobs/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
}
