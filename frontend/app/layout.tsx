import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Remote Jobs Platform - US Salary Only',
  description: 'Find remote technical and design jobs with US-level salaries. AI-curated remote opportunities that hire worldwide.',
  keywords: 'remote jobs, US salary, technical jobs, design jobs, work from home, global hiring',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
