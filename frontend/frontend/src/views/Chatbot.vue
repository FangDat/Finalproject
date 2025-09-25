<template>
  <div class="chatbot-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 Viet Cloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn router-link-active">🤖 Chatbot</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main v-if="username" class="chat-main">
      <header class="chat-header">
        <h3>🤖 Chat with <span class="brand">Viet Cloud</span></h3>
      </header>

      <section class="chat-window">
        <div class="chat-message user">Tell me the temperature of Da Nang now</div>
        <div class="chat-message bot">The temperature in Da Nang is 36 °C now.</div>
        <div class="chat-message user">Please give me information on hotel room prices in Da Nang</div>
        <div class="chat-message bot">
          Please wait a moment, I will send you some room booking information via Booking.com, Expedia or Hotelbeds
        </div>
        <div class="chat-message bot">Thinking.....</div>
      </section>

      <!-- Gợi ý -->
      <section class="chat-suggestions">
        <button class="suggest-btn">Suggested summer travel destinations in Asia</button>
        <button class="suggest-btn">Hotel room prices in Da Lat city</button>
        <button class="suggest-btn">Is the weather next week suitable for going to the beach in Da Nang?</button>
      </section>

      <!-- Ô nhập -->
      <footer class="chat-input-area">
        <input type="text" placeholder="Enter your message..." class="chat-input" />
        <button class="btn-send">➤</button>
      </footer>
    </main>
  </div>
</template>

<script>
export default {
  name: "Chatbot",
  data() {
    return {
      username: this.getCookie("username") || "",
    };
  },
  methods: {
    // 🔐 Helper đọc cookie
    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    },

    logout() {
      // Xóa cookie
      document.cookie = "access=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = "refresh=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";

      this.username = "";
      this.$router.push("/");   // quay về Home
      window.location.reload(); // refresh để về trạng thái chưa login
    },
  },
  mounted() {
    // Theo dõi thay đổi cookie để update username
    this.checkCookieInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
      }
    }, 1000);
  },
  beforeUnmount() {
    clearInterval(this.checkCookieInterval);
  },
};
</script>

<style scoped src="@/assets/Chatbot.css"></style>
