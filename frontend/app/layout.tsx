import React from "react";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "AI Policy & Transformation Advisor",
  description: "Evidence-backed policy analysis and implementation planning using RAG + CrewAI.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-ink-100 font-sans text-ink-900">{children}</body>
    </html>
  );
}
