import { Download, Info, RotateCcw, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import * as processingApi from "../../../api/processing";
import type { ImageProcessingSettings } from "../../../api/types";

const DEFAULT_SETTINGS: ImageProcessingSettings = {
  brightness: 100,
  contrast: 100,
  saturation: 100,
  hue: 0,
  blur: 0,
  sharpness: 0,
  rotation: 0,
  flipHorizontal: false,
  flipVertical: false,
  grayscale: false,
  applyToCount: 10,
  applyToAll: false,
};

interface ImageProcessingStepProps {
  datasetId: string;
  settings: ImageProcessingSettings;
  onSettingsChange: (settings: ImageProcessingSettings) => void;
  onApplied: (result: { processed_images: number; output_dir: string }) => void;
}

export function ImageProcessingStep({
  datasetId,
  settings,
  onSettingsChange,
  onApplied,
}: ImageProcessingStepProps) {
  const [totalImages, setTotalImages] = useState(0);
  const [applying, setApplying] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    processingApi
      .getProcessingInfo(datasetId)
      .then((info) => setTotalImages(info.total_images))
      .catch(() => setTotalImages(0));
  }, [datasetId]);

  useEffect(() => {
    let objectUrl: string | null = null;
    processingApi
      .getRandomImage(datasetId)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      })
      .catch(() => setPreviewUrl(null));
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [datasetId]);

  function updateSetting<K extends keyof ImageProcessingSettings>(
    key: K,
    value: ImageProcessingSettings[K],
  ) {
    onSettingsChange({ ...settings, [key]: value });
  }

  async function handleApply() {
    setApplying(true);
    setError(null);
    try {
      const result = await processingApi.applyProcessing(datasetId, settings);
      onApplied(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply image processing");
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
      <div className="bg-surface-muted rounded-lg flex items-center justify-center overflow-hidden">
        {previewUrl ? (
          <img src={previewUrl} alt="Dataset preview" className="max-h-full max-w-full object-contain" />
        ) : (
          <p className="text-gray-500 text-sm p-8">No preview available</p>
        )}
      </div>

      <div className="space-y-4 h-full flex flex-col">
        <div className="flex items-center gap-2 pb-3 border-b border-border-default">
          <Settings className="w-5 h-5 text-brand" />
          <h3 className="font-semibold text-gray-800">Image Adjustments</h3>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          <div className="bg-surface rounded-lg shadow-sm p-4 border-l-4 border-brand">
            <h4 className="font-semibold text-gray-800 mb-3 text-sm">Color Adjustments</h4>
            <div className="space-y-3">
              {(
                [
                  ["brightness", 0, 200, "%"],
                  ["contrast", 0, 200, "%"],
                  ["saturation", 0, 200, "%"],
                  ["hue", -180, 180, "°"],
                ] as const
              ).map(([key, min, max, unit]) => (
                <div key={key}>
                  <div className="flex justify-between mb-1">
                    <label className="text-xs font-medium text-gray-700 capitalize">{key}</label>
                    <span className="text-xs text-brand font-semibold">
                      {settings[key]}
                      {unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={min}
                    max={max}
                    value={settings[key]}
                    onChange={(e) => updateSetting(key, Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[color:var(--color-brand)]"
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-surface rounded-lg shadow-sm p-4 border-l-4 border-brand-secondary">
            <h4 className="font-semibold text-gray-800 mb-3 text-sm">Effects</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-xs font-medium text-gray-700">Blur</label>
                  <span className="text-xs text-brand-secondary font-semibold">{settings.blur}px</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={0.1}
                  value={settings.blur}
                  onChange={(e) => updateSetting("blur", Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <ToggleRow
                label="Grayscale"
                checked={settings.grayscale}
                onChange={(v) => updateSetting("grayscale", v)}
              />
            </div>
          </div>

          <div className="bg-surface rounded-lg shadow-sm p-4 border-l-4 border-brand-secondary-hover">
            <h4 className="font-semibold text-gray-800 mb-3 text-sm">Transformations</h4>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <label className="text-xs font-medium text-gray-700">Rotation</label>
                  <span className="text-xs font-semibold">{settings.rotation}&deg;</span>
                </div>
                <input
                  type="range"
                  min={-180}
                  max={180}
                  value={settings.rotation}
                  onChange={(e) => updateSetting("rotation", Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => updateSetting("flipHorizontal", !settings.flipHorizontal)}
                  className={`p-2 rounded-lg font-medium text-xs transition-colors ${settings.flipHorizontal ? "bg-brand-secondary-hover text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
                >
                  Flip H
                </button>
                <button
                  onClick={() => updateSetting("flipVertical", !settings.flipVertical)}
                  className={`p-2 rounded-lg font-medium text-xs transition-colors ${settings.flipVertical ? "bg-brand-secondary-hover text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
                >
                  Flip V
                </button>
              </div>
            </div>
          </div>

          <div className="bg-surface rounded-lg shadow-sm p-4 border-l-4 border-brand-hover">
            <h4 className="font-semibold text-gray-800 mb-3 text-sm">Apply To</h4>
            <div className="space-y-3">
              <div className="bg-blue-50 rounded-lg p-2 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-700">Total Images:</span>
                  <span className="font-semibold text-brand">{totalImages}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Will Process:</span>
                  <span className="font-semibold text-brand-secondary">
                    {settings.applyToAll ? "All" : settings.applyToCount}
                  </span>
                </div>
              </div>
              <ToggleRow
                label="Apply to all"
                checked={settings.applyToAll}
                onChange={(v) => updateSetting("applyToAll", v)}
              />
              {!settings.applyToAll && (
                <div>
                  <div className="flex justify-between mb-1">
                    <label className="text-xs font-medium text-gray-700">Number of Images</label>
                    <span className="text-xs font-semibold">{settings.applyToCount}</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={totalImages || 100}
                    value={settings.applyToCount}
                    onChange={(e) => updateSetting("applyToCount", Number(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-3 border border-amber-200">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-amber-800">
                <p className="font-medium mb-1">Processing writes to a separate "processed/" folder</p>
                <p>Your original dataset files are never modified.</p>
              </div>
            </div>
          </div>

          {error && <p className="text-sm text-status-error">{error}</p>}
        </div>

        <div className="flex-shrink-0 space-y-2 pt-4 border-t border-border-default">
          <button
            onClick={() => onSettingsChange(DEFAULT_SETTINGS)}
            className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset All
          </button>
          <button
            onClick={handleApply}
            disabled={applying}
            className="w-full px-4 py-3 bg-gradient-to-r from-brand to-brand-secondary hover:from-brand-hover hover:to-brand-secondary-hover text-white font-semibold rounded-lg transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {applying ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Applying...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Apply Processing
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
      <label className="text-xs font-medium text-gray-700">{label}</label>
      <button
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${checked ? "bg-brand-secondary" : "bg-gray-300"}`}
      >
        <span
          className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${checked ? "translate-x-5" : "translate-x-1"}`}
        />
      </button>
    </div>
  );
}

export { DEFAULT_SETTINGS };
