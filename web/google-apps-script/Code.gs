/**
 * Google Apps Script สำหรับรับภาพจาก Web Dataset Collector แล้วบันทึกลง Google Drive
 * วิธีใช้งาน:
 * 1. ไปที่ https://script.google.com/home
 * 2. กด "New project" (โครงการใหม่)
 * 3. วางโค้ดนี้ทั้งหมดลงใน Code.gs
 * 4. แทนที่ FOLDER_ID ด้วย ID ของโฟลเดอร์ Google Drive ของคุณ (ดูจาก URL โฟลเดอร์)
 * 5. กด Deploy -> New deployment -> เลือกประเภท "Web app"
 *    - Description: Dataset Collector
 *    - Execute as: Me
 *    - Who has access: Anyone (ทุกคน)
 * 6. กด Deploy แล้วคัดลอก "Web app URL" ไปใส่ในหน้าต่าง Settings ของเว็บ!
 */

const DEFAULT_FOLDER_ID = "PUT_YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE";

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

    // แยกโฟลเดอร์ย่อยตามชื่อคลาส เช่น with-helmet / without-helmet
    const className = data.className || "unclassified";
    let targetFolder = folder;
    const subFolders = folder.getFoldersByName(className);
    if (subFolders.hasNext()) {
      targetFolder = subFolders.next();
    } else {
      targetFolder = folder.createFolder(className);
    }

    // แปลง Base64 เป็นไฟล์รูปภาพ
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
}
