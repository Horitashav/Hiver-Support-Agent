import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hiver AI Support Agent",
  description: "AI-powered customer support triage and response system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}