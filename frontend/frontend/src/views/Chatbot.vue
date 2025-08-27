<template>
  <div class="chatbot-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">🌤 Viet Cloud</h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link to="/chatbot" class="nav-btn active">🤖 Chatbot</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="chat-main">
      <header class="chat-header">
        <h3>🤖 Chat with <span class="brand">Viet Cloud</span></h3>
      </header>

      <section class="chat-window">
        <div class="chat-message bot">The temperature in Da Nang is 36 °C now.</div>
        <div class="chat-message user">Tell me the temperature of Da Nang now</div>
        <div class="chat-message user">Please give me information on hotel room prices in Da Nang</div>
        <div class="chat-message bot">
          Please wait a moment, I will send you some room booking information via Booking.com, Expedia or Hotelbeds
        </div>
        <div class="chat-message bot">Thinking.....</div>
      </section>

      <!-- Suggestion quick replies -->
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
};
</script>

<!-- <style src="@/assets/common.css"></style> -->
<style src="@/assets/Chatbot.css"></style>
