import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { image, filename, className, webhookUrl, folderId } = body;

    if (!image || !filename) {
      return NextResponse.json({ success: false, error: 'Missing image or filename' }, { status: 400 });
    }

    // กำหนด URL ของ Google Apps Script Webhook
    const targetWebhook = webhookUrl || process.env.GOOGLE_DRIVE_WEBHOOK_URL || "https://script.google.com/macros/s/AKfycbx2MpINdkQl0o7UBpy-EgEqE_x6G7cvF7hCFTh3u8VpOpa_7wMDBKedjNjBQtiXgpAKHg/exec";
    const targetFolder = folderId || process.env.GOOGLE_DRIVE_FOLDER_ID || "1Epai3etZT3mqQLOQxkJAKhIoAg7uOFYW";

    if (!targetWebhook) {
      return NextResponse.json({
        success: false,
        error: 'Google Drive Webhook URL not configured. Please add it in Settings.'
      }, { status: 400 });
    }

    // ยิงต่อไปยัง Google Apps Script
    const response = await fetch(targetWebhook, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({
        image,
        filename,
        className: className || 'unclassified',
        folderId: targetFolder
      })
    });

    const result = await response.json();
    return NextResponse.json(result);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Upload proxy error';
    return NextResponse.json({ success: false, error: message }, { status: 500 });
  }
}
