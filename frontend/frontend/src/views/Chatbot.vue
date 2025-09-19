<template>
  <div class="chatbot-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">🌤 Viet Cloud</h2>
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
        <button class="btn-logout" @click="logout">Logout</button>
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
      username: localStorage.getItem("username") || "",
    };
  },
  methods: {
    logout() {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("username");
      this.username = "";
      this.$router.push("/");   // quay về Home
      window.location.reload(); // refresh để về trạng thái chưa login
    },
  },
  mounted() {
    // Theo dõi thay đổi localStorage để update username
    window.addEventListener("storage", () => {
      this.username = localStorage.getItem("username") || "";
    });
  },
};
</script>

<style scoped src="@/assets/Chatbot.css"></style>
