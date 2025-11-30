import type React from "react"
import type { Metadata, Viewport } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

// <CHANGE> Updated metadata for cybersecurity dashboard
export const metadata: Metadata = {
  title: "Performa - Autonomous Security Agent",
  description:
    "AI-powered autonomous cybersecurity agent dashboard for vulnerability assessment and penetration testing",
  generator: "v0.app",
  icons: {
    icon: "/performa-logo.png",
    apple: "/performa-logo.png",
  },
}

export const viewport: Viewport = {
  themeColor: "#1a1a2e",
  colorScheme: "dark",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`font-sans antialiased`}>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
