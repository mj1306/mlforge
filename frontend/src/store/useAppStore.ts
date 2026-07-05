import { create } from "zustand";

interface AppState {
  training: boolean;
  setTraining: (training: boolean) => void;
  currentModel: string | null;
  setCurrentModel: (model: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  training: false,
  setTraining: (training) => set({ training }),
  currentModel: null,
  setCurrentModel: (currentModel) => set({ currentModel }),
}));
