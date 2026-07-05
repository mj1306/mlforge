import { useEffect, useRef, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { subscribeToJobStream } from "../../../api/client";
import type { JobRecord } from "../../../api/types";
import { MetricCard, ValidationMetric } from "../../../components/training";

interface TrainStepProps {
  jobId: string;
  onComplete: () => void;
}

type SelectedMetric = "box_loss" | "cls_loss" | "dfl_loss" | "all";
type ViewMode = "live" | "history";
type LossPoint = { x: number; box_loss: number; cls_loss: number; dfl_loss: number };

const STAGE_COLOR: Record<string, string> = {
  preparing: "bg-yellow-500",
  training: "bg-blue-500",
  validating: "bg-purple-500",
  complete: "bg-green-500",
  cancelled: "bg-gray-500",
  error: "bg-red-500",
};

export function TrainStep({ jobId, onComplete }: TrainStepProps) {
  const [job, setJob] = useState<JobRecord | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<SelectedMetric>("all");
  const [viewMode, setViewMode] = useState<ViewMode>("live");
  const [liveData, setLiveData] = useState<LossPoint[]>([]);
  const [history, setHistory] = useState<LossPoint[]>([]);
  const lastEpochRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    setIsConnected(true);
    const unsubscribe = subscribeToJobStream<JobRecord>(
      jobId,
      (record) => {
        setJob(record);
        const progress = record.progress;

        if (progress.epoch !== lastEpochRef.current) {
          lastEpochRef.current = progress.epoch;
          setLiveData([]);
        }

        if (progress.metrics && progress.batch !== undefined) {
          setLiveData((prev) => [
            ...prev,
            {
              x: progress.batch as number,
              box_loss: progress.metrics!.box_loss,
              cls_loss: progress.metrics!.cls_loss,
              dfl_loss: progress.metrics!.dfl_loss,
            },
          ]);
        }

        if (progress.last_epoch_metrics && progress.epoch !== undefined) {
          setHistory((prev) => [
            ...prev,
            { x: progress.epoch as number, ...progress.last_epoch_metrics! },
          ]);
        }

        if (record.status === "succeeded" || record.status === "failed" || record.status === "cancelled") {
          setTimeout(() => onComplete(), 2000);
        }
      },
      () => setIsConnected(false),
    );
    return unsubscribe;
  }, [jobId, onComplete]);

  if (!job) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4" />
        <p className="text-gray-600 text-sm">Connecting to training stream...</p>
      </div>
    );
  }

  const progress = job.progress;
  const stage = progress.stage ?? job.status;
  const hasLive = liveData.length > 0;
  const hasHistory = history.length > 0;
  const chartData = viewMode === "live" ? liveData : history;
  const metricLabel =
    selectedMetric === "all"
      ? "All Losses"
      : selectedMetric === "box_loss"
        ? "Box Loss"
        : selectedMetric === "cls_loss"
          ? "Class Loss"
          : "DFL Loss";

  return (
    <div className="space-y-4 w-full">
      <div className="bg-surface rounded-lg shadow p-4 border-l-4 border-blue-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`w-3 h-3 rounded-full ${STAGE_COLOR[stage] ?? "bg-gray-400"} ${stage === "training" ? "animate-pulse" : ""}`}
            />
            <div>
              <span className="font-bold text-gray-800 text-lg">
                {stage.charAt(0).toUpperCase() + stage.slice(1)}
              </span>
              <p className="text-sm text-gray-600 mt-1">{progress.status ?? job.status}</p>
            </div>
          </div>
          {isConnected && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs text-green-600 font-semibold">LIVE</span>
            </div>
          )}
        </div>
      </div>

      {progress.device && (
        <div
          className={`rounded-lg shadow p-3 border-l-4 ${progress.device.type === "cuda" ? "bg-green-50 border-green-500" : "bg-gray-50 border-gray-500"}`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">{progress.device.display}</span>
            {progress.device.type === "cuda" && !!progress.gpu_memory_used && (
              <span className="text-xs text-gray-600">{progress.gpu_memory_used} GB used</span>
            )}
          </div>
        </div>
      )}

      {!!progress.total_epochs && (
        <div className="bg-surface rounded-lg shadow p-4">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-bold text-gray-700">
              Epoch {progress.epoch ?? 0} / {progress.total_epochs}
            </span>
            <span className="text-xs text-gray-500">
              {Math.round(((progress.epoch ?? 0) / progress.total_epochs) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 transition-all duration-500"
              style={{ width: `${((progress.epoch ?? 0) / progress.total_epochs) * 100}%` }}
            />
          </div>
        </div>
      )}

      {stage === "training" && progress.metrics && (
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            label="Box Loss"
            value={progress.metrics.box_loss.toFixed(4)}
            color="blue"
            isSelected={selectedMetric === "box_loss"}
            onClick={() => setSelectedMetric(selectedMetric === "box_loss" ? "all" : "box_loss")}
          />
          <MetricCard
            label="Class Loss"
            value={progress.metrics.cls_loss.toFixed(4)}
            color="purple"
            isSelected={selectedMetric === "cls_loss"}
            onClick={() => setSelectedMetric(selectedMetric === "cls_loss" ? "all" : "cls_loss")}
          />
          <MetricCard
            label="DFL Loss"
            value={progress.metrics.dfl_loss.toFixed(4)}
            color="indigo"
            isSelected={selectedMetric === "dfl_loss"}
            onClick={() => setSelectedMetric(selectedMetric === "dfl_loss" ? "all" : "dfl_loss")}
          />
          <MetricCard
            label="Instances"
            value={progress.metrics.instances.toString()}
            color="green"
            isSelected={false}
            onClick={() => {}}
          />
        </div>
      )}

      {(hasLive || hasHistory) && (
        <div className="bg-surface rounded-lg shadow p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-bold text-gray-800">
              {metricLabel} - {viewMode === "live" ? "Current Epoch" : "All Epochs"}
            </h4>
            {hasHistory && (
              <button
                onClick={() => setViewMode(viewMode === "live" ? "history" : "live")}
                className="text-xs px-3 py-1 rounded font-medium bg-blue-100 text-blue-700 hover:bg-blue-200"
              >
                {viewMode === "live" ? "Show History" : "Show Live"}
              </button>
            )}
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="x" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip contentStyle={{ fontSize: "12px" }} />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              {(selectedMetric === "all" || selectedMetric === "box_loss") && (
                <Line type="monotone" dataKey="box_loss" stroke="#3B82F6" name="Box Loss" strokeWidth={2} dot={false} isAnimationActive={false} />
              )}
              {(selectedMetric === "all" || selectedMetric === "cls_loss") && (
                <Line type="monotone" dataKey="cls_loss" stroke="#8B5CF6" name="Class Loss" strokeWidth={2} dot={false} isAnimationActive={false} />
              )}
              {(selectedMetric === "all" || selectedMetric === "dfl_loss") && (
                <Line type="monotone" dataKey="dfl_loss" stroke="#6366F1" name="DFL Loss" strokeWidth={2} dot={false} isAnimationActive={false} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {progress.validation && (
        <div className="bg-surface rounded-lg shadow p-4">
          <h4 className="text-sm font-bold text-gray-800 mb-3">Validation Metrics</h4>
          <div className="grid grid-cols-2 gap-4">
            <ValidationMetric label="Precision" value={progress.validation.precision} color="blue" />
            <ValidationMetric label="Recall" value={progress.validation.recall} color="purple" />
            <ValidationMetric label="mAP@50" value={progress.validation.mAP50} color="indigo" />
            <ValidationMetric label="mAP@50-95" value={progress.validation.mAP50_95} color="green" />
          </div>
        </div>
      )}

      {job.status === "failed" && (
        <div className="bg-red-50 border-l-4 border-status-error p-4 rounded-lg">
          <h4 className="text-sm font-bold text-red-800 mb-1">Training Error</h4>
          <p className="text-sm text-red-700">{job.error}</p>
        </div>
      )}

      {job.status === "succeeded" && (
        <div className="bg-green-50 border-l-4 border-status-success p-4 rounded-lg">
          <h4 className="text-sm font-bold text-green-800 mb-1">Training Complete</h4>
          <p className="text-sm text-green-700">Successfully trained for {progress.total_epochs ?? "?"} epochs.</p>
        </div>
      )}

      {job.status === "cancelled" && (
        <div className="bg-gray-50 border-l-4 border-gray-400 p-4 rounded-lg">
          <h4 className="text-sm font-bold text-gray-800 mb-1">Training Cancelled</h4>
        </div>
      )}
    </div>
  );
}
