export * from './types';
export * from './yolo';
export * from './resnet';
export * from './mobilenet';

import { yoloModels } from './yolo';
import { resnetModels } from './resnet';
import { mobilenetModels } from './mobilenet';
import type { ModelOption, SubmodelSpec } from './types';

export const allModels: Record<string, ModelOption[]> = {
  YOLO: yoloModels,
  ResNet: resnetModels,
  MobileNet: mobilenetModels,
};

// Helper function to get all submodel names for a model
export function getSubmodelNames(modelName: string, modelFamily: string): string[] {
  const family = allModels[modelFamily];
  const model = family?.find((m) => m.name === modelName);
  return model ? Object.keys(model.submodels) : [];
}

// Helper function to get specific submodel details
export function getSubmodelDetails(
  modelName: string,
  modelFamily: string,
  submodelName: string
): SubmodelSpec | undefined {
  const family = allModels[modelFamily];
  const model = family?.find((m) => m.name === modelName);
  return model?.submodels[submodelName];
}

export default allModels;
