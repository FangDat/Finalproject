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
            <img :src="getIconSrc(item.icon, item.time)" class="forecast-icon" />
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
        <img :src="getDayIcon(day.icon)" class="forecast-icon" />
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
    // Icon phân biệt ngày/đêm (dùng cho hiện tại + today forecast)
    getIconSrc(iconName, timeStr = null) {
      let hour = null;
      if (timeStr) {
        try {
          hour = parseInt(timeStr.split(":")[0], 10);
        } catch {
          hour = null;
        }
      } else {
        hour = new Date().getHours();
      }

      const isNight = hour !== null && (hour >= 18 || hour < 7);

      if (iconName.includes("cloud")) {
        return isNight
          ? require("@/assets/moonandclouds.png")
          : require("@/assets/clouds.png");
      }
      if (iconName.includes("clear")) {
        return isNight
          ? require("@/assets/moon.png")
          : require("@/assets/clear.png");
      }
      if (iconName.includes("rain")) {
        return require("@/assets/rain.png");
      }

      try {
        return require(`@/assets/${iconName}.png`);
      } catch {
        return require("@/assets/clouds.png");
      }
    },

    // Icon mặc định ban ngày (cho 3-day forecast)
    getDayIcon(iconName) {
      if (iconName.includes("cloud")) {
        return require("@/assets/clouds.png");
      }
      if (iconName.includes("clear")) {
        return require("@/assets/clear.png");
      }
      if (iconName.includes("rain")) {
        return require("@/assets/rain.png");
      }

      try {
        return require(`@/assets/${iconName}.png`);
      } catch {
        return require("@/assets/clouds.png");
      }
    },

    async fetchWeather() {
      try {
        const response = await fetch("http://localhost:8000/api/weather/");
        const data = await response.json();

        if (response.ok) {
          this.city = data.location;
          this.temperature = data.temperature;
          this.realFeel = data.temperature;
          this.wind = data.wind_speed;
          this.chanceOfRain =
            data.chance_of_rain !== undefined
              ? data.chance_of_rain + "%"
              : "0%";
          this.condition = data.condition;

          // Giờ local từ upcoming_hours
          let localHour = null;
          if (data.upcoming_hours && data.upcoming_hours.length > 0) {
            localHour = parseInt(
              data.upcoming_hours[0].time.split(" ")[1].split(":")[0],
              10
            );
          }

          // Icon hiện tại (có phân biệt ngày/đêm)
          this.weatherIcon = this.getIconSrc(
            data.condition.toLowerCase(),
            localHour !== null ? localHour + ":00" : null
          );

          // Forecast hôm nay
          this.forecastToday = data.upcoming_hours.map((item) => ({
            time: item.time.split(" ")[1].slice(0, 5),
            temp: item.temp,
            icon: item.condition.toLowerCase(),
          }));

          // Forecast 3 ngày (icon ban ngày mặc định)
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
