import { create } from "zustand";
import { ApiError } from "../api/client";
import { getCurrentUser, login, logout, register } from "../api/auth";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  /** false until the initial GET /auth/me round-trip settles, so route
   * guards can wait instead of bouncing a logged-in user to /login. */
  initialized: boolean;
  loading: boolean;
  error: string | null;
  init: () => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  initialized: false,
  loading: false,
  error: null,

  init: async () => {
    try {
      const user = await getCurrentUser();
      set({ user, initialized: true });
    } catch {
      set({ user: null, initialized: true });
    }
  },

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const user = await login(username, password);
      set({ user });
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "Login failed" });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  register: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const user = await register(username, password);
      set({ user });
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "Registration failed" });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  logout: async () => {
    try {
      await logout();
    } finally {
      set({ user: null });
    }
  },

  clearError: () => set({ error: null }),
}));
