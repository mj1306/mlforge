const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorBody(response: Response): Promise<{ detail?: unknown }> {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await parseErrorBody(response);
    const message =
      typeof body.detail === "string" ? body.detail : response.statusText || "Request failed";
    throw new ApiError(response.status, body.detail, message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    const body = await parseErrorBody(response);
    const message =
      typeof body.detail === "string" ? body.detail : response.statusText || "Request failed";
    throw new ApiError(response.status, body.detail, message);
  }
  return response.blob();
}

export function subscribeToJobStream<T>(
  jobId: string,
  onEvent: (data: T) => void,
  onError?: (event: Event) => void,
): () => void {
  const source = new EventSource(`${BASE_URL}/jobs/${jobId}/stream`);
  source.onmessage = (event) => {
    onEvent(JSON.parse(event.data) as T);
  };
  source.onerror = (event) => {
    onError?.(event);
  };
  return () => source.close();
}

export { BASE_URL };
