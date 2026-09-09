// CivicLens AI - JavaScript React API Client
// Supports seamless switching between Python FastAPI (port 8000) and Java Spring Boot (port 8080)
import axios from "axios";

export const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || "8000"; // Set to 8080 for Spring Boot
export const BACKEND_BASE_URL =
  import.meta.env.VITE_BACKEND_URL ||
  (import.meta.env.DEV ? `http://localhost:${BACKEND_PORT}` : "");

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (BACKEND_BASE_URL ? `${BACKEND_BASE_URL}/api/v1` : "/api/v1");

export function getMediaUrl(urlPath) {
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
      localStorage.removeItem("civiclens_token");
      localStorage.removeItem("civiclens_user");
    }
    return Promise.reject(error);
  }
);
