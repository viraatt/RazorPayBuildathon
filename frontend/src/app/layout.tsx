import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Finance-Ops Reconciliation Agent',
  description: 'Automated 3-layer reconciliation engine powered by Gemini 2.0 Flash',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        {children}
      </body>
    </html>
  )
}
