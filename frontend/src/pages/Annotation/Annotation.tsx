import { CheckCircle2, ExternalLink, Loader2, XCircle } from "lucide-react";
import { useEffect, useRef } from "react";
import { Button, Card } from "../../components/ui";
import { useCvatStore } from "../../store/useCvatStore";

const POLL_INTERVAL_MS = 2000;

const STATE_LABEL: Record<string, string> = {
  stopped: "Stopped",
  starting: "Starting...",
  running: "Running",
  stopping: "Stopping...",
  error: "Error",
};

export function Annotation() {
  const { status, loading, error, refresh, start, stop } = useCvatStore();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (status.state === "starting" || status.state === "stopping") {
      pollRef.current = setInterval(refresh, POLL_INTERVAL_MS);
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [status.state, refresh]);

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 p-8">
      <Card className="max-w-lg w-full text-center space-y-4">
        <h2 className="text-xl font-bold text-brand">CVAT Annotation Tool</h2>
        <p className="text-sm text-gray-600">
          Launch a local CVAT instance (via Docker Compose) to annotate images before training.
        </p>

        <div className="flex items-center justify-center gap-2 py-2">
          {status.state === "running" && <CheckCircle2 className="w-5 h-5 text-status-success" />}
          {(status.state === "starting" || status.state === "stopping") && (
            <Loader2 className="w-5 h-5 text-status-info animate-spin" />
          )}
          {status.state === "error" && <XCircle className="w-5 h-5 text-status-error" />}
          <span className="font-medium text-gray-800">{STATE_LABEL[status.state] ?? status.state}</span>
        </div>

        {error && <p className="text-sm text-status-error">{error}</p>}

        <div className="flex items-center justify-center gap-3">
          {status.state === "stopped" || status.state === "error" ? (
            <Button onClick={start} loading={loading}>
              Launch CVAT
            </Button>
          ) : (
            <Button variant="outline" onClick={stop} loading={loading} disabled={status.state === "starting"}>
              Stop CVAT
            </Button>
          )}
          {status.state === "running" && status.url && (
            <a
              href={status.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 px-4 py-2 rounded font-medium bg-brand-secondary text-white hover:bg-brand-secondary-hover"
            >
              Open CVAT <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>

        <p className="text-xs text-gray-400">
          First launch downloads CVAT's Docker images and can take a few minutes.
        </p>
      </Card>
    </div>
  );
}
