export type SubmodelSpec = {
  filename: string;
  parameters?: number;
  layers?: number;
  flops?: string;
  mAP?: string;
  inputSize?: string;
  description?: string;
  speed?: string;
  memoryUsage?: string;
};

export type ModelOption = {
  name: string;
  submodels: Record<string, SubmodelSpec>;
  image?: string;
  description?: string;
  backbone?: string;
  neck?: string;
  head?: string;
  releaseYear?: number;
  framework?: string;
};

export type ModelFamily = "YOLO" | "ResNet" | "MobileNet";
