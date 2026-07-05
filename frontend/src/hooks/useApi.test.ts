import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useApi } from "./useApi";

describe("useApi", () => {
  it("tracks loading and data on success", async () => {
    const { result } = renderHook(() => useApi<string>());

    let promise: Promise<string>;
    act(() => {
      promise = result.current.execute(() => Promise.resolve("done"));
    });
    expect(result.current.loading).toBe(true);

    await act(async () => {
      await promise;
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe("done");
    expect(result.current.error).toBeNull();
  });

  it("tracks error message on failure", async () => {
    const { result } = renderHook(() => useApi<string>());

    await act(async () => {
      await result.current.execute(() => Promise.reject(new Error("boom"))).catch(() => {});
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("boom");
    expect(result.current.data).toBeNull();
  });

  it("reset clears loading, error and data", async () => {
    const { result } = renderHook(() => useApi<string>());

    await act(async () => {
      await result.current.execute(() => Promise.resolve("done"));
    });
    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});
