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
          <h2 class="temperature">{{ Math.round(temperature) }}°C</h2>
        </div>
        <div class="weather-icon">
          <img :src="weatherIcon" alt="Weather Icon" />
        </div>
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
            <img :src="getIconSrc(item.icon)" class="forecast-icon" />
            <p>{{ Math.round(item.temp) }}°C</p>
          </div>
        </div>
      </section>

      <!-- Điều kiện không khí -->
      <section class="card">
        <h3 class="section-title">Air Condition</h3>
        <div class="air-grid">
          <div>🌡️ Real feel: {{ Math.round(realFeel) }}°C</div>
          <div>💨 Wind: {{ Math.round(wind) }} km/h</div>
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
        <img :src="getIconSrc(day.icon)" class="forecast-icon" />
        <div>{{ day.temp.split('/').map(t => Math.round(t)).join('/') }}</div>
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
      temperature: null,
      chanceOfRain: "0%",
      realFeel: null,
      wind: null,
      visibility: 11,
      uvIndex: 2,
      condition: "",
      weatherIcon: require("@/assets/clear.png"),
      forecastToday: [],
      forecast3days: [],
    };
  },
  methods: {
    getIconSrc(iconName) {
      try {
        return require(`@/assets/${iconName.toLowerCase()}.png`);
      } catch {
        return require("@/assets/clouds.png"); // default icon
      }
    },
    async fetchWeather() {
      try {
        const response = await fetch("http://localhost:8000/api/weather/");
        const data = await response.json();

        if (response.ok) {
          // Thông tin hiện tại
          this.city = data.location;
          this.temperature = data.temperature;
          this.realFeel = data.temperature;
          this.wind = data.wind_speed;
          this.chanceOfRain =
            data.chance_of_rain !== undefined
              ? data.chance_of_rain + "%"
              : "0%";
          this.condition = data.condition;
          this.weatherIcon = this.getIconSrc(
            data.condition.split(" ")[0].toLowerCase()
          );

          // Today's forecast: 5 mốc giờ tiếp theo từ API
          this.forecastToday = data.upcoming_hours.map((item) => ({
            time: item.time.split(" ")[1].slice(0, 5), // HH:MM
            temp: item.temp,
            icon: item.condition.toLowerCase(),
          }));

          // 3-day forecast
          this.forecast3days = data.daily_forecast.map((item) => ({
            day: item.day,
            temp: item.temp,
            icon: item.condition.toLowerCase(),
          }));
        } else {
          console.error("Lỗi fetch weather:", data);
        }
      } catch (err) {
        console.error("Không thể lấy dữ liệu thời tiết:", err);
      }
    },
  },
  mounted() {
    this.fetchWeather();
  },
};
</script>

<style src="@/assets/Home.css"></style>
