// apiClient.js
import { forceLogout } from "./authService";

export async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    ...options,
  });

  if (res.status === 401 || res.status === 403) {
    // 🟡 nếu là manual logout → bỏ qua 1 lần DUY NHẤT
    if (sessionStorage.getItem("vietcloud_manual_logout")) {
      sessionStorage.removeItem("vietcloud_manual_logout"); // 🔥 XOÁ NGAY
      throw new Error("Unauthorized after manual logout");
    }

    // 🔴 hệ thống / bị ban
    if (!sessionStorage.getItem("vietcloud_force_logged_out")) {
      await forceLogout(
        "🚫 Your account has been disabled or session expired.",
        "system"
      );
    }

    throw new Error("Unauthorized");
  }

  return res;
}
