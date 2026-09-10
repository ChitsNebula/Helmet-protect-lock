"use client";

import React, { useState } from "react";
import { X, Check, Copy, ExternalLink, HardDrive, Key, HelpCircle, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { CaptureSettings } from "@/lib/types";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: CaptureSettings;
  onUpdateSettings: (patch: Partial<CaptureSettings>) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
}) => {
  const [webhookUrl, setWebhookUrl] = useState(settings.driveWebhookUrl);
  const [folderId, setFolderId] = useState(settings.driveFolderId);
  const [isCopied, setIsCopied] = useState(false);
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "failed">("idle");
  const [testMessage, setTestMessage] = useState("");

  if (!isOpen) return null;

  const gasCode = `const DEFAULT_FOLDER_ID = "${folderId || "YOUR_GOOGLE_DRIVE_FOLDER_ID"}";

function doPost(e) {
  try {
    let data;
    if (e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    } else {
      return responseJSON({ success: false, error: "No payload found" });
    }

    const folderId = data.folderId || DEFAULT_FOLDER_ID;
    const folder = DriveApp.getFolderById(folderId);

    const className = data.className || "unclassified";
    let targetFolder = folder;
    const subFolders = folder.getFoldersByName(className);
    if (subFolders.hasNext()) {
      targetFolder = subFolders.next();
    } else {
      targetFolder = folder.createFolder(className);
    }

    const base64Data = data.image.replace(/^data:image\/(png|jpeg|jpg);base64,/, "");
    const decodedBlob = Utilities.newBlob(Utilities.base64Decode(base64Data), "image/jpeg", data.filename);

    const file = targetFolder.createFile(decodedBlob);
    file.setDescription("Uploaded via Helmet Dataset Web App | Class: " + className);

    return responseJSON({
      success: true,
      fileId: file.getId(),
      fileUrl: file.getUrl(),
      filename: data.filename
    });
  } catch (err) {
    return responseJSON({
      success: false,
      error: err.toString()
    });
  }
}

function doGet() {
  return responseJSON({ status: "ok", message: "Helmet Dataset Google Drive API is active!" });
}

function responseJSON(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(gasCode);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleSave = () => {
    onUpdateSettings({
      driveWebhookUrl: webhookUrl.trim(),
      driveFolderId: folderId.trim(),
    });
    localStorage.setItem("helmet_drive_webhook", webhookUrl.trim());
    localStorage.setItem("helmet_drive_folder", folderId.trim());
    onClose();
  };

  const handleTestConnection = async () => {
    if (!webhookUrl) {
      setTestStatus("failed");
      setTestMessage("กรุณากรอก Google Apps Script Webhook URL ก่อนทดสอบ");
      return;
    }
    setTestStatus("testing");
    try {
      const res = await fetch(webhookUrl);
      const data = await res.json();
      if (data && data.status === "ok") {
        setTestStatus("success");
        setTestMessage("เชื่อมต่อกับ Google Apps Script สำเร็จ พร้อมบันทึกภาพลง Drive!");
      } else {
        setTestStatus("failed");
        setTestMessage("ตอบกลับไม่ถูกต้อง: " + JSON.stringify(data));
      }
    } catch (err: unknown) {
      setTestStatus("failed");
      setTestMessage("ไม่สามารถเชื่อมต่อได้: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#151922] w-full max-w-xl rounded-2xl border border-white/10 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#3E6AE1]/20 rounded-lg text-[#3E6AE1]">
              <HardDrive size={20} />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">ตั้งค่าการเชื่อมต่อ Google Drive</h2>
              <p className="text-xs text-gray-400">บันทึกภาพที่ถ่ายเข้าโฟลเดอร์ Google Drive อัตโนมัติ</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white p-1 rounded-lg">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-5 text-sm">
          {/* Inputs */}
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-gray-300 block mb-1">
                Google Apps Script Web App URL:
              </label>
              <input
                type="text"
                placeholder="https://script.google.com/macros/s/.../exec"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white text-xs font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-300 block mb-1">
                Google Drive Folder ID (โฟลเดอร์ปลายทาง):
              </label>
              <input
                type="text"
                placeholder="1a2b3c4d5e... (ดูจาก URL โฟลเดอร์ใน Google Drive)"
                value={folderId}
                onChange={(e) => setFolderId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-black/40 border border-white/10 rounded-xl text-white text-xs font-mono focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Test Connection Button */}
            <div className="pt-1 flex items-center justify-between">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testStatus === "testing"}
                className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-gray-300 rounded-lg flex items-center gap-1.5"
              >
                {testStatus === "testing" ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                <span>ทดสอบการเชื่อมต่อ</span>
              </button>

              {testStatus === "success" && (
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 size={14} /> สำเร็จ
                </span>
              )}
              {testStatus === "failed" && (
                <span className="text-xs text-rose-400 flex items-center gap-1 max-w-[280px] truncate" title={testMessage}>
                  <AlertCircle size={14} /> {testMessage}
                </span>
              )}
            </div>
          </div>

          {/* 3-Step Guide */}
          <div className="p-4 bg-white/5 rounded-xl border border-white/5 space-y-3">
            <h4 className="text-xs font-bold text-white flex items-center gap-1.5 uppercase tracking-wider">
              <HelpCircle size={15} className="text-emerald-400" />
              วิธีสร้าง Webhook บันทึกรูปใน Google Drive (ทำครั้งเดียวใน 2 นาที):
            </h4>
            <ol className="text-xs text-gray-300 space-y-1.5 list-decimal list-inside leading-relaxed">
              <li>สร้างโฟลเดอร์ใหม่ใน Google Drive (เช่น <code>Helmet_Dataset</code>) แล้วเปิดดู URL เพื่อก๊อปปี้ Folder ID ท้ายลิงก์</li>
              <li>
                เปิด <a href="https://script.google.com/home" target="_blank" rel="noreferrer" className="text-blue-400 underline inline-flex items-center gap-0.5">Google Apps Script <ExternalLink size={10} /></a> แล้วกด <strong>โครงการใหม่ (New project)</strong>
              </li>
              <li>ก๊อปปี้โค้ดด้านล่างนี้ไปวางแทนที่ทั้งหมดในไฟล์ <code>Code.gs</code></li>
              <li>
                กด <strong>ทำให้ใช้งานได้ (Deploy)</strong> &gt; <strong>การทำให้ใช้งานได้รายการใหม่ (New deployment)</strong> &gt; เลือกประเภท <strong>เว็บแอป (Web app)</strong>
                <ul className="list-disc list-inside pl-4 text-gray-400 pt-1">
                  <li>การเข้าถึง (Who has access): <strong>ทุกคน (Anyone)</strong></li>
                </ul>
              </li>
              <li>ก๊อปปี้ <strong>URL เว็บแอป (Web app URL)</strong> มาวางในช่องด้านบนนี้แล้วกดบันทึก จบเลย!</li>
            </ol>

            {/* Code Box */}
            <div className="relative mt-2">
              <pre className="p-3 bg-black/60 rounded-lg text-[10px] font-mono text-gray-300 max-h-36 overflow-y-auto border border-white/10">
                {gasCode}
              </pre>
              <button
                type="button"
                onClick={handleCopyCode}
                className="absolute top-2 right-2 px-2.5 py-1 bg-white/10 hover:bg-white/20 text-white rounded text-[11px] flex items-center gap-1 font-sans backdrop-blur-sm"
              >
                {isCopied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                <span>{isCopied ? "คัดลอกแล้ว!" : "คัดลอกโค้ด"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-white/10 flex items-center justify-end gap-2 bg-black/20">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white rounded-lg transition-colors"
          >
            ยกเลิก
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 bg-[#3E6AE1] hover:bg-blue-600 text-white text-xs font-bold rounded-lg shadow-md shadow-blue-500/20 transition-all"
          >
            บันทึกการตั้งค่า
          </button>
        </div>
      </div>
    </div>
  );
};
