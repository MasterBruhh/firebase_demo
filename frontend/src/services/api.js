// frontend/src/services/api.js
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ----- Interceptor global -----
api.interceptors.request.use((config) => {
  if (!config.headers.Authorization) {
    const token = localStorage.getItem("idToken");
    if (token && token !== "null") {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// ---------- APIs ----------
export const authAPI = {
  register: (email, password) => api.post("/auth/register", { email, password }),
  getCurrentUser: () => api.get("/auth/me"),          // token via interceptor
  testAdminRoute: () => api.get("/auth/admin-only-test"),
};

export const documentsAPI = {
  upload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/documents/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  search: (query) => api.get(`/documents/search?query=${encodeURIComponent(query)}`),
  list:   ()      => api.get("/documents/list"),
  download: (id)  => api.get(`/documents/download/${id}`),
};

export const auditAPI = {
  logEvent: (eventType, eventDetails = {}) => {
    return api.post("/audit/event", {
      event_type: eventType,
      details: eventDetails,
    });
  },

  getLogs: (limit = 100) => {
    return api.get(`/audit/logs?limit=${limit}`);
  },
};

export default api;
