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
        <div class="search-container" style="position:relative;">
          <input
            type="text"
            v-model="searchQuery"
            @input="onSearchInput"
            @keyup.enter="onEnterSearch"
            placeholder="Search city..."
            class="search-bar"
            autocomplete="off"
          />
          <span class="search-icon" @click="onClickSearch">🔍</span>

          <!-- Suggestions dropdown -->
          <ul v-if="showSuggestions && suggestions.length" class="suggestions">
            <li
              v-for="(s, idx) in suggestions"
              :key="idx"
              @click="selectSuggestion(s)"
              class="suggestion-item"
            >
              {{ s.name }} <small v-if="!s.is_vn">· {{ s.raw }}</small>
            </li>
          </ul>
        </div>
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

      <!-- Forecast trong ngày -->
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
        <div>
          {{ day.temp.split('/').map(t => Math.round(t)).join('/') }}
        </div>
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
      searchQuery: "",
      suggestions: [],
      showSuggestions: false,
      suggestTimer: null,
      city: "Loading...",
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
    // --- Icon logic ban ngày / ban đêm ---
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
    getDayIcon(iconName) {
      if (iconName.includes("cloud")) return require("@/assets/clouds.png");
      if (iconName.includes("clear")) return require("@/assets/clear.png");
      if (iconName.includes("rain")) return require("@/assets/rain.png");
      try {
        return require(`@/assets/${iconName}.png`);
      } catch {
        return require("@/assets/clouds.png");
      }
    },

    // --- Autocomplete handling ---
    onSearchInput() {
      // debounce requests
      this.showSuggestions = false;
      if (this.suggestTimer) clearTimeout(this.suggestTimer);
      const q = this.searchQuery.trim();
      if (!q) {
        this.suggestions = [];
        return;
      }
      this.suggestTimer = setTimeout(() => {
        this.fetchSuggestions(q);
      }, 300);
    },

    async fetchSuggestions(q) {
      try {
        const res = await fetch(
          `http://localhost:8000/api/autocomplete/?q=${encodeURIComponent(q)}`
        );
        const arr = await res.json();
        if (Array.isArray(arr)) {
          this.suggestions = arr;
          this.showSuggestions = arr.length > 0;
        } else {
          this.suggestions = [];
          this.showSuggestions = false;
        }
      } catch (err) {
        console.error("Autocomplete error", err);
        this.suggestions = [];
        this.showSuggestions = false;
      }
    },

    selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;
      if (s.lat && s.lon) {
        this.getWeatherByLocation(s.lat, s.lon);
      } else {
        // fallback: search by text
        this.fetchWeather(s.name);
      }
    },

    onEnterSearch() {
      // if there is a visible suggestion and first suggestion matches exactly, use it
      if (
        this.suggestions.length > 0 &&
        this.suggestions[0].name.toLowerCase() === this.searchQuery.trim().toLowerCase()
      ) {
        this.selectSuggestion(this.suggestions[0]);
        return;
      }
      // otherwise search by text
      this.fetchWeather(this.searchQuery.trim());
      this.showSuggestions = false;
    },

    onClickSearch() {
      this.onEnterSearch();
    },

    // --- Fetch thời tiết từ backend (by city text) ---
    async fetchWeather(city = "") {
      try {
        let url = city
          ? `http://localhost:8000/api/weather/?city=${encodeURIComponent(city)}`
          : "http://localhost:8000/api/weather/";
        const response = await fetch(url);
        const data = await response.json();

        if (response.ok) {
          this.applyWeatherData(data);
        } else {
          alert(data.error || "Không lấy được dữ liệu thời tiết");
        }
      } catch (err) {
        alert("Không thể kết nối đến server");
        console.error(err);
      }
    },

    // --- Lấy thời tiết theo tọa độ ---
    getWeatherByLocation(lat, lon) {
      fetch(`http://localhost:8000/api/weather/?lat=${lat}&lon=${lon}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.error) {
            alert(data.error);
            return;
          }
          this.applyWeatherData(data);
        })
        .catch((err) => console.error("Error location weather:", err));
    },

    applyWeatherData(data) {
      this.city = data.location;
      this.temperature = data.temperature;
      this.realFeel = data.temperature;
      this.wind = data.wind_speed;
      this.chanceOfRain = data.chance_of_rain ? data.chance_of_rain + "%" : "0%";
      this.condition = data.condition;

      // icon chính
      let localHour = null;
      if (data.upcoming_hours?.length > 0) {
        localHour = parseInt(
          data.upcoming_hours[0].time.split(" ")[1].split(":")[0],
          10
        );
      }
      this.weatherIcon = this.getIconSrc(
        data.condition.toLowerCase(),
        localHour !== null ? localHour + ":00" : null
      );

      // forecast hôm nay
      this.forecastToday = (data.upcoming_hours || []).map((item) => ({
        time: item.time.split(" ")[1].slice(0, 5),
        temp: item.temp,
        icon: item.condition.toLowerCase(),
      }));

      // forecast 3 ngày
      this.forecast3days = (data.daily_forecast || []).map((item) => ({
        day: item.day,
        temp: item.temp,
        icon: item.condition.toLowerCase(),
      }));
    },
  },

  // --- Khi load trang ---
  mounted() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.getWeatherByLocation(pos.coords.latitude, pos.coords.longitude);
        },
        () => {
          this.fetchWeather(); // fallback city
        }
      );
    } else {
      this.fetchWeather();
    }
  },
};
</script>

<style src="@/assets/Home.css"></style>


