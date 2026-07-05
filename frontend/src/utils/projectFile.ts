// Replaces the old Electron IPC save/load (window.electronAPI.saveProject/openProject)
// with the browser-native File System Access API, falling back to a Blob
// download / <input type=file> pair on browsers that don't support it
// (Firefox, Safari).

interface FileSystemAccessWindow extends Window {
  showSaveFilePicker?: (options?: unknown) => Promise<FileSystemFileHandle>;
  showOpenFilePicker?: (options?: unknown) => Promise<FileSystemFileHandle[]>;
}

export async function saveProjectToFile(data: unknown, suggestedName = "mlforge-project.json"): Promise<void> {
  const json = JSON.stringify(data, null, 2);
  const win = window as FileSystemAccessWindow;

  if (win.showSaveFilePicker) {
    const handle = await win.showSaveFilePicker({
      suggestedName,
      types: [{ description: "MLForge project", accept: { "application/json": [".json"] } }],
    });
    const writable = await handle.createWritable();
    await writable.write(json);
    await writable.close();
    return;
  }

  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = suggestedName;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function loadProjectFromFile<T>(): Promise<T | null> {
  const win = window as FileSystemAccessWindow;

  if (win.showOpenFilePicker) {
    const [handle] = await win.showOpenFilePicker({
      types: [{ description: "MLForge project", accept: { "application/json": [".json"] } }],
    });
    const file = await handle.getFile();
    return JSON.parse(await file.text()) as T;
  }

  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/json";
    input.onchange = () => {
      const file = input.files?.[0];
      if (!file) {
        resolve(null);
        return;
      }
      file.text().then((text) => resolve(JSON.parse(text) as T));
    };
    input.click();
  });
}
