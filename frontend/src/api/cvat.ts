import { request } from "./client";
import type { CvatStatus } from "./types";

export async function getCvatStatus(): Promise<CvatStatus> {
  return request("/cvat/status");
}

export async function startCvat(): Promise<CvatStatus> {
  return request("/cvat/start", { method: "POST" });
}

export async function stopCvat(): Promise<CvatStatus> {
  return request("/cvat/stop", { method: "POST" });
}
