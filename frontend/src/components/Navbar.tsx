"use client";

import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";
import { LogOut, Shield, Eye } from "lucide-react";

interface NavbarProps {
  user: User;
}

export default function Navbar({ user }: NavbarProps) {
  const router = useRouter();

  const handleLogout = () => {
    api.clearToken();
    router.push("/login");
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-blue-600">TechKraft</h1>
        <span className="text-gray-300">|</span>
        <span className="text-sm text-gray-500">Candidate Dashboard</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-full">
          {user.role === "admin" ? (
            <Shield className="h-4 w-4 text-amber-500" />
          ) : (
            <Eye className="h-4 w-4 text-blue-500" />
          )}
          <span className="text-sm font-medium">{user.full_name}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 capitalize">
            {user.role}
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </nav>
  );
}
