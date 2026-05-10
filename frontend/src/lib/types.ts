export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "reviewer";
  created_at: string;
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  role_applied: string;
  status: "new" | "reviewed" | "hired" | "rejected" | "archived";
  skills: string[];
  internal_notes: string | null;
  created_at: string;
}

export interface CandidateDetail extends Candidate {
  scores: Score[];
  summaries: Summary[];
}

export interface Score {
  id: string;
  candidate_id: string;
  category: string;
  score: number;
  reviewer_id: string;
  reviewer_name: string | null;
  note: string | null;
  created_at: string;
}

export interface Summary {
  id: string;
  candidate_id: string;
  content: string;
  average_score: number | null;
  generated_at: string;
}

export interface PaginatedCandidates {
  items: Candidate[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
