import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "VisionInspect AI",
  description: "AI-powered manufacturing defect detection and quality inspection platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
