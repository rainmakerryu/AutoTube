"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import {
  LayoutDashboard,
  Plus,
  Settings,
  Menu,
  Film,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects/new", label: "New Video", icon: Plus },
  { href: "/settings", label: "Settings", icon: Settings },
] as const;

function NavLinks({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onClick}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-violet-950/60 text-violet-200 border border-violet-800/40"
                : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
            }`}
          >
            <Icon className={`h-4 w-4 ${isActive ? "text-violet-400" : ""}`} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full min-h-screen">
      <aside className="hidden w-64 flex-col border-r border-zinc-800 bg-zinc-950 p-4 md:flex">
        <div className="mb-6 flex items-center gap-2 px-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-brand">
            <Film className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-semibold gradient-brand-text">AutoTube</span>
        </div>
        <NavLinks />
        <div className="mt-auto pt-4">
          <Separator className="mb-4 bg-zinc-800" />
          <div className="flex items-center gap-3 px-3">
            <UserButton signInUrl="/login" />
            <span className="text-sm text-zinc-400">Account</span>
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4 md:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md gradient-brand">
              <Film className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="font-semibold gradient-brand-text">AutoTube</span>
          </div>
          <div className="flex items-center gap-3">
            <UserButton signInUrl="/login" />
            <Sheet>
              <SheetTrigger render={<Button variant="ghost" size="icon" />}>
                  <Menu className="h-5 w-5" />
              </SheetTrigger>
              <SheetContent side="left" className="w-64 bg-zinc-950 p-4">
                <div className="mb-6 flex items-center gap-2 px-3 pt-4">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-brand">
                    <Film className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-lg font-semibold gradient-brand-text">AutoTube</span>
                </div>
                <NavLinks />
              </SheetContent>
            </Sheet>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-zinc-950 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
