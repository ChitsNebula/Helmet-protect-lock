/**
 * Google Apps Script - บันทึกภาพ Dataset เข้า Google Drive อัตโนมัติ (ฉบับแก้ปัญหาโฟลเดอร์ซ้ำ 100%)
 * โฟลเดอร์เป้าหมาย: https://drive.google.com/drive/folders/1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW
 */
const FOLDER_ID = "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW";

function doPost(e) {
  // 1. ใช้ LockService ป้องกันคำขอวิ่งเข้ามาชนกันพร้อมกัน (Race Condition)
  const lock = LockService.getScriptLock();
  lock.waitLock(30000); // รอคิวได้สูงสุด 30 วินาที

  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ success: false, error: "No payload found" });
    }

    const data = JSON.parse(e.postData.contents);
    const mainFolder = DriveApp.getFolderById(FOLDER_ID);
    const className = data.className || "unclassified";

    // 2. ค้นหาโฟลเดอร์คลาสทั้งหมดที่มีชื่อเดียวกัน
    const subFolders = mainFolder.getFoldersByName(className);
    const existingFolders = [];
    while (subFolders.hasNext()) {
      existingFolders.push(subFolders.next());
    }

    let targetFolder = null;
    if (existingFolders.length > 0) {
      targetFolder = existingFolders[0];

      // หากมีโฟลเดอร์ชื่อซ้ำกัน ให้ย้ายไฟล์ทั้งหมดมารวมที่โฟลเดอร์แรก แล้วลบโฟลเดอร์ซ้ำทิ้งให้อัตโนมัติ
      for (let i = 1; i < existingFolders.length; i++) {
        const dupFolder = existingFolders[i];
        const files = dupFolder.getFiles();
        while (files.hasNext()) {
          files.next().moveTo(targetFolder);
        }
        dupFolder.setTrashed(true);
      }
    } else {
      targetFolder = mainFolder.createFolder(className);
    }

    // 3. ปลดล็อคคิวเพื่อให้คำขอถัดไปทำงานได้ทันที
    lock.releaseLock();

    // 4. บันทึกไฟล์ภาพลงในโฟลเดอร์เป้าหมาย
    const base64Data = data.image.split(",")[1] || data.image;
    const decodedBytes = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decodedBytes, "image/jpeg", data.filename || ("photo_" + Date.now() + ".jpg"));

    const file = targetFolder.createFile(blob);

    return jsonResponse({
      success: true,
      fileId: file.getId(),
      fileUrl: file.getUrl(),
      filename: data.filename
    });
  } catch (err) {
    try {
      lock.releaseLock();
    } catch (e) {
      // Ignore
    }
    return jsonResponse({
      success: false,
      error: err.toString()
    });
  }
}

function doGet() {
  return jsonResponse({
    status: "ok",
    folderId: FOLDER_ID,
    message: "Google Drive Upload Webhook is READY (Lock Enabled)!"
  });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
