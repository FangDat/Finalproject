// authService.js

let isLoggingOut = false;

export async function forceLogout() {
  if (isLoggingOut) {
    return;
  }

  isLoggingOut = true;

  try {
    await fetch("http://localhost:8000/api/logout/", {
      method: "POST",
      credentials: "include",
    });
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

    // 🔓 reset lock cho lần sau
    setTimeout(() => {
      isLoggingOut = false;
    }, 500);
  }
}
