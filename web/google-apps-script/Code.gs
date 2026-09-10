/**
 * Google Apps Script - บันทึกภาพ Dataset เข้า Google Drive
 * แยกโฟลเดอร์ตาม "วันที่ (YYYY-MM-DD)" -> ตามด้วย "คลาส (with-helmet / without-helmet)"
 * โฟลเดอร์เป้าหมาย: https://drive.google.com/drive/folders/1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW
 */
const FOLDER_ID = "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW";

function doPost(e) {
  // 1. ล็อคคิวป้องกัน Race condition เมื่อรูปถูกอัปโหลดรัวๆ
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);

  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ success: false, error: "No payload found" });
    }

    const data = JSON.parse(e.postData.contents);
    const mainFolder = DriveApp.getFolderById(FOLDER_ID);

    // 2. หาวันที่ปัจจุบัน (เวลาไทย GMT+7) เช่น 2026-09-10
    const dateStr = Utilities.formatDate(new Date(), "Asia/Bangkok", "yyyy-MM-dd");
    const className = data.className || "unclassified";

    // 3. เข้าถึงหรือสร้างโฟลเดอร์ "วันที่" -> โฟลเดอร์ "คลาส" (พร้อมกันโฟลเดอร์ซ้ำ)
    const dateFolder = getOrCreateFolder(mainFolder, dateStr);
    const classFolder = getOrCreateFolder(dateFolder, className);

    // 4. ปลดล็อคคิว
    lock.releaseLock();

    // 5. บันทึกไฟล์ภาพ
    const base64Data = data.image.split(",")[1] || data.image;
    const decodedBytes = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decodedBytes, "image/jpeg", data.filename || ("photo_" + Date.now() + ".jpg"));

    const file = classFolder.createFile(blob);

    return jsonResponse({
      success: true,
      fileId: file.getId(),
      fileUrl: file.getUrl(),
      filename: data.filename,
      dateFolder: dateStr,
      className: className
    });
  } catch (err) {
    try {
      lock.releaseLock();
    } catch (e) {}
    return jsonResponse({
      success: false,
      error: err.toString()
    });
  }
}

/**
 * ฟังก์ชันค้นหาโฟลเดอร์ หากยังไม่มีให้สร้าง และหากมีชื่อซ้ำกันให้ยุบรวมอัตโนมัติ
 */
function getOrCreateFolder(parentFolder, folderName) {
  const folders = parentFolder.getFoldersByName(folderName);
  const list = [];
  while (folders.hasNext()) {
    list.push(folders.next());
  }

  if (list.length > 0) {
    const target = list[0];
    // ถ้ารอบก่อนหน้ามีโฟลเดอร์ชื่อซ้ำ ให้ย้ายทุกอย่างมารวมที่โฟลเดอร์แรก แล้วลบโฟลเดอร์ซ้ำทิ้ง
    for (let i = 1; i < list.length; i++) {
      const dup = list[i];
      const files = dup.getFiles();
      while (files.hasNext()) files.next().moveTo(target);
      const subFolders = dup.getFolders();
      while (subFolders.hasNext()) subFolders.next().moveTo(target);
      dup.setTrashed(true);
    }
    return target;
  }

  return parentFolder.createFolder(folderName);
}

function doGet() {
  return jsonResponse({
    status: "ok",
    folderId: FOLDER_ID,
    message: "Google Drive Upload Webhook is READY (Date-Based Folder Separation)!"
  });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
