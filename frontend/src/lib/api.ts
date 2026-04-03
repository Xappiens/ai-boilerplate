/**
 * API Client with JWT Interceptor
 * =================================
 * Axios instance configured to automatically inject
 * the JWT token from localStorage into all requests.
 */

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor: Inject JWT ────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor: Handle 401 ──────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Redirect to login if not already there
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth API ──────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    const { data } = await api.post<LoginResponse>("/api/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("access_token", data.access_token);
    return data;
  },

  register: async (
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ): Promise<UserProfile> => {
    const { data } = await api.post<UserProfile>("/api/auth/register", {
      email,
      password,
      first_name: firstName || null,
      last_name: lastName || null,
    });
    return data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const { data } = await api.get<UserProfile>("/api/users/me");
    return data;
  },

  logout: () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  },
};

// ── Documents API ─────────────────────────────────────────────

export interface Document {
  id: string;
  title: string;
  content: string;
  status: "pending" | "queued" | "processing" | "completed" | "failed";
  ai_summary: string | null;
  ai_model_used: string | null;
  owner_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TaskEnqueuedResponse {
  message: string;
  document_id: string;
  status: string;
}

export const documentsApi = {
  list: async (): Promise<Document[]> => {
    const { data } = await api.get<Document[]>("/api/documents/");
    return data;
  },

  create: async (title: string, content: string): Promise<Document> => {
    const { data } = await api.post<Document>("/api/documents/", { title, content });
    return data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await api.get<Document>(`/api/documents/${id}`);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/documents/${id}`);
  },

  process: async (id: string): Promise<TaskEnqueuedResponse> => {
    const { data } = await api.post<TaskEnqueuedResponse>(
      `/api/documents/${id}/process`
    );
    return data;
  },
};

export default api;
