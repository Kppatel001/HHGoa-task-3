import { useCallback, useRef, useState } from "react";
import { UploadCloud, Camera, X, ImageIcon } from "lucide-react";
import { cn } from "../lib/utils";

const ACCEPT = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const MAX_MB = 10;

interface Meta {
  width: number;
  height: number;
  sizeKb: number;
}

export function FaceUploader({
  file,
  onFile,
  disabled,
}: {
  file: File | null;
  onFile: (f: File | null) => void;
  disabled?: boolean;
}) {
  const [drag, setDrag] = useState(false);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [warn, setWarn] = useState<string | null>(null);
  const [camOn, setCamOn] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const accept = useCallback(
    (f: File) => {
      setWarn(null);
      if (!ACCEPT.includes(f.type)) {
        setWarn("Unsupported file type. Use JPG, PNG or WebP.");
        return;
      }
      if (f.size > MAX_MB * 1024 * 1024) {
        setWarn(`File exceeds ${MAX_MB} MB.`);
        return;
      }
      const url = URL.createObjectURL(f);
      setPreview(url);
      const img = new Image();
      img.onload = () => {
        setMeta({ width: img.width, height: img.height, sizeKb: Math.round(f.size / 1024) });
        if (Math.min(img.width, img.height) < 200) {
          setWarn("Low-resolution image — detection may be less reliable.");
        }
      };
      img.src = url;
      onFile(f);
    },
    [onFile]
  );

  const stopCam = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCamOn(false);
  };

  const startCam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setCamOn(true);
      setTimeout(() => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      }, 50);
    } catch {
      setWarn("Camera unavailable or permission denied.");
    }
  };

  const snap = () => {
    const v = videoRef.current;
    if (!v) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d")?.drawImage(v, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) accept(new File([blob], `capture_${Date.now()}.png`, { type: "image/png" }));
      stopCam();
    }, "image/png");
  };

  const clear = () => {
    setPreview(null);
    setMeta(null);
    setWarn(null);
    onFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  if (camOn) {
    return (
      <div className="glass p-4">
        <video ref={videoRef} autoPlay playsInline className="mx-auto max-h-[360px] rounded-lg" />
        <div className="mt-4 flex justify-center gap-3">
          <button className="btn-primary" onClick={snap}>
            <Camera size={16} /> Capture
          </button>
          <button className="btn-ghost" onClick={stopCam}>
            <X size={16} /> Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (disabled) return;
          const f = e.dataTransfer.files?.[0];
          if (f) accept(f);
        }}
        className={cn(
          "relative flex min-h-[280px] flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition",
          drag ? "border-accent-blue bg-accent-blue/5" : "border-white/15 bg-white/[0.02]",
          disabled && "pointer-events-none opacity-60"
        )}
      >
        {preview ? (
          <div className="w-full">
            <div className="relative mx-auto max-w-md">
              <img src={preview} alt="preview" className="mx-auto max-h-[320px] rounded-xl" />
              <button
                onClick={clear}
                className="absolute right-2 top-2 rounded-full bg-base-900/80 p-1.5 text-slate-200 hover:bg-base-900"
              >
                <X size={16} />
              </button>
            </div>
            {meta && (
              <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
                <span className="chip bg-white/5">
                  <ImageIcon size={12} /> {meta.width}×{meta.height}px
                </span>
                <span className="chip bg-white/5">{meta.sizeKb} KB</span>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-accent-blue/10">
              <UploadCloud className="text-accent-blue" size={26} />
            </div>
            <p className="text-sm font-medium text-slate-200">
              Drag & drop a face image, or click to upload
            </p>
            <p className="mt-1 text-xs text-slate-500">JPG · JPEG · PNG · WebP · up to {MAX_MB} MB</p>
            <div className="mt-5 flex gap-3">
              <button className="btn-primary" onClick={() => inputRef.current?.click()}>
                <UploadCloud size={16} /> Choose file
              </button>
              <button className="btn-ghost" onClick={startCam}>
                <Camera size={16} /> Use camera
              </button>
            </div>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT.join(",")}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) accept(f);
          }}
        />
      </div>
      {warn && <p className="mt-3 text-sm text-accent-amber">{warn}</p>}
    </div>
  );
}
