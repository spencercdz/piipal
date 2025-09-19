import type { Metadata } from "next";
import { TikTok_Sans } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const tiktokSans = TikTok_Sans({
  variable: "--font-tiktok-sans",
  subsets: ["latin"],
});

const tiktokMono = TikTok_Sans({
  variable: "--font-tiktok-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PIIPal - AI Content Privacy",
  description: "Safeguard your content with AI-powered PII detection.",
  keywords: "PII detection, content safety, Reels, privacy, blur, censor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${tiktokSans.variable} ${tiktokMono.variable} antialiased bg-black text-white`}
      >
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}