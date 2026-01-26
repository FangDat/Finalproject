// authService.js
export async function forceLogout(message = "", reason = "system") {
  // ❗ Nếu logout chủ động → KHÔNG hiển thị warning
  if (reason === "manual") {
    sessionStorage.setItem("vietcloud_manual_logout", "1");
  }

  if (sessionStorage.getItem("vietcloud_force_logged_out")) {
    return;
  }

  sessionStorage.setItem("vietcloud_force_logged_out", "1");

  if (message && reason !== "manual") {
    alert(message);
  }

  try {
    await fetch("http://localhost:8000/api/logout/", {
      method: "POST",
      credentials: "include",
    });
  } catch (e) {
    console.warn("Logout API failed", e);
  } finally {
    localStorage.clear();

    document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

    window.location.href = "/#/login";
  }
}
