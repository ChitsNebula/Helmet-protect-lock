"use client";

import React, { useRef, useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { RefreshCw, FlipHorizontal, AlertCircle, X, Play, Pause, Square, CheckCircle2 } from "lucide-react";
import { CaptureSettings } from "@/lib/types";

export interface CameraViewRef {
  capture: (className: string) => { dataUrl: string; blob: Promise<Blob | null> } | null;
}

interface CameraViewProps {
  settings: CaptureSettings;
  onUpdateSettings: (patch: Partial<CaptureSettings>) => void;
  isCapturing: boolean;
  isPaused: boolean;
  isFullscreen: boolean;
  onCloseFullscreen: () => void;
  onStartCapture: () => void;
  onPauseCapture: () => void;
  onResumeCapture: () => void;
  onStopCapture: () => void;
  capturedCount: number;
  countdownProgress: number;
  flashTrigger: number;
}

export const CameraView = forwardRef<CameraViewRef, CameraViewProps>(
  (
    {
      settings,
      onUpdateSettings,
      isCapturing,
      isPaused,
      isFullscreen,
      onCloseFullscreen,
      onStartCapture,
      onPauseCapture,
      onResumeCapture,
      onStopCapture,
      capturedCount,
      countdownProgress,
      flashTrigger,
    },
    ref
  ) => {
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

    // Setup camera stream with unconstrained natural aspect ratio
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
            width: { ideal: 1920 },
            height: { ideal: 1080 },
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
    }, [settings.facingMode]);

    const handleLoadedMetadata = () => {
      if (videoRef.current) {
        setVideoDimensions({
          width: videoRef.current.videoWidth,
          height: videoRef.current.videoHeight,
        });
      }
    };

    useImperativeHandle(ref, () => ({
      capture: () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas || video.videoWidth === 0) return null;

        // Use natural camera resolution without distortion
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        if (!ctx) return null;

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
        mirror: settings.facingMode === "user" ? false : true,
      });
    };

    const toggleMirror = () => {
      onUpdateSettings({ mirror: !settings.mirror });
    };

    return (
      <div
        className={`relative transition-all duration-300 overflow-hidden bg-[#0D1017] flex items-center justify-center ${
          isFullscreen
            ? "fixed inset-0 z-50 w-screen h-screen bg-black"
            : "w-full min-h-[300px] max-h-[68vh] rounded-2xl border border-white/10 shadow-2xl"
        }`}
      >
        <canvas ref={canvasRef} className="hidden" />

        {cameraError ? (
          <div className="flex flex-col items-center justify-center p-6 text-center max-w-md">
            <div className="w-16 h-16 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mb-4">
              <AlertCircle size={32} />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">ไม่สามารถเปิดกล้องได้</h3>
            <p className="text-sm text-gray-400 mb-6">{cameraError}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 bg-[#3E6AE1] hover:bg-blue-600 text-white rounded-lg font-medium transition-all"
            >
              ลองใหม่อีกครั้ง
            </button>
          </div>
        ) : (
          <>
            {/* Native Video Feed - Adapts to Portrait or Landscape */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onLoadedMetadata={handleLoadedMetadata}
              className={`w-full h-full object-contain transition-transform duration-300 ${
                settings.mirror ? "scale-x-[-1]" : ""
              } ${isFullscreen ? "max-h-screen max-w-screen" : "max-h-[68vh]"}`}
            />

            {/* Shutter Flash Animation Overlay */}
            <div
              className={`absolute inset-0 bg-white pointer-events-none transition-opacity duration-100 ${
                isFlashActive ? "opacity-80" : "opacity-0"
              }`}
            />

            {/* Top Bar Controls */}
            <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none z-10">
              <div className="flex items-center gap-2 bg-black/70 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-white/15">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
                </span>
                <span className="text-xs font-bold text-white tracking-wider">
                  {isCapturing ? "RECORDING" : "LIVE"}
                </span>
                {videoDimensions.width > 0 && (
                  <span className="text-[11px] text-gray-300 border-l border-white/20 pl-2">
                    {videoDimensions.width}x{videoDimensions.height}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 pointer-events-auto">
                <button
                  onClick={toggleMirror}
                  title="สลับโหมดกระจก (Mirror)"
                  className={`p-2.5 rounded-full border transition-all ${
                    settings.mirror
                      ? "bg-blue-500/30 border-blue-500/50 text-blue-300"
                      : "bg-black/70 border-white/15 text-gray-400 hover:text-white"
                  }`}
                >
                  <FlipHorizontal size={18} />
                </button>
                <button
                  onClick={toggleFacingMode}
                  title="สลับกล้องหน้า/หลัง"
                  className="p-2.5 bg-black/70 hover:bg-black/90 text-gray-300 hover:text-white rounded-full border border-white/15 transition-all active:scale-95"
                >
                  <RefreshCw size={18} />
                </button>
                {isFullscreen && (
                  <button
                    onClick={onCloseFullscreen}
                    title="ปิดโหมดเต็มจอ"
                    className="p-2.5 bg-rose-600/80 hover:bg-rose-600 text-white rounded-full shadow-lg transition-all active:scale-95 ml-2"
                  >
                    <X size={20} />
                  </button>
                )}
              </div>
            </div>

            {/* FULLSCREEN MODE: Big Start Button in Center */}
            {isFullscreen && !isCapturing && (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-black/40 backdrop-blur-[2px] z-20">
                <div className="text-center flex flex-col items-center gap-4 bg-black/80 p-6 sm:p-8 rounded-3xl border border-white/20 shadow-2xl max-w-sm w-full animate-in fade-in zoom-in duration-200">
                  <div className="w-16 h-16 rounded-full bg-blue-500/20 text-[#3E6AE1] flex items-center justify-center">
                    <Play size={32} fill="currentColor" className="ml-1" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white mb-1">พร้อมถ่ายรูปแล้ว</h2>
                    <p className="text-xs text-gray-300">
                      หมวด: <strong className="text-emerald-400 font-bold">{settings.className}</strong> | เป้าหมาย: {settings.targetCount} รูป (ทุก {settings.intervalSec}s)
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={onStartCapture}
                    className="w-full py-4 bg-gradient-to-r from-[#3E6AE1] to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-extrabold rounded-2xl shadow-xl shadow-blue-500/40 text-lg flex items-center justify-center gap-2.5 transition-all active:scale-95"
                  >
                    <Play size={22} fill="currentColor" />
                    <span>เริ่มถ่ายภาพ</span>
                  </button>
                  <button
                    type="button"
                    onClick={onCloseFullscreen}
                    className="text-xs text-gray-400 hover:text-white transition-colors"
                  >
                    ✕ ย้อนกลับไปตั้งค่า
                  </button>
                </div>
              </div>
            )}

            {/* FULLSCREEN MODE: Live Floating HUD during Capture */}
            {isFullscreen && isCapturing && (
              <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3 z-20 w-full max-w-md px-4">
                {/* Progress Pill */}
                <div className="bg-black/85 backdrop-blur-md px-6 py-2.5 rounded-full border border-white/20 shadow-2xl flex items-center gap-4">
                  <div className="text-sm font-bold text-white">
                    ถ่ายแล้ว: <span className="text-emerald-400 text-base">{capturedCount}</span> / {settings.targetCount}
                  </div>
                  <div className="w-24 h-2 bg-white/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-400 transition-all duration-150"
                      style={{ width: `${Math.min(100, (capturedCount / settings.targetCount) * 100)}%` }}
                    />
                  </div>
                </div>

                {/* Floating Controls */}
                <div className="flex items-center gap-3">
                  {isPaused ? (
                    <button
                      onClick={onResumeCapture}
                      className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-2xl shadow-lg flex items-center gap-2 text-sm active:scale-95"
                    >
                      <Play size={18} fill="currentColor" />
                      <span>ทำต่อ</span>
                    </button>
                  ) : (
                    <button
                      onClick={onPauseCapture}
                      className="px-6 py-3 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-2xl shadow-lg flex items-center gap-2 text-sm active:scale-95"
                    >
                      <Pause size={18} />
                      <span>หยุดชั่วคราว</span>
                    </button>
                  )}
                  <button
                    onClick={onStopCapture}
                    className="px-6 py-3 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-2xl shadow-lg flex items-center gap-2 text-sm active:scale-95"
                  >
                    <Square size={18} fill="currentColor" />
                    <span>เสร็จสิ้น</span>
                  </button>
                </div>
              </div>
            )}

            {/* Interval Progress Bar */}
            {isCapturing && (
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-black/40 overflow-hidden z-10">
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
