"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useState, useEffect } from "react";
import { Menu, Package2, Settings, X, ChevronRight } from "lucide-react";

import { Button } from "./ui/button";
import { ThemeToggle } from "./ui/theme-toggle";
import { Toaster } from "./ui/toaster";
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "./ui/collapsible";
import { cn } from "../lib/utils";

type NavLink = {
  type: "link";
  href: string;
  label: string;
};

type NavDropdown = {
  type: "dropdown";
  label: string;
  items: Array<{ href: string; label: string }>;
};

type NavItem = NavLink | NavDropdown;

const NAV_ITEMS: NavItem[] = [
  { type: "link", href: "/", label: "Dashboard" },
  { type: "link", href: "/listings", label: "Listings" },
  { type: "link", href: "/builder", label: "Builder" },
  {
    type: "dropdown",
    label: "Catalogs",
    items: [
      { href: "/cpus", label: "CPUs" },
    ]
  },
  { type: "link", href: "/profiles", label: "Profiles" },
  { type: "link", href: "/valuation-rules", label: "Valuation Rules" },
  { type: "link", href: "/global-fields", label: "Global Fields" },
  { type: "link", href: "/import", label: "Import" },
  { type: "link", href: "/admin", label: "Admin" }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [catalogsOpen, setCatalogsOpen] = useState(true);

  // Restore catalogs dropdown state from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('nav:catalogs-open');
      if (stored !== null) {
        setCatalogsOpen(stored === 'true');
      }
    } catch (error) {
      // Handle SecurityError in private browsing mode or when localStorage is disabled
      console.warn('localStorage access denied:', error);
    }
  }, []);

  // Persist catalogs dropdown state to localStorage
  const handleCatalogsToggle = (open: boolean) => {
    setCatalogsOpen(open);
    try {
      localStorage.setItem('nav:catalogs-open', String(open));
    } catch (error) {
      // Handle SecurityError in private browsing mode or when localStorage is disabled
      console.warn('localStorage write failed:', error);
    }
  };

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
          <ThemeToggle />
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
          {NAV_ITEMS.map((item, index) => {
            if (item.type === "link") {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)} // Close sidebar on mobile after navigation
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  {item.label}
                </Link>
              );
            }

            // Handle dropdown items
            if (item.type === "dropdown") {
              const isAnyChildActive = item.items.some((child) => pathname.startsWith(child.href));

              return (
                <Collapsible
                  key={`dropdown-${index}`}
                  open={catalogsOpen}
                  onOpenChange={handleCatalogsToggle}
                >
                  <CollapsibleTrigger
                    className={cn(
                      "flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isAnyChildActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                    aria-expanded={catalogsOpen}
                  >
                    <span>{item.label}</span>
                    <ChevronRight
                      className={cn(
                        "h-4 w-4 transition-transform duration-200",
                        catalogsOpen && "rotate-90"
                      )}
                    />
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div role="group" className="flex flex-col gap-1 pt-1">
                      {item.items.map((child) => {
                        const childActive = pathname === child.href;
                        return (
                          <Link
                            key={child.href}
                            href={child.href}
                            onClick={() => setSidebarOpen(false)}
                            className={cn(
                              "rounded-md pl-8 pr-3 py-2 text-sm font-medium transition-colors",
                              childActive
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted"
                            )}
                          >
                            {child.label}
                          </Link>
                        );
                      })}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              );
            }

            return null;
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

      {/* Toast notifications */}
      <Toaster />
    </div>
  );
}
