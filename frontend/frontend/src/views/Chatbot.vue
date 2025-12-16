<template>
  <div class="chatbot-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 VietCloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn router-link-active">
          🤖 Chatbot
        </router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main v-if="username" class="chat-main">
      <header class="chat-header">
        <h3>🤖 Chat with <span class="brand">VietCloud</span></h3>
      </header>

      <!-- CHAT CONTENT -->
      <section class="chat-window">
        <div class="chat-message user">Tell me the temperature of Da Nang now</div>
        <div class="chat-message bot">The temperature in Da Nang is 36 °C now.</div>
        <div class="chat-message user">
          Please give me information on hotel room prices in Da Nang
        </div>
        <div class="chat-message bot">
          Please wait a moment, I will send you some room booking information via Booking.com,
          Expedia or Hotelbeds
        </div>
        <div class="chat-message bot">Thinking.....</div>
      </section>

      <!-- Suggestions -->
      <section class="chat-suggestions">
        <button class="suggest-btn">
          Suggested summer travel destinations in Asia
        </button>
        <button class="suggest-btn">
          Hotel room prices in Da Lat city
        </button>
        <button class="suggest-btn">
          Is the weather next week suitable for going to the beach in Da Nang?
        </button>
      </section>

      <!-- Input -->
      <footer class="chat-input-area">
        <input
          type="text"
          placeholder="Enter your message..."
          class="chat-input"
          :disabled="!is_premium"
        />
        <button class="btn-send" :disabled="!is_premium">➤</button>
      </footer>

      <!-- 🔒 PREMIUM OVERLAY -->
      <div v-if="!is_premium" class="premium-overlay">
        <div class="overlay-content">
          <h2>🔒 Premium Feature</h2>
          <p>
            The AI Chatbot is available for <strong>VietCloud Premium</strong> users only.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: "Chatbot",
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
    };
  },
  methods: {
    // 🔐 Helper đọc cookie
    getCookie(name) {
      const match = document.cookie.match(
        new RegExp("(^| )" + name + "=([^;]+)")
      );
      return match ? decodeURIComponent(match[2]) : null;
    },

    // ✅ Giống Home.vue
    async fetchUserInfo() {
      try {
        const res = await fetch("http://localhost:8000/api/user-info/", {
          method: "GET",
          credentials: "include",
        });
        if (!res.ok) throw new Error("Not logged in");

        const data = await res.json();
        this.username = data.username || "";
        this.is_premium = data.is_premium || false;
      } catch (err) {
        this.username = "";
        this.is_premium = false;
      }
    },
  },
  mounted() {
    this.fetchUserInfo();

    // 🔄 Sync cookie changes (login / logout)
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
        this.fetchUserInfo();
      }
    }, 1000);
  },
  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped src="@/assets/Chatbot.css"></style>
