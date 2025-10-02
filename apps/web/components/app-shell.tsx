"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useState } from "react";
import { Menu, Package2, Settings, X } from "lucide-react";

import { Button } from "./ui/button";
import { cn } from "../lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/profiles", label: "Profiles" },
  { href: "/valuation-rules", label: "Valuation Rules" },
  { href: "/global-fields", label: "Global Fields" },
  { href: "/import", label: "Import" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen w-full overflow-x-hidden bg-muted/40">
      {/* Sticky Navbar */}
      <header className="fixed top-0 left-0 right-0 z-[100] flex h-14 items-center justify-between border-b bg-background/95 backdrop-blur px-4">
        <div className="flex items-center gap-2">
          {/* Mobile menu toggle */}
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="hidden text-sm font-medium text-foreground md:inline">Deal Brain</span>
            <span className="hidden sm:inline">Personal SFF deal intelligence</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="rounded-full bg-primary/10 px-3 py-1 text-xs text-primary">MVP build</span>
        </div>
      </header>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-[80] bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Fixed Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-14 z-[90] h-[calc(100vh-3.5rem)] w-64 flex-col border-r bg-background p-4 transition-transform",
          "lg:translate-x-0 lg:flex", // Always visible on desktop
          sidebarOpen ? "flex translate-x-0" : "-translate-x-full" // Toggle on mobile
        )}
      >
        <div className="flex items-center gap-2 px-2 text-lg font-semibold">
          <Package2 className="h-6 w-6" />
          Deal Brain
        </div>
        <nav className="mt-6 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setSidebarOpen(false)} // Close sidebar on mobile after navigation
                className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto flex flex-col gap-2 px-2 text-xs text-muted-foreground/80">
          <span className="font-medium">Quick actions</span>
          <Button variant="secondary" size="sm">
            <Menu className="mr-2 h-4 w-4" /> Command Palette (⌘K)
          </Button>
          <Button variant="ghost" size="sm">
            <Settings className="mr-2 h-4 w-4" /> Settings
          </Button>
        </div>
      </aside>

      {/* Main content with top and left margin */}
      <main className="flex-1 pt-14 lg:ml-64 overflow-x-hidden">
        <div className="space-y-6 p-6">{children}</div>
      </main>
    </div>
  );
}
