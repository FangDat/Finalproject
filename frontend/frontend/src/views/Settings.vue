<template>
  <div class="settings-container">
    <!-- Mobile: Toggle sidebar button -->
      <button
        class="sidebar-toggle"
        @click="toggleSidebar"
      >
        ☰
      </button>

      <!-- Mobile overlay -->
      <div
        v-if="showSidebar"
        class="sidebar-overlay"
        @click="closeSidebar"
      ></div>
    <!-- Sidebar trái -->
    <aside class="sidebar-left" :class="{ open: showSidebar }">
      <h2 class="logo">
        <router-link to="/">🌤 VietCloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link
          to="/"
          exact
          class="nav-btn"
          @click.native="closeSidebar"
        >
          ☁️ Weather
        </router-link>
        <router-link to="/map" class="nav-btn" @click.native="closeSidebar">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn" @click.native="closeSidebar">🤖 Chatbot</router-link>
        <router-link to="/settings" class="nav-btn" @click.native="closeSidebar">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn" @click.native="closeSidebar">👤 Profile</router-link>
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
            :class="{ active: windSpeed === 'm/s' }"
            @click="windSpeed = 'm/s'"
          >
            m/s
          </button>
          <button
            class="settings-unit-btn"
            :class="{ active: windSpeed === 'Mph' }"
            @click="windSpeed = 'Mph'"
          >
            Mph
          </button>


          <p><strong>VISIBILITY</strong></p>
          <button
            class="settings-unit-btn"
            :class="{ active: Visibility === 'Kilometers' }"
            @click="Visibility = 'Kilometers'"
          >
            Kilometers
          </button>
          <button
            class="settings-unit-btn"
            :class="{ active: Visibility === 'Miles' }"
            @click="Visibility = 'Miles'"
          >
            Miles
          </button>
        </div>
      </section>

      <!-- Nút Done -->
      <div class="settings-done-box">
        <button class="settings-done-btn" @click="saveSettings">Done</button>
      </div>
    </main>

    <!-- Sidebar phải -->
    <aside
      class="settings-sidebar-right"
      v-if="!username || (username && !is_premium)"
    >
      <h3 class="settings-section-title">Advanced</h3>

      <div class="premium-features">
        <h4><strong>Try now to experience exclusive features</strong></h4>
        <ul class="premium-list">
          <li><strong>AI Weather Chatbot</strong> Ask natural questions and get smart, real-time weather insights.</li>
          <li><strong>7-Day Forecast</strong> Access detailed forecasts to plan trips, work, and outdoor activities.</li>
          <li><strong>Search History</strong> Review and track your previously searched locations anytime.</li>
        </ul>
      </div>


      <div class="settings-pricing-box">
        <p><strong>Register now VietCloud with attractive price</strong></p>
        <p>$6.96 / month</p>

        <!-- 🔹 Chưa login → Sign up -->
        <router-link
          v-if="!username"
          to="/signup"
          class="settings-btn-signup"
        >
          Sign up
        </router-link>

        <!-- 🔹 Đã login nhưng chưa premium → Upgrade -->
        <router-link
          v-else-if="username && !is_premium"
          to="/billing"
          class="settings-btn-signup"
        >
          Upgrade
        </router-link>
      </div>
    </aside>

    <!-- Popup thông báo -->
    <div v-if="showPopup" class="settings-popup">
      ✅ Settings saved successfully! Automatically return to Home page.
    </div>
  </div>
</template>

<script>
import apiClient from "@/services/apiClient";
export default {
  name: "Settings",
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
      showSidebar: false,
      temperature: "Celsius",
      windSpeed: "m/s", 
      Visibility: "Kilometers",
      notifications: false,
      generalLocation: false,
      showPopup: false,
    };
  },
  methods: {
    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    },
    async fetchUserInfo() {
      try {
        const res = await apiClient.get("/api/user-info/");
        const data = res.data;

        this.username = data.username || "";
        this.is_premium = data.is_premium || false;
      } catch (e) {
        this.username = "";
        this.is_premium = false;
      }
    },
  
      toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },
    closeSidebar() {
      this.showSidebar = false;
    },

    saveSettings() {
      // lưu settings
      const settings = {
        temperature: this.temperature,
        windSpeed: this.windSpeed,
        Visibility: this.Visibility,
        notifications: this.notifications,
        generalLocation: this.generalLocation,
      };
      localStorage.setItem("vietcloud_settings", JSON.stringify(settings));

      // hiện popup
      this.showPopup = true;

      // sau 3 giây chuyển về Home + refresh
      setTimeout(() => {
        this.showPopup = false;
        window.location.href = "/"; // điều hướng về Home + reload cứng trang
      }, 3000);
    },
    loadSettings() {
      const saved = localStorage.getItem("vietcloud_settings");
      if (saved) {
        const parsed = JSON.parse(saved);
        this.temperature = parsed.temperature || this.temperature;
        this.windSpeed = parsed.windSpeed || this.windSpeed;
        this.Visibility = parsed.Visibility || this.Visibility;
        this.notifications = parsed.notifications ?? this.notifications;
        this.generalLocation = parsed.generalLocation ?? this.generalLocation;
      }
    },
  },
  watch: {
    $route() {
      this.showSidebar = false;
    }
  },
  mounted() {
    this.loadSettings();
    this.fetchUserInfo(); // ⚡ lấy thông tin user khi mount
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
        this.fetchUserInfo(); // cập nhật is_premium
      }
    }, 1000);
  },
  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped src="@/assets/Settings.css"></style>
