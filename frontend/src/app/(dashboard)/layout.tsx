"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import {
  LayoutDashboard,
  Plus,
  Settings,
  Menu,
  Film,
  LogOut,
  User,
  CreditCard,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

const NAV_ITEMS = [
  { href: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { href: "/projects/new", label: "새 영상", icon: Plus },
  { href: "/pricing", label: "가격 안내", icon: CreditCard },
  { href: "/settings", label: "설정", icon: Settings },
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

function UserMenu() {
  const { user, plan, signOut } = useAuth();
  if (!user) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3 px-3 py-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800 border border-zinc-700 relative">
           <User className="h-4 w-4 text-zinc-400" />
           {plan === "pro" && (
             <div className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 border border-zinc-950">
               <Zap className="h-2.5 w-2.5 text-white fill-white" />
             </div>
           )}
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-zinc-200 truncate max-w-[100px]">
                {user.email?.split("@")[0]}
            </span>
            {plan === "pro" ? (
                <span className="rounded bg-indigo-500/20 px-1 py-0.5 text-[8px] font-bold text-indigo-400 border border-indigo-500/30 uppercase tracking-tighter">
                   Pro
                </span>
            ) : (
                <span className="rounded bg-zinc-800 px-1 py-0.5 text-[8px] font-bold text-zinc-500 border border-zinc-700 uppercase tracking-tighter">
                   Free
                </span>
            )}
          </div>
          <span className="text-[10px] text-zinc-500 truncate max-w-[140px]">
            {user.email}
          </span>
        </div>
      </div>
      <Button 
        variant="ghost" 
        size="sm" 
        onClick={() => signOut()}
        className="flex items-center justify-start gap-3 px-3 py-2 h-9 text-zinc-400 hover:text-red-400 hover:bg-red-950/20"
      >
        <LogOut className="h-4 w-4" />
        <span className="text-sm font-medium">로그아웃</span>
      </Button>
    </div>
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
          <UserMenu />
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
            <Sheet>
              <SheetTrigger 
                render={
                  <Button variant="ghost" size="icon">
                     <Menu className="h-5 w-5" />
                  </Button>
                } 
              />
              <SheetContent side="left" className="w-64 bg-zinc-950 p-4 flex flex-col">
                <div className="mb-6 flex items-center gap-2 px-3 pt-4">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-brand">
                    <Film className="h-4 w-4 text-white" />
                  </div>
                  <span className="text-lg font-semibold gradient-brand-text">AutoTube</span>
                </div>
                <NavLinks />
                <div className="mt-auto pb-4">
                  <Separator className="mb-4 bg-zinc-800" />
                  <UserMenu />
                </div>
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
