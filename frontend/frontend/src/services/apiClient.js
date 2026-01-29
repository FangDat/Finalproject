// apiClient.js
import { forceLogout } from "./authService";

export async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    credentials: "include",
    ...options,
  });

  if (res.status === 401 || res.status === 403) {
    // 🔒 Unauthorized → logout (đã có lock chống lặp)
    forceLogout();
    throw new Error("Unauthorized");
  }

  return res;
}
