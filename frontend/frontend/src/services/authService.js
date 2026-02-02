// authService.js
import apiClient from "./apiClient";

let isLoggingOut = false;

// ===============================
// FORCE LOGOUT (DÙNG AXIOS)
// ===============================
export async function forceLogout() {
  if (isLoggingOut) return;
  isLoggingOut = true;

  try {
    await apiClient.post("/api/logout/");
  } catch (e) {
    console.warn("Logout API failed", e);
  } finally {
    // 🧹 clear browser storage
    localStorage.clear();

    document.cookie =
      "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie =
      "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie =
      "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

    setTimeout(() => {
      isLoggingOut = false;
    }, 500);
  }
}

/* ======================================================
   AUTH APIs (AXIOS ONLY)
====================================================== */

// 🔄 refresh access token
export async function refreshToken() {
  await apiClient.post("/api/refresh/");
  return true;
}

// 👤 lấy thông tin user
export async function getUserInfo() {
  const res = await apiClient.get("/api/user-info/");
  return res.data;
}

// 📝 Signup
export async function signup(payload) {
  const res = await apiClient.post("/api/signup/", payload);
  return res.data;
}

// 🔐 Verify OTP
export async function verifySignupOtp(email, otp) {
  const res = await apiClient.post("/api/verify-otp/", { email, otp });
  return res.data;
}

// 🔁 Resend OTP
export async function resendSignupOtp(email) {
  await apiClient.post("/api/resend-otp/", { email });
  return true;
}
