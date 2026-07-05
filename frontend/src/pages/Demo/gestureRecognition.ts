import type { GestureRecognizerResult, NormalizedLandmark } from "@mediapipe/tasks-vision";

// The wasm runtime and the .task model are fetched from CDNs on first use
// (then cached by the browser). Keeping them out of the bundle keeps the app
// build small; the trade-off is that the demo page needs internet access the
// first time it runs.
// Keep this version in lockstep with the @mediapipe/tasks-vision entry in
// package.json -- the JS API and the wasm runtime must match.
const WASM_CDN = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task";

export interface GestureRecognizerLike {
  recognizeForVideo(video: HTMLVideoElement, timestampMs: number): GestureRecognizerResult;
  close(): void;
}

export async function createGestureRecognizer(): Promise<GestureRecognizerLike> {
  // Dynamic import keeps the ~700KB mediapipe JS out of the main bundle --
  // it loads only when someone actually starts the demo.
  const { FilesetResolver, GestureRecognizer } = await import("@mediapipe/tasks-vision");
  const vision = await FilesetResolver.forVisionTasks(WASM_CDN);
  return GestureRecognizer.createFromOptions(vision, {
    baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
    runningMode: "VIDEO",
    numHands: 2,
  });
}

/** The canned gestures MediaPipe's recognizer ships with, mapped to the
 * emoji/meme reactions the demo shows. */
export const GESTURE_MEMES: Record<string, { emoji: string; caption: string }> = {
  Thumb_Up: { emoji: "👍", caption: "Certified banger" },
  Thumb_Down: { emoji: "👎", caption: "Big nope" },
  Victory: { emoji: "✌️", caption: "Victory!" },
  Open_Palm: { emoji: "👋", caption: "Hello there" },
  Closed_Fist: { emoji: "✊", caption: "Power move" },
  Pointing_Up: { emoji: "☝️", caption: "One more thing…" },
  ILoveYou: { emoji: "🤟", caption: "Rock on" },
};

// MediaPipe hand-landmark connection pairs (21-point hand skeleton).
const HAND_CONNECTIONS: ReadonlyArray<readonly [number, number]> = [
  [0, 1], [1, 2], [2, 3], [3, 4], // thumb
  [0, 5], [5, 6], [6, 7], [7, 8], // index
  [5, 9], [9, 10], [10, 11], [11, 12], // middle
  [9, 13], [13, 14], [14, 15], [15, 16], // ring
  [13, 17], [17, 18], [18, 19], [19, 20], [0, 17], // pinky + palm
];

export function drawHands(
  ctx: CanvasRenderingContext2D,
  hands: NormalizedLandmark[][],
): void {
  const { width, height } = ctx.canvas;
  for (const landmarks of hands) {
    ctx.strokeStyle = "rgba(45, 27, 158, 0.9)"; // brand-secondary
    ctx.lineWidth = 3;
    for (const [a, b] of HAND_CONNECTIONS) {
      ctx.beginPath();
      ctx.moveTo(landmarks[a].x * width, landmarks[a].y * height);
      ctx.lineTo(landmarks[b].x * width, landmarks[b].y * height);
      ctx.stroke();
    }
    ctx.fillStyle = "#10b981"; // status-success
    for (const point of landmarks) {
      ctx.beginPath();
      ctx.arc(point.x * width, point.y * height, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}
