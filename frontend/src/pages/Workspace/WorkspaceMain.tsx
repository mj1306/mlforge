import { Save, Upload } from "lucide-react";
import { useState } from "react";
import * as trainingApi from "../../api/training";
import type { DatasetUploadResult, ImageProcessingSettings } from "../../api/types";
import { Button } from "../../components/ui";
import { useAppStore } from "../../store/useAppStore";
import { saveProjectToFile, loadProjectFromFile } from "../../utils/projectFile";
import { DEFAULT_SETTINGS, ImageProcessingStep } from "./steps/ImageProcessingStep";
import { HyperParametersStep, type Hyperparams } from "./steps/HyperParametersStep";
import { SelectModelStep } from "./steps/SelectModelStep";
import { TrainStep } from "./steps/TrainStep";
import { UploadDatasetStep } from "./steps/UploadDatasetStep";
import type { ModelFamily } from "../../config/models";
import { getSubmodelDetails } from "../../config/models";

interface WorkspaceProjectFile {
  version: 1;
  step: Step;
  modelName: string;
  submodel: string;
  dataset: DatasetUploadResult | null;
  processingSettings: ImageProcessingSettings;
  hyperparams: Hyperparams;
}

const STEPS = ["Select Model", "Upload Dataset", "Image Processing", "Hyperparameters", "Train"] as const;
type Step = (typeof STEPS)[number];

const DEFAULT_HYPERPARAMS: Hyperparams = { epochs: 30, batch: 16, imgsz: 640, lr0: 0.01 };

export function WorkspaceMain() {
  const [step, setStep] = useState<Step>("Select Model");
  const [family] = useState<ModelFamily>("YOLO");
  const [modelName, setModelName] = useState("YOLOv8");
  const [submodel, setSubmodel] = useState("n");
  const [dataset, setDataset] = useState<DatasetUploadResult | null>(null);
  const [processingSettings, setProcessingSettings] = useState<ImageProcessingSettings>(DEFAULT_SETTINGS);
  const [hyperparams, setHyperparams] = useState<Hyperparams>(DEFAULT_HYPERPARAMS);
  const [jobId, setJobId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  const training = useAppStore((s) => s.training);
  const setTraining = useAppStore((s) => s.setTraining);
  const setCurrentModel = useAppStore((s) => s.setCurrentModel);

  function goToStep(target: Step) {
    setStep(target);
  }

  function nextStep() {
    const index = STEPS.indexOf(step);
    if (index < STEPS.length - 1) setStep(STEPS[index + 1]);
  }

  async function handleStartTraining() {
    if (!dataset) return;
    setStartError(null);
    setTraining(true);
    setCurrentModel(modelName);
    const filename = getSubmodelDetails(modelName, family, submodel)?.filename ?? "yolov8n.pt";
    try {
      const { job_id } = await trainingApi.startTraining({
        model: filename,
        dataset_id: dataset.dataset_id,
        epochs: hyperparams.epochs,
        batch: hyperparams.batch,
        imgsz: hyperparams.imgsz,
        lr0: hyperparams.lr0,
      });
      setJobId(job_id);
    } catch (err) {
      setStartError(err instanceof Error ? err.message : "Failed to start training");
      setTraining(false);
      setCurrentModel(null);
    }
  }

  async function handleSave() {
    const project: WorkspaceProjectFile = {
      version: 1,
      step,
      modelName,
      submodel,
      dataset,
      processingSettings,
      hyperparams,
    };
    await saveProjectToFile(project, `${modelName}-project.json`);
  }

  async function handleLoad() {
    const project = await loadProjectFromFile<WorkspaceProjectFile>();
    if (!project) return;
    setStep(project.step);
    setModelName(project.modelName);
    setSubmodel(project.submodel);
    setDataset(project.dataset);
    setProcessingSettings(project.processingSettings);
    setHyperparams(project.hyperparams);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center px-6 py-3 bg-surface border-b-2 border-brand">
        <h1 className="text-xl font-bold text-brand">{modelName} Training Workspace</h1>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={handleLoad}>
            <Upload className="w-4 h-4 inline mr-1" /> Load
          </Button>
          <Button variant="ghost" size="sm" onClick={handleSave}>
            <Save className="w-4 h-4 inline mr-1" /> Save
          </Button>
        </div>
      </div>

      <div className="flex gap-2 px-6 py-2 bg-surface-muted text-sm overflow-x-auto">
        {STEPS.map((s) => (
          <button
            key={s}
            onClick={() => goToStep(s)}
            className={`px-3 py-1 rounded-full whitespace-nowrap ${step === s ? "bg-brand text-white" : "text-gray-600 hover:bg-gray-200"}`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {step === "Select Model" && (
          <SelectModelStep
            family={family}
            modelName={modelName}
            submodel={submodel}
            onChange={(m, s) => {
              setModelName(m);
              setSubmodel(s);
            }}
          />
        )}

        {step === "Upload Dataset" && (
          <UploadDatasetStep
            onUploaded={(result) => {
              setDataset(result);
              nextStep();
            }}
          />
        )}

        {step === "Image Processing" && dataset && (
          <ImageProcessingStep
            datasetId={dataset.dataset_id}
            settings={processingSettings}
            onSettingsChange={setProcessingSettings}
            onApplied={() => nextStep()}
          />
        )}

        {step === "Hyperparameters" && (
          <HyperParametersStep values={hyperparams} onChange={setHyperparams} />
        )}

        {step === "Train" && (
          <div className="space-y-4">
            {!jobId && (
              <>
                <Button onClick={handleStartTraining} disabled={!dataset || training}>
                  Start training
                </Button>
                {startError && <p className="text-sm text-status-error">{startError}</p>}
                {!dataset && <p className="text-sm text-gray-500">Upload a dataset first.</p>}
              </>
            )}
            {jobId && (
              <TrainStep
                jobId={jobId}
                onComplete={() => {
                  setTraining(false);
                }}
              />
            )}
          </div>
        )}
      </div>

      <div className="flex justify-between px-6 py-3 border-t border-border-default bg-surface">
        <Button
          variant="ghost"
          onClick={() => goToStep(STEPS[Math.max(0, STEPS.indexOf(step) - 1)])}
          disabled={step === STEPS[0]}
        >
          Back
        </Button>
        {step !== "Train" && (
          <Button onClick={nextStep} disabled={step === "Upload Dataset" && !dataset}>
            Next
          </Button>
        )}
      </div>
    </div>
  );
}
