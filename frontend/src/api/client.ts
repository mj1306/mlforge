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

/** FastAPI returns a plain string `detail` for HTTPExceptions, but a list of
 * {loc, msg} objects for 422 validation errors. Flatten the latter into one
 * readable line so the UI never shows a bare "Unprocessable Entity". */
function messageFromDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((entry) => {
        if (entry && typeof entry === "object" && "msg" in entry) {
          const loc = Array.isArray((entry as { loc?: unknown }).loc)
            ? ((entry as { loc: unknown[] }).loc)
            : [];
          const field = loc[loc.length - 1];
          const msg = String((entry as { msg: unknown }).msg);
          return field ? `${String(field)}: ${msg}` : msg;
        }
        return null;
      })
      .filter((part): part is string => Boolean(part));
    if (parts.length > 0) return parts.join("; ");
  }
  return fallback;
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // credentials: "include" sends the mlforge_session cookie on the
  // cross-origin (5173 -> 8000) API calls; the backend scopes all data to it.
  const response = await fetch(`${BASE_URL}${path}`, { credentials: "include", ...init });
  if (!response.ok) {
    const body = await parseErrorBody(response);
    const message = messageFromDetail(body.detail, response.statusText || "Request failed");
    throw new ApiError(response.status, body.detail, message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(`${BASE_URL}${path}`, { credentials: "include", ...init });
  if (!response.ok) {
    const body = await parseErrorBody(response);
    const message = messageFromDetail(body.detail, response.statusText || "Request failed");
    throw new ApiError(response.status, body.detail, message);
  }
  return response.blob();
}

export function subscribeToJobStream<T>(
  jobId: string,
  onEvent: (data: T) => void,
  onError?: (event: Event) => void,
): () => void {
  const source = new EventSource(`${BASE_URL}/jobs/${jobId}/stream`, {
    withCredentials: true,
  });
  source.onmessage = (event) => {
    onEvent(JSON.parse(event.data) as T);
  };
  source.onerror = (event) => {
    onError?.(event);
  };
  return () => source.close();
}

export { BASE_URL };
