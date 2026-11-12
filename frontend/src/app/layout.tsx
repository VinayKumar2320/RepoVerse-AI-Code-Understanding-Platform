import React from 'react';
import '../styles/globals.css';
import { Navbar } from '../components/layout/Navbar';

export const metadata = {
  title: 'RepoVerse — Interactive GitHub Repository Digital Twin & AI Code Understanding Platform',
  description: 'Understand Code. Explore Architecture. Travel Through Git History.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 flex flex-col p-4 md:p-6 overflow-x-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
