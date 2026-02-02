// adminApi.js
import apiClient from "./apiClient";

const BASE_URL = "/api/admin";

// ===============================
// 👥 USERS
// ===============================

// 📋 fetch users (có search)
export async function fetchUsers(query = "") {
  const res = await apiClient.get(`${BASE_URL}/users/`, {
    params: query ? { q: query } : {},
  });
  return res.data;
}

// 👤 user detail
export async function fetchUserDetail(userId) {
  const res = await apiClient.get(`${BASE_URL}/users/${userId}/`);
  return res.data;
}

// 🚫 ban / unban
export async function banOrUnbanUser(userId) {
  const res = await apiClient.post(
    `${BASE_URL}/users/${userId}/ban/`
  );
  return res.data;
}

// ⭐ update premium
export async function updatePremium(userId, days) {
  const res = await apiClient.post(
    `${BASE_URL}/users/${userId}/premium/`,
    { days }
  );
  return res.data;
}

// ❌ delete user
export async function deleteUser(userId) {
  const res = await apiClient.delete(
    `${BASE_URL}/users/${userId}/delete/`
  );
  return res.data;
}

// 📜 audit logs
export async function fetchAuditLogs() {
  const res = await apiClient.get(`${BASE_URL}/audit-logs/`);
  return res.data;
}
