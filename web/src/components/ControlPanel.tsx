"use client";

import React from "react";
import { Play, Pause, Square, Camera, ShieldCheck, ShieldAlert, Maximize2, Sliders } from "lucide-react";
import { CaptureSettings } from "@/lib/types";

interface ControlPanelProps {
  settings: CaptureSettings;
  onUpdateSettings: (patch: Partial<CaptureSettings>) => void;
  isCapturing: boolean;
  isPaused: boolean;
  onOpenFullscreen: () => void;
  onStartAuto: () => void;
  onPauseAuto: () => void;
  onResumeAuto: () => void;
  onStopAuto: () => void;
  onManualCapture: () => void;
  capturedCount: number;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  settings,
  onUpdateSettings,
  isCapturing,
  isPaused,
  onOpenFullscreen,
  onPauseAuto,
  onResumeAuto,
  onStopAuto,
  onManualCapture,
  capturedCount,
}) => {
  const isWithHelmet = settings.className === "with-helmet";
  const isWithoutHelmet = settings.className === "without-helmet";

  return (
    <div className="flex flex-col gap-5 bg-[#12151C] p-5 sm:p-6 rounded-2xl border border-white/10 shadow-xl">
      {/* 1. Class / Label Selector */}
      <div>
        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2.5 block">
          เลือกหมวดหมู่ภาพ (DATASET CLASS)
        </label>
        <div className="grid grid-cols-2 gap-2.5">
          <button
            type="button"
            onClick={() => onUpdateSettings({ className: "with-helmet" })}
            className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-semibold transition-all ${
              isWithHelmet
                ? "bg-emerald-500/20 border-emerald-500 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
            }`}
          >
            <ShieldCheck size={18} />
            <span>ใส่หมวก (with-helmet)</span>
          </button>

          <button
            type="button"
            onClick={() => onUpdateSettings({ className: "without-helmet" })}
            className={`flex items-center justify-center gap-2 py-3 px-4 rounded-xl border text-sm font-semibold transition-all ${
              isWithoutHelmet
                ? "bg-rose-500/20 border-rose-500 text-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.3)]"
                : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
            }`}
          >
            <ShieldAlert size={18} />
            <span>ไม่ใส่หมวก (without-helmet)</span>
          </button>
        </div>
      </div>

      {/* 2. Mode Settings (Auto vs Manual) */}
      <div className="p-4 bg-white/5 rounded-xl border border-white/5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-200 flex items-center gap-2">
            <Sliders size={16} className="text-[#3E6AE1]" />
            โหมดการถ่ายภาพ (Capture Mode)
          </span>
          <div className="flex bg-black/40 p-1 rounded-lg border border-white/10">
            <button
              onClick={() => onUpdateSettings({ autoMode: true })}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                settings.autoMode ? "bg-[#3E6AE1] text-white shadow" : "text-gray-400 hover:text-white"
              }`}
            >
              อัตโนมัติ (Auto)
            </button>
            <button
              onClick={() => onUpdateSettings({ autoMode: false })}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                !settings.autoMode ? "bg-[#3E6AE1] text-white shadow" : "text-gray-400 hover:text-white"
              }`}
            >
              กดเอง (Manual)
            </button>
          </div>
        </div>

        {/* Auto Parameters */}
        {settings.autoMode && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-white/5">
            {/* Interval Selector */}
            <div>
              <label className="text-[11px] text-gray-400 font-medium block mb-1.5">
                ความถี่ (ทุกๆ วินาที):
              </label>
              <div className="grid grid-cols-4 gap-1">
                {[1.0, 1.5, 2.0, 3.0].map((sec) => (
                  <button
                    key={sec}
                    type="button"
                    onClick={() => onUpdateSettings({ intervalSec: sec })}
                    className={`py-1.5 text-xs font-semibold rounded border transition-all ${
                      settings.intervalSec === sec
                        ? "bg-[#3E6AE1] border-[#3E6AE1] text-white shadow"
                        : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                    }`}
                  >
                    {sec}s
                  </button>
                ))}
              </div>
            </div>

            {/* Target Count with direct number input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] text-gray-400 font-medium">
                  เป้าหมาย (จำนวนรูป):
                </label>
                <span className="text-[10px] text-blue-400 font-mono">พิมพ์เลขได้อิสระ</span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={settings.targetCount}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10);
                    onUpdateSettings({ targetCount: isNaN(val) ? 1 : Math.max(1, Math.min(2000, val)) });
                  }}
                  className="w-20 px-2.5 py-1.5 bg-black/50 border border-white/20 rounded-lg text-white font-bold text-center text-sm focus:border-blue-500 focus:outline-none"
                />
                <div className="flex-1 grid grid-cols-4 gap-1">
                  {[20, 50, 100, 200].map((cnt) => (
                    <button
                      key={cnt}
                      type="button"
                      onClick={() => onUpdateSettings({ targetCount: cnt })}
                      className={`py-1.5 text-xs font-semibold rounded border transition-all ${
                        settings.targetCount === cnt
                          ? "bg-[#3E6AE1] border-[#3E6AE1] text-white shadow"
                          : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10"
                      }`}
                    >
                      {cnt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Primary Action Buttons */}
      <div className="flex flex-col gap-3">
        {settings.autoMode ? (
          !isCapturing ? (
            /* Button to Open Fullscreen Ready Mode */
            <button
              type="button"
              onClick={onOpenFullscreen}
              className="w-full py-4 bg-gradient-to-r from-[#3E6AE1] via-blue-600 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2.5 text-base transition-all active:scale-[0.99]"
            >
              <Maximize2 size={20} />
              <span>📷 เตรียมถ่ายรูป (เต็มจอ)</span>
            </button>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {isPaused ? (
                <button
                  type="button"
                  onClick={onResumeAuto}
                  className="py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl flex items-center justify-center gap-2 text-sm transition-all"
                >
                  <Play size={18} fill="currentColor" />
                  <span>ทำต่อ (Resume)</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={onPauseAuto}
                  className="py-3.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-xl flex items-center justify-center gap-2 text-sm transition-all"
                >
                  <Pause size={18} />
                  <span>หยุดชั่วคราว (Pause)</span>
                </button>
              )}
              <button
                type="button"
                onClick={onStopAuto}
                className="py-3.5 bg-rose-600/80 hover:bg-rose-600 text-white font-bold rounded-xl flex items-center justify-center gap-2 text-sm transition-all"
              >
                <Square size={18} fill="currentColor" />
                <span>เสร็จสิ้น (Stop)</span>
              </button>
            </div>
          )
        ) : (
          <button
            type="button"
            onClick={onManualCapture}
            className="w-full py-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2.5 text-base transition-all active:scale-[0.99]"
          >
            <Camera size={22} />
            <span>กดถ่ายภาพช็อตนี้ (Spacebar)</span>
          </button>
        )}

        <div className="flex items-center justify-between px-2 pt-1 text-xs text-gray-400">
          <span className="text-gray-400">
            หมวดหมู่: <strong className={isWithHelmet ? "text-emerald-400" : "text-rose-400"}>{settings.className}</strong>
          </span>
          <span className="font-mono text-gray-400">
            ถ่ายแล้ว: <strong className="text-white font-bold">{capturedCount}</strong> ภาพ
          </span>
        </div>
      </div>
    </div>
  );
};
