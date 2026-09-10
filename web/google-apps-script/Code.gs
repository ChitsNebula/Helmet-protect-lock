/**
 * Google Apps Script - บันทึกภาพ Dataset เข้า Google Drive อัตโนมัติ
 * โฟลเดอร์ปลายทาง: https://drive.google.com/drive/folders/1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW
 *
 * วิธีใช้งาน (ทำครั้งเดียวใน 1 นาที):
 * 1. ไปที่ https://script.google.com/home
 * 2. กดปุ่ม "โครงการใหม่" (New project) ด้านซ้ายบน
 * 3. ลบโค้ดเดิมออกให้หมด แล้ววางโค้ดนี้ทั้งหมดลงไป
 * 4. กดปุ่ม "ทำให้ใช้งานได้" (Deploy) มุมขวาบน -> เลือก "การทำให้ใช้งานได้รายการใหม่" (New deployment)
 *    - เลือกประเภท: เว็บแอป (Web app)
 *    - คำอธิบาย: Helmet Dataset Webhook
 *    - ดำเนินการในฐานะ (Execute as): ฉัน (Me)
 *    - ผู้ที่มีสิทธิ์เข้าถึง (Who has access): ทุกคน (Anyone)
 * 5. กด "ทำให้ใช้งานได้" (Deploy) แล้วคัดลอก "URL เว็บแอป" (Web app URL)
 * 6. เอา URL นั้นมาวางในปุ่มตั้งค่า (ฟันเฟือง) บนหน้าเว็บ แล้วกดบันทึก จบเลย!
 */

const FOLDER_ID = "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW";

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ success: false, error: "No payload found" });
    }

    const data = JSON.parse(e.postData.contents);
    const folder = DriveApp.getFolderById(FOLDER_ID);

    // แยกโฟลเดอร์ตามคลาส (with-helmet / without-helmet)
    const className = data.className || "unclassified";
    let targetFolder = folder;
    const subFolders = folder.getFoldersByName(className);
    if (subFolders.hasNext()) {
      targetFolder = subFolders.next();
    } else {
      targetFolder = folder.createFolder(className);
    }

    // แปลง Base64 เป็นไฟล์ภาพ JPG
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
    message: "Helmet Dataset Google Drive Webhook is READY!"
  });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
