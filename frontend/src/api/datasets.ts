import { request } from "./client";
import type { DatasetInfo, DatasetUploadResult } from "./types";

export async function uploadDataset(file: File): Promise<DatasetUploadResult> {
  const formData = new FormData();
  formData.append("dataset", file);
  return request<DatasetUploadResult>("/datasets", { method: "POST", body: formData });
}

export async function listDatasets(): Promise<string[]> {
  const { datasets } = await request<{ datasets: string[] }>("/datasets");
  return datasets;
}

export async function getDatasetInfo(datasetId: string): Promise<DatasetInfo> {
  return request<DatasetInfo>(`/datasets/${encodeURIComponent(datasetId)}`);
}

export async function updateClasses(
  datasetId: string,
  classes: Record<number, string>,
): Promise<{ yaml_path: string }> {
  return request(`/datasets/${encodeURIComponent(datasetId)}/classes`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ classes }),
  });
}
