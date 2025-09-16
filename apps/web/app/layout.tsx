import "./globals.css";

import { ReactNode } from "react";

import { AppShell } from "../components/app-shell";
import { Providers } from "../components/providers";

export const metadata = {
  title: "Deal Brain",
  description: "Price-to-performance intelligence for SFF PCs"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}

