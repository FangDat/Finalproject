// apiClient.js
import axios from "axios";
import { forceLogout } from "./authService";

const API_BASE_URL = "https://api.vietcloud.work";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 15000,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";

    // ❗ Những endpoint KHÔNG được auto logout
    const SAFE_AUTH_ENDPOINTS = [
      "/api/login/",
      "/api/signup/",
      "/api/verify-otp/",
      "/api/resend-otp/",
      "/api/forgot-password/",
      "/api/change-email/verify-password/",
      "/api/change-email/verify-otp/",
      "/api/change-password/",
    ];

    const isSafeEndpoint = SAFE_AUTH_ENDPOINTS.some((ep) =>
      url.includes(ep)
    );

    /*
      🔥 CHỈ logout khi:
      - 401 / 403
      - KHÔNG phải auth-related endpoint
    */
    if (
      (status === 401 || status === 403) &&
      !isSafeEndpoint
    ) {
      console.warn("🚫 Auth expired → force logout");
      await forceLogout();
    }

    return Promise.reject(error);
  }
);

export default apiClient;
