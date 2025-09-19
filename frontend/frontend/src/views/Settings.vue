<template>
  <div class="settings-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 Viet Cloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
       <router-link v-if="username" to="/chatbot" class="nav-btn">🤖 Chatbot</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
      </nav>
    </aside>


    <!-- Nội dung chính -->
    <main class="settings-main">
      <!-- Units -->
      <section class="settings-card">
        <h3 class="settings-section-title">Units</h3>
        <div class="settings-unit-group">
          <p><strong>TEMPERATURE</strong></p>
          <button
            class="settings-unit-btn"
            :class="{ active: temperature === 'Celsius' }"
            @click="temperature = 'Celsius'"
          >
            Celsius
          </button>
          <button
            class="settings-unit-btn"
            :class="{ active: temperature === 'Fahrenheit' }"
            @click="temperature = 'Fahrenheit'"
          >
            Fahrenheit
          </button>

          <p><strong>WIND SPEED</strong></p>
          <button
            class="settings-unit-btn"
            :class="{ active: windSpeed === 'Km/h' }"
            @click="windSpeed = 'Km/h'"
          >
            Km/h
          </button>
          <button
            class="settings-unit-btn"
            :class="{ active: windSpeed === 'Mph' }"
            @click="windSpeed = 'Mph'"
          >
            Mph
          </button>

          <p><strong>DISTANCE</strong></p>
          <button
            class="settings-unit-btn"
            :class="{ active: distance === 'Kilometers' }"
            @click="distance = 'Kilometers'"
          >
            Kilometers
          </button>
          <button
            class="settings-unit-btn"
            :class="{ active: distance === 'Miles' }"
            @click="distance = 'Miles'"
          >
            Miles
          </button>
        </div>
      </section>

      <!-- Notifications -->
      <section class="settings-card">
        <h3 class="settings-section-title">Notifications</h3>
        <div class="settings-toggle-item" @click="notifications = !notifications">
          <span>Be aware of the weather</span>
          <span class="settings-check" v-if="notifications">✔</span>
        </div>
      </section>

      <!-- General -->
      <section class="settings-card">
        <h3 class="settings-section-title">General</h3>
        <div class="settings-toggle-item" @click="generalLocation = !generalLocation">
          <span>Get weather of your location</span>
          <span class="settings-check" v-if="generalLocation">✔</span>
        </div>
      </section>
    </main>

    <!-- Sidebar phải -->
    <aside class="settings-sidebar-right">
      <h3 class="settings-section-title">Advanced</h3>
      <h4><strong>Try now to experience exclusive features</strong></h4>
      <p>* Chat bot<br />* 7 days Forecast<br />* Search History</p>
      <div class="settings-pricing-box">
        <p><strong>Register now VietCloud with attractive price</strong></p>
        <p>$6.96 / month</p>
        <!-- Nút signup chỉ hiện nếu chưa login -->
        <router-link v-if="!username" to="/signup" class="settings-btn-signup">Sign up</router-link>
      </div>
    </aside>
  </div>
</template>

<script>
export default {
  name: "Settings",
  data() {
    return {
      username: localStorage.getItem("username") || "",
      temperature: "Celsius",
      windSpeed: "Km/h",
      distance: "Kilometers",
      notifications: false,
      generalLocation: false,
    };
  },
  mounted() {
    // Cập nhật username khi localStorage thay đổi (ví dụ khi login/logout)
    window.addEventListener("storage", () => {
      this.username = localStorage.getItem("username") || "";
    });
  },
};
</script>

<style scoped src="@/assets/Settings.css"></style>
