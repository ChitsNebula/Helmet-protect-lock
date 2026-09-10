import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  themeColor: "#0A0D14",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "Helmet Dataset Collector - Web Camera & Google Drive",
  description: "ถ่ายรูปสร้าง Dataset หมวกกันน็อกอัตโนมัติผ่านเว็บเบราว์เซอร์ พร้อมส่งขึ้น Google Drive",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th" className="dark">
      <body className={`${inter.className} bg-[#0A0D14] text-white antialiased`}>{children}</body>
    </html>
  );
}
