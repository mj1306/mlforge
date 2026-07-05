import { afterEach, describe, expect, it, vi } from "vitest";
import { getCvatStatus, startCvat, stopCvat } from "./cvat";

function stubFetchOnce(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => body }),
  );
}

describe("cvat api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("getCvatStatus hits /cvat/status and returns the status", async () => {
    stubFetchOnce({ state: "stopped", url: null, job_id: null, detail: null });

    const status = await getCvatStatus();

    expect(status.state).toBe("stopped");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/cvat/status"),
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("startCvat POSTs to /cvat/start", async () => {
    stubFetchOnce({ state: "starting", url: null, job_id: "abc", detail: null });

    const status = await startCvat();

    expect(status.state).toBe("starting");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/cvat/start"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("stopCvat POSTs to /cvat/stop", async () => {
    stubFetchOnce({ state: "stopped", url: null, job_id: null, detail: null });

    const status = await stopCvat();

    expect(status.state).toBe("stopped");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/cvat/stop"),
      expect.objectContaining({ method: "POST" }),
    );
  });
});
