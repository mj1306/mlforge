import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import * as datasetsApi from "../../../api/datasets";
import { UploadDatasetStep } from "./UploadDatasetStep";

describe("UploadDatasetStep", () => {
  it("uploads the selected file and calls onUploaded with the result", async () => {
    const uploadResult = {
      dataset_id: "sample-abc123",
      yaml_path: "/data/datasets/sample-abc123/data.yaml",
      classes: { 0: "cat", 1: "dog" },
    };
    vi.spyOn(datasetsApi, "uploadDataset").mockResolvedValue(uploadResult);
    const onUploaded = vi.fn();

    render(<UploadDatasetStep onUploaded={onUploaded} />);

    const file = new File(["dummy"], "dataset.zip", { type: "application/zip" });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload and continue/i }));

    await waitFor(() => {
      expect(onUploaded).toHaveBeenCalledWith(uploadResult, file);
    });
    expect(datasetsApi.uploadDataset).toHaveBeenCalledWith(file);
  });

  it("disables the upload button until a file is chosen", () => {
    render(<UploadDatasetStep onUploaded={vi.fn()} />);

    expect(screen.getByRole("button", { name: /upload and continue/i })).toBeDisabled();
  });

  it("shows an error message when the upload fails", async () => {
    vi.spyOn(datasetsApi, "uploadDataset").mockRejectedValue(new Error("Invalid zip archive"));
    render(<UploadDatasetStep onUploaded={vi.fn()} />);

    const file = new File(["dummy"], "dataset.zip", { type: "application/zip" });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: /upload and continue/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid zip archive")).toBeInTheDocument();
    });
  });
});
