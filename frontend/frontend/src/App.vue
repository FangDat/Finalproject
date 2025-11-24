<template>
  <div id="app">
    <!-- Header hiển thị VietCloud + auth -->
    <header v-if="showHeader" class="app-header">
      <h1 class="logo-title">VietCloud</h1>

      <div class="spacer"></div>

      <div class="auth-wrapper">
        <h2 v-if="username" class="hello-text">Hello, {{ username }}</h2>
        <div class="auth-btn">
          <router-link v-if="!username" to="/login">
            <button class="btn-login">Login</button>
          </router-link>
          <button v-else class="btn-logout" @click="logout">Logout</button>
        </div>
      </div>
    </header>

    <router-view />
  </div>
</template>
<script>
export default {
  name: "App",
  data() {
    return {
      username: this.getCookie("username") || "",
      refreshInterval: null, // interval refresh token
    };
  },
  computed: {
    showHeader() {
      const path = this.$route.path;
      return !(path === "/login" || path === "/signup" || path === "/credit-card");
    },
  },
  methods: {
    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    },

    async logout() {
      try {
        const res = await fetch("http://localhost:8000/api/logout/", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });

        document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie = "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        this.username = "";
        this.$router.push("/");
        window.location.reload();
      } catch (err) {
        console.error("Logout failed", err);
        document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        document.cookie = "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        this.username = "";
        this.$router.push("/");
        window.location.reload();
      }
    },

    // -------------------------------
    // 🔄 Refresh token tự động
    // -------------------------------
    async refreshToken() {
      try {
        const res = await fetch("http://localhost:8000/api/refresh/", {
          method: "POST",
          credentials: "include", // quan trọng: gửi cookie HttpOnly
        });

        if (!res.ok) {
          console.warn("Refresh token failed:", res.status);
          // nếu refresh thất bại → logout user
          this.logout();
        } else {
          console.log("Access token refreshed successfully");
        }
      } catch (err) {
        console.error("Error refreshing token:", err);
        this.logout();
      }
    },
  },
  mounted() {
    // Đồng bộ cookie username mỗi giây để update UI
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
      }
    }, 1000);

    // Refresh token tự động 25 phút 1 lần
    this.refreshInterval = setInterval(() => {
      this.refreshToken();
    }, 25 * 60 * 1000); // 25 phút

    // Watch route thay đổi
    this.$watch(
      () => this.$route.path,
      () => {
        this.username = this.getCookie("username") || "";
      }
    );
  },
  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
    clearInterval(this.refreshInterval);
  },
};
</script>


<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  margin: 2px;
}

/* Header flex: logo trái, auth phải */
.app-header {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 6px 0;
  margin-bottom: 15px;
}

/* Spacer đẩy auth sang phải */
.spacer {
  flex: 1;
}

/* Wrapper cho Hello + auth, lùi vào 50px */
.auth-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 42px; 
}

/* Logo */
.logo-title {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
  color: #2196f3;
}

/* Hello text giống Home.vue */
.hello-text {
  font-size: 2rem;
  font-weight: 500;
  color: #2196f3;
  font-family: "Segoe UI", sans-serif;
  margin: 0;
  flex-shrink: 0;
}

/* Auth button wrapper */
.auth-btn {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Login button */
.btn-login {
  width: 180px;
  padding: 8px 16px;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
  text-align: center;
  background: #FFA500;
  color: #fff;
}
.btn-login:hover {
  background: #d48a00;
}

/* Logout button */
.btn-logout {
  width: 180px;
  padding: 8px 16px;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
  text-align: center;
  background: #f1392c;
  color: #fff;
}
.btn-logout:hover {
  background: #d32f2f;
}


</style>
