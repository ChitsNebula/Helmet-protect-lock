export type DatasetClass = 'with-helmet' | 'without-helmet' | 'custom';

export interface CapturedImage {
  id: string;
  dataUrl: string;
  blob: Blob;
  filename: string;
  className: string;
  timestamp: number;
  status: 'pending' | 'uploading' | 'uploaded' | 'failed';
  error?: string;
  driveFileUrl?: string;
}

export interface CaptureSettings {
  className: string;
  autoMode: boolean;
  intervalSec: number;
  targetCount: number;
  mirror: boolean;
  resolution: '720p' | '1080p';
  facingMode: 'user' | 'environment';
  shutterSound: boolean;
  flashEffect: boolean;
  driveWebhookUrl: string;
  driveFolderId: string;
}
