import { Camera, CameraOff, Loader2, Sparkles } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Card } from "../../components/ui";
import { ROUTES } from "../../constants/routes";
import { useAuthStore } from "../../store/useAuthStore";
import {
  GESTURE_MEMES,
  drawHands,
  createGestureRecognizer,
  type GestureRecognizerLike,
} from "./gestureRecognition";

type DemoState = "idle" | "loading" | "running" | "error";

interface FloatingEmoji {
  id: number;
  emoji: string;
  /** percentage of the video width/height where the emoji spawns */
  x: number;
  y: number;
}

/** How long a gesture must be held before it fires (avoids flicker spam). */
const GESTURE_HOLD_MS = 250;
/** Cooldown between emoji bursts for the same held gesture. */
const BURST_COOLDOWN_MS = 900;

export function LiveDemo() {
  const user = useAuthStore((s) => s.user);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const recognizerRef = useRef<GestureRecognizerLike | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const rafRef = useRef<number>(0);
  const gestureSinceRef = useRef<{ name: string; at: number; lastBurst: number }>({
    name: "",
    at: 0,
    lastBurst: 0,
  });
  const emojiIdRef = useRef(0);

  const [state, setState] = useState<DemoState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentGesture, setCurrentGesture] = useState<string | null>(null);
  const [floating, setFloating] = useState<FloatingEmoji[]>([]);

  const stop = useCallback(() => {
    cancelAnimationFrame(rafRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    recognizerRef.current?.close();
    recognizerRef.current = null;
    setState("idle");
    setCurrentGesture(null);
    setFloating([]);
  }, []);

  useEffect(() => stop, [stop]);

  const spawnBurst = useCallback((emoji: string, x: number, y: number) => {
    const burst: FloatingEmoji[] = Array.from({ length: 5 }, () => ({
      id: emojiIdRef.current++,
      emoji,
      x: x + (Math.random() * 16 - 8),
      y: y + (Math.random() * 10 - 5),
    }));
    setFloating((prev) => [...prev.slice(-20), ...burst]);
    // matches the float-up animation duration below
    setTimeout(() => {
      setFloating((prev) => prev.filter((f) => !burst.some((b) => b.id === f.id)));
    }, 1800);
  }, []);

  const start = useCallback(async () => {
    setState("loading");
    setErrorMessage(null);
    try {
      const [stream, recognizer] = await Promise.all([
        navigator.mediaDevices.getUserMedia({ video: { width: 960, height: 540 } }),
        createGestureRecognizer(),
      ]);
      streamRef.current = stream;
      recognizerRef.current = recognizer;

      const video = videoRef.current!;
      video.srcObject = stream;
      await video.play();

      setState("running");

      let lastVideoTime = -1;
      const loop = () => {
        const canvas = canvasRef.current;
        const rec = recognizerRef.current;
        if (!canvas || !rec || video.readyState < 2) {
          rafRef.current = requestAnimationFrame(loop);
          return;
        }
        if (video.currentTime !== lastVideoTime) {
          lastVideoTime = video.currentTime;
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          const result = rec.recognizeForVideo(video, performance.now());
          const ctx = canvas.getContext("2d")!;
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          drawHands(ctx, result.landmarks);

          const top = result.gestures[0]?.[0];
          const meme = top && top.categoryName !== "None" ? GESTURE_MEMES[top.categoryName] : undefined;
          setCurrentGesture(meme ? top.categoryName : null);

          const now = performance.now();
          const held = gestureSinceRef.current;
          if (meme && top) {
            if (held.name !== top.categoryName) {
              gestureSinceRef.current = { name: top.categoryName, at: now, lastBurst: 0 };
            } else if (now - held.at > GESTURE_HOLD_MS && now - held.lastBurst > BURST_COOLDOWN_MS) {
              held.lastBurst = now;
              const wrist = result.landmarks[0]?.[0];
              // mirror x because the video is mirrored
              spawnBurst(meme.emoji, wrist ? (1 - wrist.x) * 100 : 50, wrist ? wrist.y * 100 : 50);
            }
          } else {
            gestureSinceRef.current = { name: "", at: 0, lastBurst: 0 };
          }
        }
        rafRef.current = requestAnimationFrame(loop);
      };
      rafRef.current = requestAnimationFrame(loop);
    } catch (err) {
      stop();
      setState("error");
      setErrorMessage(
        err instanceof DOMException && err.name === "NotAllowedError"
          ? "Camera access was denied. Allow camera access in your browser and try again."
          : `Could not start the demo: ${err instanceof Error ? err.message : String(err)}. Note: the gesture model is fetched from a CDN, so the demo needs internet access the first time.`,
      );
    }
  }, [spawnBurst, stop]);

  const activeMeme = currentGesture ? GESTURE_MEMES[currentGesture] : null;

  return (
    <div className="max-w-4xl w-full mx-auto px-6 py-10 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-brand">Live hand-gesture demo</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          This is a pretrained computer-vision model (Google MediaPipe) running{" "}
          <span className="font-medium">entirely in your browser</span> — no upload, nothing
          leaves your device. Show a gesture to the camera: 👍 ✌️ ✋ ✊ ☝️ 🤟 👎
        </p>
      </div>

      <div className="relative mx-auto max-w-3xl rounded-xl overflow-hidden bg-gray-900 aspect-video shadow-lg">
        {/* mirrored so it behaves like a mirror */}
        <video ref={videoRef} className="absolute inset-0 w-full h-full object-cover -scale-x-100" playsInline muted />
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full object-cover -scale-x-100" />

        {floating.map((f) => (
          <span
            key={f.id}
            className="absolute text-5xl animate-float-up pointer-events-none select-none"
            style={{ left: `${f.x}%`, top: `${f.y}%` }}
          >
            {f.emoji}
          </span>
        ))}

        {activeMeme && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 text-white px-4 py-2 rounded-full text-lg font-medium backdrop-blur-sm">
            {activeMeme.emoji} {activeMeme.caption}
          </div>
        )}

        {state !== "running" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-white/90">
            {state === "loading" ? (
              <>
                <Loader2 className="w-10 h-10 animate-spin" />
                <p className="text-sm">Loading camera and gesture model…</p>
              </>
            ) : (
              <>
                <Camera className="w-12 h-12" />
                <Button onClick={start} size="lg">
                  Start camera
                </Button>
                <p className="text-xs text-white/60">Video stays on your device.</p>
              </>
            )}
          </div>
        )}
      </div>

      {errorMessage && <p className="text-sm text-status-error text-center">{errorMessage}</p>}

      <div className="flex justify-center gap-3">
        {state === "running" && (
          <Button variant="outline" onClick={stop}>
            <span className="inline-flex items-center gap-2">
              <CameraOff className="w-4 h-4" /> Stop camera
            </span>
          </Button>
        )}
      </div>

      <Card className="max-w-3xl mx-auto">
        <div className="flex items-start gap-3">
          <Sparkles className="w-6 h-6 text-brand shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-gray-800 mb-1">This is what you can build</h3>
            <p className="text-sm text-gray-600">
              Gesture recognition like this is just a trained vision model. MLForge gives you the
              same workflow for your own ideas: upload or annotate images, pick a YOLO variant,
              and train it on your data — then watch metrics stream live.{" "}
              {user ? (
                <Link to={ROUTES.workspace} className="text-brand font-medium hover:underline">
                  Open the Workspace →
                </Link>
              ) : (
                <Link to={ROUTES.login} className="text-brand font-medium hover:underline">
                  Create a free account to train your own →
                </Link>
              )}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
