"use client";

import React, { useRef, useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { RefreshCw, FlipHorizontal, AlertCircle } from "lucide-react";
import { CaptureSettings } from "@/lib/types";

export interface CameraViewRef {
  capture: (className: string) => { dataUrl: string; blob: Promise<Blob | null> } | null;
}

interface CameraViewProps {
  settings: CaptureSettings;
  onUpdateSettings: (patch: Partial<CaptureSettings>) => void;
  isCapturing: boolean;
  countdownProgress: number; // 0 to 100
  flashTrigger: number;
}

export const CameraView = forwardRef<CameraViewRef, CameraViewProps>(
  ({ settings, onUpdateSettings, isCapturing, countdownProgress, flashTrigger }, ref) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [cameraError, setCameraError] = useState<string | null>(null);
    const [isFlashActive, setIsFlashActive] = useState(false);
    const [videoDimensions, setVideoDimensions] = useState<{ width: number; height: number }>({ width: 0, height: 0 });

    // Flash trigger animation
    useEffect(() => {
      if (flashTrigger > 0 && settings.flashEffect) {
        setIsFlashActive(true);
        const timer = setTimeout(() => setIsFlashActive(false), 120);
        return () => clearTimeout(timer);
      }
    }, [flashTrigger, settings.flashEffect]);

    // Setup camera stream
    useEffect(() => {
      let isMounted = true;

      async function initCamera() {
        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
        }
        setCameraError(null);

        const constraints: MediaStreamConstraints = {
          audio: false,
          video: {
            facingMode: settings.facingMode,
            width: { ideal: settings.resolution === "1080p" ? 1920 : 1280 },
            height: { ideal: settings.resolution === "1080p" ? 1080 : 720 },
          },
        };

        try {
          const newStream = await navigator.mediaDevices.getUserMedia(constraints);
          if (!isMounted) return;
          setStream(newStream);
          if (videoRef.current) {
            videoRef.current.srcObject = newStream;
          }
        } catch (err: unknown) {
          if (!isMounted) return;
          const msg = err instanceof Error ? err.message : "Cannot access camera";
          setCameraError(msg + " (กรุณากดอนุญาตสิทธิ์เข้าถึงกล้องในเบราว์เซอร์)");
        }
      }

      initCamera();

      return () => {
        isMounted = false;
        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
        }
      };
    }, [settings.facingMode, settings.resolution]);

    // Handle video metadata
    const handleLoadedMetadata = () => {
      if (videoRef.current) {
        setVideoDimensions({
          width: videoRef.current.videoWidth,
          height: videoRef.current.videoHeight,
        });
      }
    };

    // Imperative capture method
    useImperativeHandle(ref, () => ({
      capture: () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas || video.videoWidth === 0) return null;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return null;

        // Apply mirror if enabled
        if (settings.mirror) {
          ctx.translate(canvas.width, 0);
          ctx.scale(-1, 1);
        }

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
        const blobPromise = new Promise<Blob | null>((resolve) => {
          canvas.toBlob((b) => resolve(b), "image/jpeg", 0.92);
        });

        return { dataUrl, blob: blobPromise };
      },
    }));

    const toggleFacingMode = () => {
      onUpdateSettings({
        facingMode: settings.facingMode === "user" ? "environment" : "user",
        // Automatically mirror front camera, unmirror back camera
        mirror: settings.facingMode === "user" ? false : true,
      });
    };

    const toggleMirror = () => {
      onUpdateSettings({ mirror: !settings.mirror });
    };

    return (
      <div className="relative w-full aspect-video md:aspect-[4/3] lg:aspect-video bg-[#0D1017] rounded-2xl overflow-hidden border border-white/10 shadow-2xl flex items-center justify-center">
        {/* Hidden Canvas for High-Res Capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Camera Error State */}
        {cameraError ? (
          <div className="flex flex-col items-center justify-center p-6 text-center max-w-md">
            <div className="w-16 h-16 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mb-4">
              <AlertCircle size={32} />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">ไม่สามารถเปิดกล้องได้</h3>
            <p className="text-sm text-gray-400 mb-6">{cameraError}</p>
            <button
              onClick={() => {
                setCameraError(null);
                window.location.reload();
              }}
              className="px-5 py-2.5 bg-[#3E6AE1] hover:bg-blue-600 text-white rounded-lg font-medium transition-all"
            >
              ลองใหม่อีกครั้ง
            </button>
          </div>
        ) : (
          <>
            {/* Live Video Feed */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={handleLoadedMetadata}
              className={`w-full h-full object-cover transition-transform duration-300 ${
                settings.mirror ? "scale-x-[-1]" : ""
              }`}
            />

            {/* Shutter Flash Animation Overlay */}
            <div
              className={`absolute inset-0 bg-white pointer-events-none transition-opacity duration-100 ${
                isFlashActive ? "opacity-80" : "opacity-0"
              }`}
            />

            {/* Top HUD Bar */}
            <div className="absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none">
              <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                </span>
                <span className="text-xs font-semibold text-white tracking-wide">
                  {isCapturing ? "CAPTURING" : "LIVE"}
                </span>
                {videoDimensions.width > 0 && (
                  <span className="text-[11px] text-gray-400 border-l border-white/20 pl-2">
                    {videoDimensions.width}x{videoDimensions.height}
                  </span>
                )}
              </div>

              {/* Camera Quick Controls */}
              <div className="flex items-center gap-1.5 pointer-events-auto">
                <button
                  onClick={toggleMirror}
                  title="สลับโหมดกระจก (Mirror)"
                  className={`p-2 rounded-full border transition-all ${
                    settings.mirror
                      ? "bg-blue-500/20 border-blue-500/40 text-blue-300"
                      : "bg-black/60 border-white/10 text-gray-400 hover:text-white"
                  }`}
                >
                  <FlipHorizontal size={16} />
                </button>
                <button
                  onClick={toggleFacingMode}
                  title="สลับกล้องหน้า/หลัง"
                  className="p-2 bg-black/60 hover:bg-black/80 text-gray-300 hover:text-white rounded-full border border-white/10 transition-all active:scale-95"
                >
                  <RefreshCw size={16} />
                </button>
              </div>
            </div>

            {/* Auto Capture Countdown Progress Bar at Bottom of Video */}
            {isCapturing && (
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-black/40 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-emerald-400 transition-all duration-75 ease-linear"
                  style={{ width: `${countdownProgress}%` }}
                />
              </div>
            )}
          </>
        )}
      </div>
    );
  }
);

CameraView.displayName = "CameraView";
