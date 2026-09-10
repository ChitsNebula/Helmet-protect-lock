"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import confetti from "canvas-confetti";
import { HelpCircle, CheckCircle2, Shield } from "lucide-react";
import { CameraView, CameraViewRef } from "@/components/CameraView";
import { ControlPanel } from "@/components/ControlPanel";
import { GalleryDrawer } from "@/components/GalleryDrawer";
import { playShutterSound } from "@/lib/audio";
import { CapturedImage, CaptureSettings } from "@/lib/types";

export default function Home() {
  const cameraRef = useRef<CameraViewRef>(null);

  // App Settings (Preset default folder ID from user)
  const [settings, setSettings] = useState<CaptureSettings>({
    className: "with-helmet",
    autoMode: true,
    intervalSec: 1.5,
    targetCount: 50,
    mirror: true,
    resolution: "1080p",
    facingMode: "user",
    shutterSound: true,
    flashEffect: true,
    driveWebhookUrl: "https://script.google.com/macros/s/AKfycbx2MpINdkQl0o7UBpy-EgEqE_x6G7cvF7hCFTh3u8VpOpa_7wMDBKedjNjBQtiXgpAKHg/exec",
    driveFolderId: "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW",
  });

  // State
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [images, setImages] = useState<CapturedImage[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [countdownProgress, setCountdownProgress] = useState(0);
  const [flashTrigger, setFlashTrigger] = useState(0);

  // Load settings from localStorage
  useEffect(() => {
    try {
      const savedWebhook = localStorage.getItem("helmet_drive_webhook");
      const savedFolder = localStorage.getItem("helmet_drive_folder");
      if (savedWebhook || savedFolder) {
        setSettings((prev) => ({
          ...prev,
          driveWebhookUrl: savedWebhook || prev.driveWebhookUrl,
          driveFolderId: savedFolder || prev.driveFolderId,
        }));
      }
    } catch {
      // Ignore
    }
  }, []);

  const updateSettings = (patch: Partial<CaptureSettings>) => {
    setSettings((prev) => ({ ...prev, ...patch }));
  };

  // Upload Queue Worker
  const uploadImage = useCallback(
    async (img: CapturedImage) => {
      if (!settings.driveWebhookUrl) {
        return;
      }

      setImages((prev) =>
        prev.map((item) => (item.id === img.id ? { ...item, status: "uploading" } : item))
      );

      try {
        const res = await fetch("/api/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image: img.dataUrl,
            filename: img.filename,
            className: img.className,
            webhookUrl: settings.driveWebhookUrl,
            folderId: settings.driveFolderId || "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW",
          }),
        });

        const data = await res.json();
        if (data.success) {
          setImages((prev) =>
            prev.map((item) =>
              item.id === img.id ? { ...item, status: "uploaded", driveFileUrl: data.fileUrl } : item
            )
          );
        } else {
          setImages((prev) =>
            prev.map((item) =>
              item.id === img.id ? { ...item, status: "failed", error: data.error } : item
            )
          );
        }
      } catch (err: unknown) {
        setImages((prev) =>
          prev.map((item) =>
            item.id === img.id
              ? { ...item, status: "failed", error: err instanceof Error ? err.message : "Upload error" }
              : item
          )
        );
      }
    },
    [settings.driveWebhookUrl, settings.driveFolderId]
  );

  // Capture Single Frame
  const captureFrame = useCallback(() => {
    if (!cameraRef.current) return;
    const result = cameraRef.current.capture(settings.className);
    if (!result) return;

    if (settings.shutterSound) {
      playShutterSound();
    }
    setFlashTrigger((prev) => prev + 1);

    const timestamp = Date.now();
    const d = new Date(timestamp);
    const dateStr = d.toISOString().replace(/[-:T.]/g, "").slice(0, 14);
    const randStr = Math.random().toString(36).substring(2, 6);
    const filename = `${settings.className}_${dateStr}_${randStr}.jpg`;

    result.blob.then((blob) => {
      if (!blob) return;
      const newImage: CapturedImage = {
        id: "img_" + timestamp + "_" + randStr,
        dataUrl: result.dataUrl,
        blob,
        filename,
        className: settings.className,
        timestamp,
        status: settings.driveWebhookUrl ? "pending" : "uploaded",
      };

      setImages((prev) => [newImage, ...prev]);

      if (settings.driveWebhookUrl) {
        uploadImage(newImage);
      }
    });
  }, [settings.className, settings.shutterSound, settings.driveWebhookUrl, uploadImage]);

  // Auto-Capture Timer Loop
  useEffect(() => {
    if (!isCapturing || isPaused) {
      setCountdownProgress(0);
      return;
    }

    const intervalMs = settings.intervalSec * 1000;
    const updateFreqMs = 50;
    let elapsed = 0;

    const timer = setInterval(() => {
      elapsed += updateFreqMs;
      const pct = Math.min(100, (elapsed / intervalMs) * 100);
      setCountdownProgress(pct);

      if (elapsed >= intervalMs) {
        elapsed = 0;
        setCountdownProgress(0);
        captureFrame();

        setImages((currentImages) => {
          if (currentImages.length + 1 >= settings.targetCount) {
            setIsCapturing(false);
            setIsFullscreen(false); // return to normal view
            try {
              confetti({ particleCount: 150, spread: 90, origin: { y: 0.6 } });
            } catch {
              // Ignore
            }
          }
          return currentImages;
        });
      }
    }, updateFreqMs);

    return () => clearInterval(timer);
  }, [isCapturing, isPaused, settings.intervalSec, settings.targetCount, captureFrame]);

  // Keyboard Shortcuts (Spacebar)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.code === "Space") {
        e.preventDefault();
        if (settings.autoMode) {
          if (!isCapturing) {
            setIsFullscreen(true);
            setIsCapturing(true);
            setIsPaused(false);
          } else {
            setIsPaused((prev) => !prev);
          }
        } else {
          captureFrame();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [settings.autoMode, isCapturing, captureFrame]);

  const handleRetryUpload = (id: string) => {
    const target = images.find((img) => img.id === id);
    if (target) {
      uploadImage(target);
    }
  };

  const isDriveConfigured = !!settings.driveWebhookUrl;

  return (
    <div className="min-h-screen bg-[#0A0D14] text-white flex flex-col selection:bg-blue-500 selection:text-white">
      {/* 1. Header */}
      <header className="sticky top-0 z-40 bg-[#0F131C]/90 backdrop-blur-md border-b border-white/10 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#3E6AE1] to-blue-400 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Shield size={20} />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold tracking-tight text-white flex items-center gap-2">
              <span>HELMET DATASET COLLECTOR</span>
              <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono border border-blue-500/30">
                v1.1
              </span>
            </h1>
            <p className="text-[11px] text-gray-400">ระบบถ่ายภาพสร้าง Dataset อัตโนมัติ & ส่งเข้า Google Drive</p>
          </div>
        </div>

        {/* Clean Status Badge (No technical settings visible to users) */}
        <div className="flex items-center gap-2">
          <div className="px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-1.5 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>ระบบพร้อมบันทึกภาพ</span>
          </div>
        </div>
      </header>

      {/* 2. Main Content Grid */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Camera Feed Viewport (7 Cols) */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <CameraView
              ref={cameraRef}
              settings={settings}
              onUpdateSettings={updateSettings}
              isCapturing={isCapturing}
              isPaused={isPaused}
              isFullscreen={isFullscreen}
              onCloseFullscreen={() => {
                setIsFullscreen(false);
                setIsCapturing(false);
                setIsPaused(false);
              }}
              onStartCapture={() => {
                setIsCapturing(true);
                setIsPaused(false);
              }}
              onPauseCapture={() => setIsPaused(true)}
              onResumeCapture={() => setIsPaused(false)}
              onStopCapture={() => {
                setIsCapturing(false);
                setIsFullscreen(false);
                setIsPaused(false);
              }}
              capturedCount={images.length}
              countdownProgress={countdownProgress}
              flashTrigger={flashTrigger}
            />

            <div className="flex items-center justify-between px-3 py-2 bg-white/5 rounded-xl border border-white/5 text-xs text-gray-400">
              <span className="flex items-center gap-1.5">
                <HelpCircle size={14} className="text-[#3E6AE1]" />
                จัดตำแหน่งให้อยู่กึ่งกลางภาพ เพื่อให้ได้ Dataset ที่มีคุณภาพสูง
              </span>
              <span className="hidden sm:inline font-mono text-[11px] text-gray-500">
                กด Spacebar เพื่อถ่าย
              </span>
            </div>
          </div>

          {/* Right: Control Center (5 Cols) */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <ControlPanel
              settings={settings}
              onUpdateSettings={updateSettings}
              isCapturing={isCapturing}
              isPaused={isPaused}
              onOpenFullscreen={() => setIsFullscreen(true)}
              onStartAuto={() => {
                setIsFullscreen(true);
                setIsCapturing(true);
                setIsPaused(false);
              }}
              onPauseAuto={() => setIsPaused(true)}
              onResumeAuto={() => setIsPaused(false)}
              onStopAuto={() => {
                setIsCapturing(false);
                setIsFullscreen(false);
                setIsPaused(false);
              }}
              onManualCapture={captureFrame}
              capturedCount={images.length}
            />
          </div>
        </div>

        {/* Bottom Section: Gallery & Upload Monitor */}
        <GalleryDrawer
          images={images}
          onClearImages={() => setImages([])}
          onRetryUpload={handleRetryUpload}
        />
      </main>

      {/* 3. Footer */}
      <footer className="border-t border-white/5 py-4 px-6 text-center text-xs text-gray-500 bg-[#0B0D13]">
        <p>Helmet Protect Lock - Web Dataset Collector &copy; 2026 | พร้อมใช้งานบน Vercel & Google Drive</p>
      </footer>


    </div>
  );
}
