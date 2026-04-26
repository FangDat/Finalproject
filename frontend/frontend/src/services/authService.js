// authService.js
import apiClient from "./apiClient";

let isLoggingOut = false; // Flag to prevent multiple logout calls

// ===============================
// FORCE LOGOUT (AXIOS)
// ===============================
export async function forceLogout() { // Function to force user logout
  if (isLoggingOut) return; // Prevent duplicate logout execution
  isLoggingOut = true;  // Set flag to indicate logout in progress

  try { 
    await apiClient.post("/api/logout/"); // Call backend logout API
  } catch (e) {
    console.warn("Logout API failed", e); // Log warning if API fails
  } finally {
    // 🧹 clear browser storage
    localStorage.clear(); // Remove all local storage data

    document.cookie =
      "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie =
      "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie =
      "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

    setTimeout(() => {
      isLoggingOut = false; // Allow future logout again
    }, 500);
  }
}

/* ======================================================
   AUTH APIs (AXIOS ONLY)
====================================================== */

// 🔄 refresh access token
export async function refreshToken() {  // Refresh authentication token
  await apiClient.post("/api/refresh/");  
  return true;  // Return success status
}

// Get current user info
export async function getUserInfo() {
  const res = await apiClient.get("/api/user-info/"); // Call user info API
  return res.data;
}

// 📝 Signup
export async function signup(payload) {
  const res = await apiClient.post("/api/signup/", payload);  // Send signup data
  return res.data;
}

// 🔐 Verify OTP
export async function verifySignupOtp(email, otp) {
  const res = await apiClient.post("/api/verify-otp/", { email, otp }); // Send email + OTP
  return res.data;
}

// 🔁 Resend OTP
export async function resendSignupOtp(email) {  // Resend OTP to user
  await apiClient.post("/api/resend-otp/", { email });  // Call resend OTP API
  return true;
}
