import { ScanFace, Fingerprint, AlertTriangle } from "lucide-react";
import { Card, CardTitle, KeyValue } from "./ui/Card";
import { pct, ms } from "../lib/utils";
import type { FaceAnalysis } from "../types";

const WARN_TEXT: Record<string, string> = {
  multiple_faces: "Multiple faces detected — the largest face is used as the target.",
  low_resolution_face: "The detected face is small/low-resolution; results may be less reliable.",
};

export function FaceResultCard({ face }: { face: FaceAnalysis }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card glow="blue">
        <CardTitle icon={<ScanFace size={16} className="text-accent-blue" />}>
          Face Detection
        </CardTitle>
        <KeyValue k="Status" v={face.face_detected ? "Face detected" : "No face"} />
        <KeyValue k="Faces found" v={face.face_count} />
        <KeyValue k="Confidence" v={pct(face.confidence)} />
        {face.bbox && (
          <KeyValue
            k="Bounding box"
            mono
            v={`x=${face.bbox.x}, y=${face.bbox.y}, w=${face.bbox.width}, h=${face.bbox.height}`}
          />
        )}
        <KeyValue k="Image quality" v={face.quality} />
        <KeyValue k="Dimensions" v={`${face.image_width}×${face.image_height}px`} />
      </Card>

      <Card>
        <CardTitle icon={<Fingerprint size={16} className="text-accent-purple" />}>
          Face Encoding
        </CardTitle>
        <KeyValue k="Status" v="Generated" />
        <KeyValue k="Embedding dimension" v={face.embedding_dimension} />
        <KeyValue k="Model" v={face.model} />
        <KeyValue k="Embedding ID" v={face.embedding_id} mono />
        <KeyValue k="Processing time" v={ms(face.processing_time_ms)} />
        <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
          The raw embedding vector is never exposed — only a non-invertible ID.
        </p>
      </Card>

      {face.warning && (
        <div className="md:col-span-2 flex items-center gap-2 rounded-lg border border-accent-amber/30 bg-accent-amber/5 px-4 py-2.5 text-sm text-accent-amber">
          <AlertTriangle size={16} />
          {WARN_TEXT[face.warning] ?? face.warning}
        </div>
      )}
    </div>
  );
}
