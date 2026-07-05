import { Download, History, Package } from "lucide-react";
import { useEffect, useState } from "react";
import { listJobs, listModels, modelWeightsUrl } from "../../api/models";
import type { JobRecord, TrainedModel } from "../../api/types";
import { Card } from "../../components/ui";
import { useAuthStore } from "../../store/useAuthStore";

const STATUS_STYLES: Record<JobRecord["status"], string> = {
  pending: "bg-surface-muted text-gray-600",
  running: "bg-status-info/10 text-status-info",
  succeeded: "bg-status-success/10 text-status-success",
  failed: "bg-status-error/10 text-status-error",
  cancelled: "bg-surface-muted text-gray-600",
};

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function MyModels() {
  const user = useAuthStore((s) => s.user);
  const [models, setModels] = useState<TrainedModel[] | null>(null);
  const [jobs, setJobs] = useState<JobRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listModels(), listJobs()])
      .then(([m, j]) => {
        if (!cancelled) {
          setModels(m);
          setJobs(j);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="max-w-4xl w-full mx-auto px-6 py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">My models</h1>
        <p className="text-sm text-gray-600 mt-1">
          Models and training activity for <span className="font-medium">{user?.username}</span>.
          Only you can see these.
        </p>
      </div>

      {error && <p className="text-sm text-status-error">{error}</p>}

      <section>
        <h2 className="flex items-center gap-2 font-semibold text-gray-800 mb-3">
          <Package className="w-5 h-5 text-brand" /> Trained models
        </h2>
        {models === null ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : models.length === 0 ? (
          <Card>
            <p className="text-sm text-gray-600">
              No trained models yet. Finish a training run in the Workspace and the resulting
              weights will show up here, ready to download.
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {models.map((model) => (
              <Card key={model.name} className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="font-medium text-gray-800 truncate">{model.name}</p>
                  <p className="text-xs text-gray-500">
                    {formatDate(model.created_at)} · {formatSize(model.size_bytes)}
                  </p>
                </div>
                <a
                  href={modelWeightsUrl(model.name)}
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:underline shrink-0"
                >
                  <Download className="w-4 h-4" /> best.pt
                </a>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="flex items-center gap-2 font-semibold text-gray-800 mb-3">
          <History className="w-5 h-5 text-brand-secondary" /> Recent activity
        </h2>
        {jobs === null ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : jobs.length === 0 ? (
          <Card>
            <p className="text-sm text-gray-600">
              No activity yet this session. Training, image-processing, and CVAT jobs you start
              will be listed here. (Job history resets when the backend restarts; trained models
              above are permanent.)
            </p>
          </Card>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <Card key={job.id} className="flex items-center justify-between gap-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-800 capitalize">
                    {job.kind.replace("_", " ")}
                  </p>
                  <p className="text-xs text-gray-500">{formatDate(job.created_at)}</p>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full shrink-0 ${STATUS_STYLES[job.status]}`}
                >
                  {job.status}
                </span>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
