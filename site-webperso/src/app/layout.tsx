import type { Metadata } from "next";
import { Inter, Spectral, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { clsx } from "clsx";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const spectral = Spectral({
  weight: ["300", "400", "500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-spectral"
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono"
});

export const metadata: Metadata = {
  title: "Olivier Cloutier | Research & Governance",
  description: "Philosophy of AI, Ethics, Governance, and Data Methods.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={clsx(
        inter.variable,
        spectral.variable,
        jetbrainsMono.variable,
        "bg-paper text-ink font-sans antialiased selection:bg-forest selection:text-paper"
      )}>
        {/* Global Noise Overlay */}
        <div className="fixed inset-0 pointer-events-none z-50 opacity-[0.03] mix-blend-multiply bg-[url('https://grainy-gradients.vercel.app/noise.svg')]"></div>

        {children}
      </body>
    </html>
  );
}
