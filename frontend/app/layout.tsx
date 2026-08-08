import './globals.css';
import { Inter } from 'next/font/google';
import { ThemeProvider } from 'next-themes';
import React from 'react';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'InterviewAI — Your Personal Technical Interviewer',
  description: 'Adaptive AI Technical Interview Agent Platform for evaluating AI Engineering knowledge.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

