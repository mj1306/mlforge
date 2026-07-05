import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, request, subscribeToJobStream } from "./client";

describe("request", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ hello: "world" }),
      }),
    );

    const result = await request<{ hello: string }>("/ping");

    expect(result).toEqual({ hello: "world" });
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => ({}) }),
    );

    const result = await request<undefined>("/ping");

    expect(result).toBeUndefined();
  });

  it("throws ApiError with the detail message on non-2xx responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({ detail: "Dataset not found" }),
      }),
    );

    await expect(request("/datasets/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Dataset not found",
    });
  });

  it("falls back to statusText when there is no JSON body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("no body");
        },
      }),
    );

    await expect(request("/boom")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("subscribeToJobStream", () => {
  it("parses incoming messages and forwards them to onEvent", () => {
    const listeners: Record<string, (event: unknown) => void> = {};
    const close = vi.fn();
    class FakeEventSource {
      constructor(_url: string) {}
      set onmessage(handler: (event: unknown) => void) {
        listeners.message = handler;
      }
      set onerror(handler: (event: unknown) => void) {
        listeners.error = handler;
      }
      close = close;
    }
    vi.stubGlobal("EventSource", FakeEventSource as unknown as typeof EventSource);

    const onEvent = vi.fn();
    const unsubscribe = subscribeToJobStream("job-1", onEvent);

    listeners.message({ data: JSON.stringify({ status: "running" }) });
    expect(onEvent).toHaveBeenCalledWith({ status: "running" });

    unsubscribe();
    expect(close).toHaveBeenCalled();

    vi.unstubAllGlobals();
  });
});
