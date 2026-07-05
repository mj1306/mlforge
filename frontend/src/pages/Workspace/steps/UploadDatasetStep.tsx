import { UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import * as datasetsApi from "../../../api/datasets";
import { Button } from "../../../components/ui";
import { useApi } from "../../../hooks/useApi";
import type { DatasetUploadResult } from "../../../api/types";

interface UploadDatasetStepProps {
  onUploaded: (result: DatasetUploadResult, file: File) => void;
}

export function UploadDatasetStep({ onUploaded }: UploadDatasetStepProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { loading, error, execute } = useApi<DatasetUploadResult>();

  async function handleUpload() {
    if (!selectedFile) return;
    try {
      const result = await execute(() => datasetsApi.uploadDataset(selectedFile));
      onUploaded(result, selectedFile);
    } catch {
      // error state is already tracked by useApi and rendered below
    }
  }

  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
      <UploadCloud className="w-12 h-12 text-brand" />
      <h3 className="text-lg font-semibold text-gray-800">Upload your dataset</h3>
      <p className="text-sm text-gray-500 max-w-md">
        Upload a zip archive of YOLO-format images and labels, or a folder already containing a
        data.yaml. We'll auto-detect classes and generate data.yaml if it's missing.
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
      />
      <Button variant="outline" onClick={() => inputRef.current?.click()}>
        {selectedFile ? selectedFile.name : "Choose dataset .zip"}
      </Button>
      {error && <p className="text-sm text-status-error">{error}</p>}
      <Button onClick={handleUpload} disabled={!selectedFile} loading={loading}>
        Upload and continue
      </Button>
    </div>
  );
}
