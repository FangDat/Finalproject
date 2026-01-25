const BASE_URL = "http://localhost:8000/api/admin";

async function handleResponse(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "API error");
  }
  return res.json();
}

export async function fetchUsers() {
  const res = await fetch(`${BASE_URL}/users/`, {
    credentials: "include",
  });
  return handleResponse(res);
}

export async function fetchUserDetail(userId) {
  const res = await fetch(`${BASE_URL}/users/${userId}/`, {
    credentials: "include",
  });
  return handleResponse(res);
}

export async function banOrUnbanUser(userId) {
  const res = await fetch(`${BASE_URL}/users/${userId}/ban/`, {
    method: "POST",
    credentials: "include",
  });
  return handleResponse(res);
}

export async function updatePremium(userId, days) {
  const res = await fetch(`${BASE_URL}/users/${userId}/premium/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days }),
  });
  return handleResponse(res);
}

export async function deleteUser(userId) {
  const res = await fetch(`${BASE_URL}/users/${userId}/delete/`, {
    method: "DELETE",
    credentials: "include",
  });
  return handleResponse(res);
}

export async function fetchAuditLogs() {
  const res = await fetch(`${BASE_URL}/audit-logs/`, {
    credentials: "include",
  });
  return handleResponse(res);
}
