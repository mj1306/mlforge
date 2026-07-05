import { allModels, getSubmodelNames } from "../../../config/models";
import type { ModelFamily } from "../../../config/models";

interface SelectModelStepProps {
  family: ModelFamily;
  modelName: string;
  submodel: string;
  onChange: (modelName: string, submodel: string) => void;
}

const AVAILABLE_FAMILIES: ModelFamily[] = ["YOLO"]; // ResNet/MobileNet registry kept for later, not wired to training yet

export function SelectModelStep({ family, modelName, submodel, onChange }: SelectModelStepProps) {
  const models = allModels[family] ?? [];

  return (
    <div className="space-y-4">
      {!AVAILABLE_FAMILIES.includes(family) && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
          {family} training isn't wired up yet -- only YOLO trains end-to-end today.
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {models.map((model) => (
          <button
            key={model.name}
            onClick={() => onChange(model.name, Object.keys(model.submodels)[0] ?? "")}
            className={`text-left rounded-lg border-2 p-3 transition-colors ${modelName === model.name ? "border-brand bg-blue-50" : "border-border-default hover:border-brand"}`}
          >
            <div className="font-semibold text-gray-800">{model.name}</div>
            <div className="text-xs text-gray-500 mt-1">
              {model.backbone} &middot; {model.releaseYear}
            </div>
          </button>
        ))}
      </div>

      {modelName && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Variant</label>
          <div className="flex flex-wrap gap-2">
            {getSubmodelNames(modelName, family).map((name) => (
              <button
                key={name}
                onClick={() => onChange(modelName, name)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${submodel === name ? "bg-brand text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"}`}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
