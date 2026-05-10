import type {
  CandidateDetail,
  PaginatedCandidates,
  Score,
  Summary,
  TokenResponse,
  User,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed: ${res.status}`);
    }

    if (res.status === 204) return undefined as T;
    return res.json();
  }

  // Auth
  async login(email: string, password: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }

  async register(email: string, password: string, full_name: string): Promise<User> {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // Candidates
  async getCandidates(params: Record<string, string | number>): Promise<PaginatedCandidates> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== "" && v !== undefined && v !== null) query.set(k, String(v));
    });
    return this.request<PaginatedCandidates>(`/candidates?${query.toString()}`);
  }

  async getCandidate(id: string): Promise<CandidateDetail> {
    return this.request<CandidateDetail>(`/candidates/${id}`);
  }

  async updateCandidate(id: string, data: Record<string, unknown>): Promise<CandidateDetail> {
    return this.request<CandidateDetail>(`/candidates/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteCandidate(id: string): Promise<void> {
    return this.request<void>(`/candidates/${id}`, { method: "DELETE" });
  }

  // Scores
  async submitScore(candidateId: string, data: { category: string; score: number; note?: string }): Promise<Score> {
    return this.request<Score>(`/candidates/${candidateId}/scores`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Summary
  async generateSummary(candidateId: string): Promise<Summary> {
    return this.request<Summary>(`/candidates/${candidateId}/summary`, {
      method: "POST",
    });
  }
}

export const api = new ApiClient();
