import { create } from "zustand";
import { getCvatStatus, startCvat, stopCvat } from "../api/cvat";
import type { CvatStatus } from "../api/types";

interface CvatStoreState {
  status: CvatStatus;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  start: () => Promise<void>;
  stop: () => Promise<void>;
}

const initialStatus: CvatStatus = { state: "stopped", url: null, job_id: null, detail: null };

export const useCvatStore = create<CvatStoreState>((set) => ({
  status: initialStatus,
  loading: false,
  error: null,

  refresh: async () => {
    try {
      const status = await getCvatStatus();
      set({ status, error: null });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to fetch CVAT status" });
    }
  },

  start: async () => {
    set({ loading: true, error: null });
    try {
      const status = await startCvat();
      set({ status });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to start CVAT" });
    } finally {
      set({ loading: false });
    }
  },

  stop: async () => {
    set({ loading: true, error: null });
    try {
      const status = await stopCvat();
      set({ status });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : "Failed to stop CVAT" });
    } finally {
      set({ loading: false });
    }
  },
}));
