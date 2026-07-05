import { Input } from "../../../components/ui";

export interface Hyperparams {
  epochs: number;
  batch: number;
  imgsz: number;
  lr0: number;
}

interface HyperParametersStepProps {
  values: Hyperparams;
  onChange: (values: Hyperparams) => void;
}

const FIELDS: Array<{ key: keyof Hyperparams; label: string; step?: number }> = [
  { key: "epochs", label: "Epochs" },
  { key: "batch", label: "Batch size" },
  { key: "imgsz", label: "Image size" },
  { key: "lr0", label: "Initial learning rate", step: 0.001 },
];

export function HyperParametersStep({ values, onChange }: HyperParametersStepProps) {
  return (
    <div className="grid grid-cols-2 gap-4 max-w-md">
      {FIELDS.map(({ key, label, step }) => (
        <Input
          key={key}
          label={label}
          type="number"
          step={step}
          value={values[key]}
          onChange={(e) => onChange({ ...values, [key]: Number(e.target.value) })}
        />
      ))}
    </div>
  );
}
