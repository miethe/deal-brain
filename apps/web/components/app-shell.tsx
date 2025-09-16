"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { Menu, Package2, Settings } from "lucide-react";

import { Button } from "./ui/button";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/profiles", label: "Profiles" },
  { href: "/valuation-rules", label: "Valuation Rules" },
  { href: "/import", label: "Import" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-muted/40">
      <aside className="hidden w-64 flex-col border-r bg-background p-4 md:flex">
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
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-background px-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="hidden text-sm font-medium text-foreground md:inline">Deal Brain</span>
            <span>Personal SFF deal intelligence</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="rounded-full bg-primary/10 px-3 py-1 text-primary">MVP build</span>
          </div>
        </header>
        <main className="flex-1 space-y-6 p-6">{children}</main>
      </div>
    </div>
  );
}
