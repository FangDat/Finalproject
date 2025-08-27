<template>
  <div class="home-container">
  <!-- Sidebar trái -->
  <aside class="sidebar-left">
    <h2 class="logo">🌤 Viet Cloud</h2>
    <nav class="nav-menu">
      <button class="nav-btn active">☁️ Weather</button>
      <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
      <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
    </nav>
  </aside>


    <!-- Nội dung chính -->
    <main class="main-content">
      <!-- Thanh trên cùng -->
      <header class="top-bar">
        <input type="text" placeholder="Search city..." class="search-bar" />
        <router-link to="/login" class="btn-login">Login</router-link>
      </header>

      <!-- Thông tin thời tiết -->
      <section class="weather-main card">
        <div>
          <h1 class="city">{{ city }}</h1>
          <p class="rain">Chance of rain: {{ chanceOfRain }}</p>
          <h2 class="temperature">{{ temperature }}°C</h2>
        </div>
        <div class="weather-icon">☀️</div>
      </section>

      <!-- Dự báo trong ngày -->
      <section class="card">
        <h3 class="section-title">Today's Forecast</h3>
        <div class="forecast-today">
          <div
            v-for="(item, index) in forecastToday"
            :key="index"
            class="forecast-item"
          >
            <p>{{ item.time }}</p>
            <div class="forecast-icon">{{ item.icon }}</div>
            <p>{{ item.temp }}°C</p>
          </div>
        </div>
      </section>

      <!-- Điều kiện không khí -->
      <section class="card">
        <h3 class="section-title">Air Condition</h3>
        <div class="air-grid">
          <div>🌡️ Real feel: {{ realFeel }}°C</div>
          <div>💨 Wind: {{ wind }} km/h</div>
          <div>👁️ Visibility: {{ visibility }} km</div>
          <div>🌞 UV index: {{ uvIndex }}</div>
          <div>💧 Chance of rain: {{ chanceOfRain }}</div>
        </div>
      </section>
    </main>

    <!-- Sidebar phải -->
    <aside class="sidebar-right">
      <h3 class="section-title">3-Day Forecast</h3>
      <div
        v-for="(day, index) in forecast3days"
        :key="index"
        class="forecast-3day"
      >
        <div>{{ day.day }}</div>
        <div class="forecast-icon">{{ day.icon }}</div>
        <div>{{ day.temp }}</div>
      </div>
      <p class="premium-text">
        Want forecast for 7 days? → Sign up for VietCloud premium now!
      </p>
      <router-link to="/signup" class="btn-signup">Sign up</router-link>
    </aside>
  </div>
</template>

<script>


export default {
  name: "Home",
  data() {
    return {
      city: "Da Nang",
      temperature: 36,
      chanceOfRain: "0%",
      realFeel: 36,
      wind: 0.2,
      visibility: 11,
      uvIndex: 2,
      forecastToday: [
        { time: "6:00", icon: "☁️", temp: 18 },
        { time: "9:00", icon: "🌧️", temp: 17 },
        { time: "12:00", icon: "⛅", temp: 20 },
        { time: "15:00", icon: "☀️", temp: 36 },
        { time: "18:00", icon: "☁️", temp: 26 },
      ],
      forecast3days: [
        { day: "Today", icon: "☀️", temp: "36/22" },
        { day: "Tue", icon: "☀️", temp: "37/22" },
        { day: "Wed", icon: "🌧️", temp: "22/17" },
      ],
    };
  },
};
</script>

<!-- <style src="@/assets/common.css"></style> -->
<style src="@/assets/Home.css"></style>
