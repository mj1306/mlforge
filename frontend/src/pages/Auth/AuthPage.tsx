import { LogIn, UserPlus } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, Input } from "../../components/ui";
import { ROUTES } from "../../constants/routes";
import { useAuthStore } from "../../store/useAuthStore";

type Mode = "login" | "register";

export function AuthPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const { login, register, loading, error, clearError } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? ROUTES.home;

  const switchMode = (next: Mode) => {
    setMode(next);
    setLocalError(null);
    clearError();
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);
    if (mode === "register") {
      // Mirror the backend's RegisterRequest constraints so the user gets a
      // readable message instead of a raw 422.
      if (!/^[a-zA-Z0-9_-]{3,32}$/.test(username)) {
        setLocalError(
          "Username must be 3–32 characters, using only letters, numbers, hyphens, or underscores — no spaces or email addresses.",
        );
        return;
      }
      if (password !== confirm) {
        setLocalError("Passwords do not match");
        return;
      }
      if (password.length < 8) {
        setLocalError("Password must be at least 8 characters");
        return;
      }
    }
    try {
      if (mode === "login") {
        await login(username, password);
      } else {
        await register(username, password);
      }
      navigate(from, { replace: true });
    } catch {
      // error is surfaced via the store
    }
  };

  return (
    <div className="flex flex-1 items-center justify-center px-6 py-12">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-brand">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            {mode === "login"
              ? "Sign in to see your datasets, training runs, and models."
              : "Your datasets and trained models are private to your account."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            placeholder="3-32 characters, letters/numbers/-/_"
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            placeholder={mode === "register" ? "At least 8 characters" : undefined}
            required
          />
          {mode === "register" && (
            <Input
              label="Confirm password"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
            />
          )}

          {(localError || error) && (
            <p className="text-sm text-status-error">{localError ?? error}</p>
          )}

          <Button type="submit" fullWidth loading={loading}>
            <span className="inline-flex items-center gap-2">
              {mode === "login" ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
              {mode === "login" ? "Sign in" : "Create account"}
            </span>
          </Button>
        </form>

        <p className="text-sm text-gray-600 text-center mt-6">
          {mode === "login" ? (
            <>
              New to MLForge?{" "}
              <button
                type="button"
                className="text-brand font-medium hover:underline"
                onClick={() => switchMode("register")}
              >
                Create an account
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="text-brand font-medium hover:underline"
                onClick={() => switchMode("login")}
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </Card>
    </div>
  );
}
