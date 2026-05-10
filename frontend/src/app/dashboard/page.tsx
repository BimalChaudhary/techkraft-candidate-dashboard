"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Candidate, PaginatedCandidates, User } from "@/lib/types";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import Pagination from "@/components/Pagination";
import { Search, Filter, Users, ChevronRight } from "lucide-react";

const STATUSES = ["", "new", "reviewed", "hired", "rejected"];

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [data, setData] = useState<PaginatedCandidates | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: "",
    role_applied: "",
    skill: "",
    keyword: "",
    page: 1,
    page_size: 10,
  });

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser || !localStorage.getItem("token")) {
      router.replace("/login");
      return;
    }
    setUser(JSON.parse(storedUser));
  }, [router]);

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getCandidates(filters);
      setData(result);
    } catch {
      api.clearToken();
      router.replace("/login");
    } finally {
      setLoading(false);
    }
  }, [filters, router]);

  useEffect(() => {
    if (user) fetchCandidates();
  }, [user, fetchCandidates]);

  const updateFilter = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Candidates</h2>
            <p className="text-sm text-gray-500 mt-1">
              {data ? `${data.total} total candidates` : "Loading..."}
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Users className="h-4 w-4" />
            Signed in as <span className="font-medium capitalize">{user.role}</span>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex items-center gap-2 mb-3 text-sm font-medium text-gray-700">
            <Filter className="h-4 w-4" />
            Filters
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, email, role..."
                value={filters.keyword}
                onChange={(e) => updateFilter("keyword", e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <select
              value={filters.status}
              onChange={(e) => updateFilter("status", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
            >
              <option value="">All Statuses</option>
              {STATUSES.filter(Boolean).map((s) => (
                <option key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Filter by role..."
              value={filters.role_applied}
              onChange={(e) => updateFilter("role_applied", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <input
              type="text"
              placeholder="Filter by skill..."
              value={filters.skill}
              onChange={(e) => updateFilter("skill", e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Candidate Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Candidate
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Role Applied
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Skills
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.items.map((candidate: Candidate) => (
                      <tr
                        key={candidate.id}
                        onClick={() => router.push(`/candidates/${candidate.id}`)}
                        className="hover:bg-blue-50/50 cursor-pointer transition"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-medium">
                              {candidate.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900">{candidate.name}</div>
                              <div className="text-xs text-gray-500">{candidate.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-700">{candidate.role_applied}</td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1">
                            {candidate.skills.slice(0, 3).map((skill) => (
                              <span
                                key={skill}
                                className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                              >
                                {skill}
                              </span>
                            ))}
                            {candidate.skills.length > 3 && (
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-400 rounded text-xs">
                                +{candidate.skills.length - 3}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={candidate.status} />
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {new Date(candidate.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="border-t border-gray-200 px-6 py-4">
                <Pagination
                  page={data.page}
                  totalPages={data.total_pages}
                  onPageChange={(p) => setFilters((prev) => ({ ...prev, page: p }))}
                />
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <Users className="h-12 w-12 mb-3" />
              <p className="text-lg font-medium">No candidates found</p>
              <p className="text-sm">Try adjusting your filters</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
