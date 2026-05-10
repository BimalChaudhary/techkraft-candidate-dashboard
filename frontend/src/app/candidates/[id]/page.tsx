"use client";

import { use, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CandidateDetail, User } from "@/lib/types";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import ScoreStars from "@/components/ScoreStars";
import {
  ArrowLeft,
  Mail,
  Briefcase,
  Star,
  Sparkles,
  FileText,
  Loader2,
  Send,
  AlertCircle,
} from "lucide-react";

const CATEGORIES = [
  "Technical Skills",
  "Communication",
  "Problem Solving",
  "Culture Fit",
  "Leadership",
];

export default function CandidateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Score form
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [score, setScore] = useState(4);
  const [note, setNote] = useState("");
  const [submittingScore, setSubmittingScore] = useState(false);

  // AI Summary
  const [generatingSummary, setGeneratingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState("");

  // Internal notes
  const [editingNotes, setEditingNotes] = useState(false);
  const [internalNotes, setInternalNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser || !localStorage.getItem("token")) {
      router.replace("/login");
      return;
    }
    setUser(JSON.parse(storedUser));
  }, [router]);

  const fetchCandidate = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getCandidate(id);
      setCandidate(data);
      setInternalNotes(data.internal_notes || "");
    } catch {
      setError("Failed to load candidate");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (user) fetchCandidate();
  }, [user, fetchCandidate]);

  const handleSubmitScore = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingScore(true);
    try {
      await api.submitScore(id, { category, score, note: note || undefined });
      setNote("");
      await fetchCandidate();
    } catch {
      setError("Failed to submit score");
    } finally {
      setSubmittingScore(false);
    }
  };

  const handleGenerateSummary = async () => {
    setGeneratingSummary(true);
    setSummaryError("");
    try {
      await api.generateSummary(id);
      await fetchCandidate();
    } catch (err) {
      setSummaryError(err instanceof Error ? err.message : "Failed to generate summary");
    } finally {
      setGeneratingSummary(false);
    }
  };

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    try {
      await api.updateCandidate(id, { internal_notes: internalNotes });
      setEditingNotes(false);
      await fetchCandidate();
    } catch {
      setError("Failed to save notes");
    } finally {
      setSavingNotes(false);
    }
  };

  if (!user) return null;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} />
        <div className="flex items-center justify-center py-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  if (error && !candidate) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} />
        <div className="flex flex-col items-center justify-center py-32 text-red-500">
          <AlertCircle className="h-12 w-12 mb-3" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!candidate) return null;

  const avgScore =
    candidate.scores.length > 0
      ? candidate.scores.reduce((sum, s) => sum + s.score, 0) / candidate.scores.length
      : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Back */}
        <button
          onClick={() => router.push("/dashboard")}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6 transition"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to candidates
        </button>

        {/* Profile Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xl font-bold">
              {candidate.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900">{candidate.name}</h2>
              <div className="flex flex-wrap items-center gap-4 mt-1 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Mail className="h-3.5 w-3.5" />
                  {candidate.email}
                </span>
                <span className="flex items-center gap-1">
                  <Briefcase className="h-3.5 w-3.5" />
                  {candidate.role_applied}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mt-3">
                {candidate.skills.map((skill) => (
                  <span key={skill} className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <StatusBadge status={candidate.status} />
              {candidate.scores.length > 0 && (
                <div className="flex items-center gap-2">
                  <ScoreStars score={Math.round(avgScore)} size="md" />
                  <span className="text-lg font-bold text-gray-900">{avgScore.toFixed(1)}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Scores + Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Existing Scores */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="flex items-center gap-2 text-lg font-semibold mb-4">
                <Star className="h-5 w-5 text-amber-500" />
                Scores ({candidate.scores.length})
              </h3>
              {candidate.scores.length > 0 ? (
                <div className="space-y-3">
                  {candidate.scores.map((s) => (
                    <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium text-sm">{s.category}</div>
                        {s.reviewer_name && (
                          <div className="text-xs text-gray-500">by {s.reviewer_name}</div>
                        )}
                        {s.note && <div className="text-xs text-gray-500 mt-1">{s.note}</div>}
                      </div>
                      <ScoreStars score={s.score} />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">No scores yet. Be the first to review!</p>
              )}
            </div>

            {/* Score Form */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="flex items-center gap-2 text-lg font-semibold mb-4">
                <Send className="h-5 w-5 text-blue-500" />
                Submit a Score
              </h3>
              <form onSubmit={handleSubmitScore} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Score</label>
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((val) => (
                        <button
                          key={val}
                          type="button"
                          onClick={() => setScore(val)}
                          className="p-1"
                        >
                          <Star
                            className={`h-7 w-7 transition ${
                              val <= score
                                ? "fill-amber-400 text-amber-400"
                                : "text-gray-300 hover:text-amber-300"
                            }`}
                          />
                        </button>
                      ))}
                      <span className="ml-2 text-sm font-medium text-gray-600">{score}/5</span>
                    </div>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Note (optional)</label>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Add your assessment notes..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={submittingScore}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                >
                  {submittingScore ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  Submit Score
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Summary + Notes */}
          <div className="space-y-6">
            {/* AI Summary */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="flex items-center gap-2 text-lg font-semibold mb-4">
                <Sparkles className="h-5 w-5 text-purple-500" />
                AI Summary
              </h3>
              {candidate.summaries.length > 0 ? (
                <div className="space-y-4">
                  {candidate.summaries.map((s) => (
                    <div key={s.id} className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{s.content}</pre>
                      <div className="mt-2 text-xs text-gray-400">
                        Generated {new Date(s.generated_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400 mb-4">No AI summary generated yet.</p>
              )}
              <button
                onClick={handleGenerateSummary}
                disabled={generatingSummary}
                className="mt-4 flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition disabled:opacity-50 w-full justify-center"
              >
                {generatingSummary ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate AI Summary
                  </>
                )}
              </button>
              {summaryError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {summaryError}
                </div>
              )}
            </div>

            {/* Internal Notes (Admin Only) */}
            {user.role === "admin" && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="flex items-center gap-2 text-lg font-semibold mb-4">
                  <FileText className="h-5 w-5 text-amber-500" />
                  Internal Notes
                  <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full ml-auto">
                    Admin Only
                  </span>
                </h3>
                {editingNotes ? (
                  <div className="space-y-3">
                    <textarea
                      value={internalNotes}
                      onChange={(e) => setInternalNotes(e.target.value)}
                      rows={6}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                      placeholder="Add internal notes about this candidate..."
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveNotes}
                        disabled={savingNotes}
                        className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                      >
                        {savingNotes ? "Saving..." : "Save"}
                      </button>
                      <button
                        onClick={() => {
                          setEditingNotes(false);
                          setInternalNotes(candidate.internal_notes || "");
                        }}
                        className="px-3 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    {candidate.internal_notes ? (
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{candidate.internal_notes}</p>
                    ) : (
                      <p className="text-sm text-gray-400">No internal notes yet.</p>
                    )}
                    <button
                      onClick={() => setEditingNotes(true)}
                      className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      {candidate.internal_notes ? "Edit Notes" : "Add Notes"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
