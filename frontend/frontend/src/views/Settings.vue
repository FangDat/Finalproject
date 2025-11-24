<template>
  <div class="settings-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 VietCloud</router-link>
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

      <!-- Nút Done -->
      <div class="settings-done-box">
        <button class="settings-done-btn" @click="saveSettings">Done</button>
      </div>
    </main>

    <!-- Sidebar phải -->
    <!-- <aside class="settings-sidebar-right" v-if="!username"> -->
    <aside class="settings-sidebar-right" v-if="!username || (username && !is_premium)">
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

    <!-- Popup thông báo -->
    <div v-if="showPopup" class="settings-popup">
      ✅ Settings saved successfully! Automatically return to Home page.
    </div>
  </div>
</template>

<script>
export default {
  name: "Settings",
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
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
        fetchUserInfo() {
      // ⚡ Gọi backend API để lấy username + is_premium
      fetch("http://localhost:8000/api/user-info/", {
        credentials: "include", // quan trọng để gửi cookie
      })
        .then(res => {
          if (!res.ok) throw new Error("Not logged in");
          return res.json();
        })
        .then(data => {
          this.username = data.username || "";
          this.is_premium = data.is_premium || false;
        })
        .catch(() => {
          this.username = "";
          this.is_premium = false;
        });
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
