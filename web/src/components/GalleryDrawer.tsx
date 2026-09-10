"use client";

import React, { useState } from "react";
import { Download, Trash2, CheckCircle2, Loader2, AlertCircle, ExternalLink, Image as ImageIcon } from "lucide-react";
import JSZip from "jszip";
import { CapturedImage } from "@/lib/types";

interface GalleryDrawerProps {
  images: CapturedImage[];
  onClearImages: () => void;
  onRetryUpload: (id: string) => void;
}

export const GalleryDrawer: React.FC<GalleryDrawerProps> = ({ images, onClearImages, onRetryUpload }) => {
  const [isZipping, setIsZipping] = useState(false);
  const [selectedPreview, setSelectedPreview] = useState<CapturedImage | null>(null);

  const uploadedCount = images.filter((img) => img.status === "uploaded").length;
  const uploadingCount = images.filter((img) => img.status === "uploading").length;
  const failedCount = images.filter((img) => img.status === "failed").length;

  // Download All as ZIP
  const handleDownloadZip = async () => {
    if (images.length === 0) return;
    setIsZipping(true);
    try {
      const zip = new JSZip();
      const folderWith = zip.folder("with-helmet");
      const folderWithout = zip.folder("without-helmet");
      const folderCustom = zip.folder("custom");

      for (const img of images) {
        // Fetch blob from dataUrl
        const res = await fetch(img.dataUrl);
        const blob = await res.blob();

        if (img.className === "with-helmet") {
          folderWith?.file(img.filename, blob);
        } else if (img.className === "without-helmet") {
          folderWithout?.file(img.filename, blob);
        } else {
          folderCustom?.file(img.filename, blob);
        }
      }

      const content = await zip.generateAsync({ type: "blob" });
      const url = URL.createObjectURL(content);
      const a = document.createElement("a");
      a.href = url;
      a.download = `helmet_dataset_${new Date().toISOString().slice(0, 10)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("เกิดข้อผิดพลาดในการสร้างไฟล์ ZIP: " + err);
    } finally {
      setIsZipping(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 bg-[#12151C] p-5 rounded-2xl border border-white/10 shadow-xl">
      {/* Header with Stats & Actions */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-white/10">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ImageIcon size={18} className="text-[#3E6AE1]" />
            รูปภาพในเซสชันนี้ ({images.length})
          </h3>
          <div className="flex items-center gap-3 text-xs mt-1 text-gray-400">
            <span className="text-emerald-400 font-medium">✓ อัปโหลดสำเร็จ: {uploadedCount}</span>
            {uploadingCount > 0 && <span className="text-blue-400 animate-pulse">⏳ กำลังส่ง: {uploadingCount}</span>}
            {failedCount > 0 && <span className="text-rose-400">✕ ล้มเหลว: {failedCount}</span>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {images.length > 0 && (
            <>
              <button
                type="button"
                disabled={isZipping}
                onClick={handleDownloadZip}
                className="px-3 py-1.5 bg-[#3E6AE1]/20 hover:bg-[#3E6AE1]/30 border border-[#3E6AE1]/40 text-[#3E6AE1] text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all"
              >
                {isZipping ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                <span>ดาวน์โหลด ZIP</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  if (confirm("คุณต้องการลบภาพทั้งหมดในเซสชันนี้ใช่หรือไม่?")) {
                    onClearImages();
                  }
                }}
                className="p-1.5 bg-white/5 hover:bg-rose-500/20 text-gray-400 hover:text-rose-400 rounded-lg transition-all"
                title="ล้างทั้งหมด"
              >
                <Trash2 size={16} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Thumbnails Grid */}
      {images.length === 0 ? (
        <div className="py-12 text-center text-gray-500 text-xs">
          ยังไม่มีรูปภาพที่ถ่ายในเซสชันนี้ <br />
          เลือกหมวดหมู่แล้วกดปุ่ม "เริ่มถ่าย" หรือ "กดถ่ายภาพ" ด้านบนได้เลย
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2.5 max-h-72 overflow-y-auto pr-1">
          {images.map((img) => (
            <div
              key={img.id}
              onClick={() => setSelectedPreview(img)}
              className="group relative aspect-square rounded-lg overflow-hidden border border-white/10 bg-black/40 cursor-pointer hover:border-blue-500/60 transition-all"
            >
              <img src={img.dataUrl} alt={img.filename} className="w-full h-full object-cover" />

              {/* Status Badge */}
              <div className="absolute bottom-1 right-1">
                {img.status === "uploaded" && (
                  <div className="bg-emerald-500 text-white p-0.5 rounded-full shadow" title="บันทึกลง Drive แล้ว">
                    <CheckCircle2 size={13} />
                  </div>
                )}
                {img.status === "uploading" && (
                  <div className="bg-blue-500 text-white p-0.5 rounded-full shadow animate-spin" title="กำลังอัปโหลด...">
                    <Loader2 size={13} />
                  </div>
                )}
                {img.status === "failed" && (
                  <div
                    onClick={(e) => {
                      e.stopPropagation();
                      onRetryUpload(img.id);
                    }}
                    className="bg-rose-500 text-white p-0.5 rounded-full shadow hover:scale-110"
                    title="ล้มเหลว - กดเพื่อลองใหม่"
                  >
                    <AlertCircle size={13} />
                  </div>
                )}
              </div>

              {/* Class Label Badge */}
              <div className="absolute top-1 left-1">
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full text-white ${
                    img.className === "with-helmet" ? "bg-emerald-600/90" : "bg-rose-600/90"
                  }`}
                >
                  {img.className === "with-helmet" ? "H" : "No-H"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {selectedPreview && (
        <div
          onClick={() => setSelectedPreview(null)}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-[#181C24] p-4 rounded-2xl max-w-lg w-full border border-white/10 shadow-2xl flex flex-col gap-3"
          >
            <div className="flex items-center justify-between text-xs text-gray-300">
              <span className="font-mono">{selectedPreview.filename}</span>
              <button
                onClick={() => setSelectedPreview(null)}
                className="text-gray-400 hover:text-white px-2 py-1 rounded"
              >
                ✕ ปิด
              </button>
            </div>
            <img
              src={selectedPreview.dataUrl}
              alt={selectedPreview.filename}
              className="w-full rounded-xl object-contain max-h-96 bg-black"
            />
            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-gray-400">
                สถานะ: <strong className="text-white">{selectedPreview.status}</strong>
              </span>
              {selectedPreview.driveFileUrl && (
                <a
                  href={selectedPreview.driveFileUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 hover:underline flex items-center gap-1"
                >
                  <span>เปิดดูใน Google Drive</span>
                  <ExternalLink size={12} />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
