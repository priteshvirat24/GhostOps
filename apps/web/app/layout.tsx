import React from 'react';
import './globals.css';

export const metadata = {
  title: 'GhostOps - Autonomous Institutional Memory & Remediation',
  description: 'The production memory that survives the engineer.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0B0F19] text-gray-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
