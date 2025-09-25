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
// import { testChangePassword } from "./testChangePassword";

export default {
  name: "App",
  data() {
    return {
      username: this.getCookie("username") || "",
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
    logout() {
      // Xoá cookie username/email (token HttpOnly backend tự quản lý)
      document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = "email=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      this.username = "";
      this.$router.push("/");
      window.location.reload();
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

    // Watch route thay đổi
    this.$watch(
      () => this.$route.path,
      () => {
        this.username = this.getCookie("username") || "";
      }
    );

    // 💡 Test change-password ngay khi App mount
    testChangePassword();
  },
  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  margin: 20px;
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
