import axios from "axios";

export const BACKEND_BASE_URL =
  import.meta.env.VITE_BACKEND_URL ??
  (import.meta.env.DEV ? "http://localhost:8000" : "");

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (BACKEND_BASE_URL ? `${BACKEND_BASE_URL}/api/v1` : "/api/v1");

export function getMediaUrl(urlPath?: string | null): string {
  if (!urlPath) return "";
  if (urlPath.startsWith("http://") || urlPath.startsWith("https://")) {
    return urlPath;
  }
  const cleanPath = urlPath.startsWith("/") ? urlPath : `/${urlPath}`;
  return BACKEND_BASE_URL ? `${BACKEND_BASE_URL}${cleanPath}` : cleanPath;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("civiclens_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if expired
      localStorage.removeItem("civiclens_token");
      localStorage.removeItem("civiclens_user");
    }
    return Promise.reject(error);
  }
);
