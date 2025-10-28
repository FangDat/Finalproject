<template>
  <DynamicBackground :icon-code="currentIcon">
    <div class="home-container">
      <!-- Sidebar trái -->
      <aside class="sidebar-left">
        <h2 class="logo">🌤 VietCloud</h2>
        <nav class="nav-menu">
          <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
          <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
          <router-link v-if="username" to="/chatbot" class="nav-btn">🤖 Chatbot</router-link>
          <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
          <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
        </nav>
      </aside>

      <!-- Nội dung chính -->
      <main class="main-content">
        <!-- Thanh trên cùng -->
        <header class="top-bar">
          <div class="left-header">
            <div class="search-container" style="position:relative;">
              <input
                type="text"
                v-model="searchQuery"
                @input="onSearchInput"
                @keyup.enter="onEnterSearch"
                placeholder="Search city..."
                class="search-bar"
                autocomplete_local="off"
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
          </div>
        </header>

        <!-- Nếu có lỗi thì hiển thị component lỗi -->
        <WeatherError
          v-if="errorMessage"
          :message="errorMessage"
          :gif="errorGif"
          @close="errorMessage = ''"
        />

        <!-- Thông tin thời tiết -->
        <section class="weather-main card" v-if="!errorMessage">
          <div>
            <h1 class="city">{{ city }}</h1>
            <p class="rain">Chance of rain: {{ chanceOfRain }}</p>
            <h2 class="temperature">
              {{ temperature !== null ? Math.round(formatTemp(temperature)) + tempUnitSymbol : '—' }}
            </h2>
          </div>
          <div class="weather-icon">
            <img :src="weatherIcon" alt="Weather Icon" />
          </div>
        </section>

        <!-- Forecast trong ngày -->
        <section class="card" v-if="!errorMessage">
          <h3 class="section-title">Today's Forecast</h3>
          <div class="forecast-today">
            <div
              v-for="(item, index) in forecastToday"
              :key="index"
              class="forecast-item"
            >
              <p>{{ item.time }}</p>
              <img :src="getIconSrc(item.icon)" class="forecast-icon" />
              <p>{{ Math.round(formatTemp(item.temp)) + tempUnitSymbol }}</p>
            </div>
          </div>
        </section>

        <!-- Điều kiện không khí -->
        <section class="card" v-if="!errorMessage">
          <h3 class="section-title">Air Condition</h3>
          <div class="air-grid">
            <div>🌡️ Real feel: {{ realFeel ? Math.round(formatTemp(realFeel)) + tempUnitSymbol : '—' }}</div>
            <div>🫧 Humidity: {{ humidity ? humidity + '%' : '—' }}</div>
            <div>💨 Wind: {{ wind ? Math.round(formatSpeed(wind)) + windUnitSymbol : '—' }}</div>
            <div>👁️ Visibility: {{ formatDistance(visibility) }} {{ distanceUnitSymbol }}</div>
            <div>🌞 UV index: {{ uvIndex }}</div>
            <div>💧 Chance of rain: {{ chanceOfRain }}</div>
          </div>
        </section>
      </main>

      <!-- Sidebar phải -->
      <aside class="sidebar-right" v-if="!errorMessage">
        <h3 class="section-title">3-Day Forecast</h3>
        <div
          v-for="(day, index) in forecast3days"
          :key="index"
          class="forecast-3day"
        >
          <div>{{ day.day }}</div>
          <img :src="getDayIcon(day.icon)" class="forecast-icon" />
          <div>
            {{ day.temp.split('/').map(t => Math.round(formatTemp(t))).join('/') }}{{ tempUnitSymbol }}
          </div>
        </div>
        <p v-if="!username" class="premium-text">
          Want forecast for 7 days? → Sign up for VietCloud premium now!
        </p>
        <router-link v-if="!username" to="/signup" class="btn-signup">Sign up</router-link>
      </aside>
    </div>
  </DynamicBackground>
</template>

<script>
import {
  cToF,
  msToKmh,
  msToMph,
  kmToMiles,
  mToKm,
  mToMiles
} from '@/utils.js'
import WeatherError from "@/components/WeatherError.vue";
import DynamicBackground from "@/components/DynamicBackground.vue"; 

export default {
  name: "Home",
  components: { WeatherError, DynamicBackground },
  data() {
    return {
      username: this.getCookie("username") || "",
      searchQuery: "",
      suggestions: [],
      showSuggestions: false,
      suggestTimer: null,
      city: "Loading...",
      temperature: null,
      chanceOfRain: "0%",
      realFeel: null,
      wind: null,
      visibility: null,
      uvIndex: 2,
      condition: "",
      weatherIcon: require("@/assets/01d.png"),
      forecastToday: [],
      forecast3days: [],
      humidity: null,
      uvIndex: null,
      errorMessage: "",
      errorGif: "",
      settings: {
        temperature: 'Celsius',
        windSpeed: 'Km/h',
        Visibility: 'Kilometers'
      },
      currentIcon: "01d", // ✅ thêm để điều khiển nền
    };
  },
  computed: {
    tempUnitSymbol() {
      return this.settings.temperature === 'Fahrenheit' ? '°F' : '°C'
    },
    windUnitSymbol() {
      return this.settings.windSpeed === 'Mph' ? ' mph' : ' km/h'
    },
    distanceUnitSymbol() {
      return this.settings.Visibility === 'Miles' ? ' miles' : ' km'
    }
  },
  watch: {
    condition(newVal) {
      // ✅ tự động cập nhật icon code khi API trả về icon
      if (newVal && typeof newVal === "string") {
        this.currentIcon = newVal;
      }
    },
  },
  methods: {
    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    },
    formatTemp(tempC) {
      return this.settings.temperature === 'Fahrenheit' ? cToF(tempC) : tempC
    },
    formatSpeed(speedMs) {
      return this.settings.windSpeed === 'Mph' ? msToMph(speedMs) : msToKmh(speedMs)
    },
    formatDistance(meters) {
      if (meters == null) return '—'
      return this.settings.Visibility === 'Miles'
        ? Math.round(mToMiles(meters))
        : Math.round(mToKm(meters))
    },
    getIconSrc(iconCode) {
      try {
        return require(`@/assets/${iconCode}.png`);
      } catch (e) {
        return require("@/assets/01d.png");
      }
    },
    getDayIcon(iconCode) {
      try {
        return require(`@/assets/${iconCode}.png`);
      } catch (e) {
        return require("@/assets/01d.png");
      }
    },
    onSearchInput() {
      if (this.suggestTimer) clearTimeout(this.suggestTimer);
      const q = this.searchQuery.trim();
      if (!q) {
        this.suggestions = [];
        this.showSuggestions = false;
        return;
      }
      this.suggestTimer = setTimeout(() => {
        this.fetchSuggestions(q);
      }, 100);
    },
    async fetchSuggestions(q) {
      try {
        const res = await fetch(`http://localhost:8000/api/autocomplete_local/?q=${encodeURIComponent(q)}`);
        const arr = await res.json();
        if (Array.isArray(arr)) {
          this.suggestions = arr;
          this.showSuggestions = arr.length > 0;
        } else {
          this.suggestions = [];
          this.showSuggestions = false;
        }
      } catch (err) {
        console.error("autocomplete_local error", err);
        this.suggestions = [];
        this.showSuggestions = false;
      }
    },
    selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;
      if (s.lat && s.lon) {
        this.getWeatherByLocation(s.lat, s.lon, s.name);
      } else {
        this.fetchWeather(s.name);
      }
    },
    onEnterSearch() {
      if (
        this.suggestions.length > 0 &&
        this.suggestions[0].name.toLowerCase() ===
          this.searchQuery.trim().toLowerCase()
      ) {
        this.selectSuggestion(this.suggestions[0]);
        return;
      }
      this.fetchWeather(this.searchQuery.trim());
      this.showSuggestions = false;
    },
    onClickSearch() {
      this.onEnterSearch();
    },
    async fetchWeather(city = "") {
      try {
        let url = city
          ? `http://localhost:8000/api/weather/?city=${encodeURIComponent(city)}`
          : "http://localhost:8000/api/weather/";
        const response = await fetch(url);
        const data = await response.json();
        if (response.ok) {
          this.errorMessage = "";
          this.errorGif = "";
          this.applyWeatherData(data);
          this.showSuggestions = false;
        } else {
          this.errorMessage = `Location '${city}' not found\nTry searching another location`;
          this.errorGif = "";
        }
      } catch (err) {
        this.errorMessage = `Location '${city}' not found\nTry searching another location`;
        this.errorGif = "";
        console.error(err);
      }
    },
    getWeatherByLocation(lat, lon, name = null) {
      let url = `http://localhost:8000/api/weather/?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;
      if (name) url += `&name=${encodeURIComponent(name)}`;
      fetch(url)
        .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
          if (!ok || data.error) {
            this.errorMessage = `Location '${this.searchQuery}' not found\nTry searching another location`;
            this.errorGif = "";
            return;
          }
          this.errorMessage = "";
          this.errorGif = "";
          this.applyWeatherData(data);
          this.showSuggestions = false;
        })
        .catch((err) => {
          this.errorMessage = `Location '${this.searchQuery}' not found\nTry searching another location`;
          this.errorGif = "";
          console.error("Error location weather:", err);
        });
    },
    applyWeatherData(data) {
      this.city = data.location || this.searchQuery;
      this.temperature = data.temperature;
      this.realFeel = data.temperature;
      this.wind = data.wind_speed;
      this.chanceOfRain = data.chance_of_rain ? data.chance_of_rain + "%" : "0%";
      this.condition = data.icon; // ✅ lấy icon code
      this.humidity = data.humidity;
      this.uvIndex = data.uv_index;
      this.visibility = data.visibility;
      if (data.icon) {
        this.weatherIcon = this.getIconSrc(data.icon);
        this.currentIcon = data.icon; // ✅ cập nhật luôn cho DynamicBackground
      } else {
        this.weatherIcon = require("@/assets/01d.png");
      }
      this.forecastToday = (data.upcoming_hours || []).map((item) => ({
        time: item.time.split(" ")[1].slice(0, 5),
        temp: item.temp,
        icon: item.icon
      }));
      this.forecast3days = (data.daily_forecast || []).map((item) => ({
        day: item.day,
        temp: item.temp,
        icon: item.icon
      }));
  //       if (data.location && data.lat != null && data.lon != null) {
  //       const cache = {
  //         fixed_name: data.location,
  //         lat: data.lat,
  //         lon: data.lon,
  //         timestamp: Date.now()
  //       };
  //       localStorage.setItem("vietcloud_location", JSON.stringify(cache));
  //     }
  //   },
  //     getCachedLocation() {
  //     const saved = localStorage.getItem("vietcloud_location");
  //     if (!saved) return null;

  //     const cache = JSON.parse(saved);
  //     const now = Date.now();
  //     // 5 phút = 300000 ms
  //     if (now - cache.timestamp < 300000) {
  //       return { name: cache.fixed_name, lat: cache.lat, lon: cache.lon };
  //     } else {
  //       localStorage.removeItem("vietcloud_location");
  //       return null;
  //     }
    }
  },
  

  mounted() {
    const saved = localStorage.getItem("vietcloud_settings");
    if (saved) {
      this.settings = JSON.parse(saved);
    }
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
      }
    }, 1000);
       // ✅ Kiểm tra cache vị trí thiết bị (chỉ tồn tại 5 phút)
  const cachedLoc = localStorage.getItem("vietcloud_device_location");
  if (cachedLoc) {
    const cache = JSON.parse(cachedLoc);
    const now = Date.now();

    // Nếu cache còn hạn (dưới 5 phút)
      if (now - cache.timestamp < 300000) { // 5 phút = 300 000 ms
        const { lat, lon, fixed_name } = cache;
        this.getWeatherByLocation(lat, lon, fixed_name);
        return;
      } else {
        // Hết hạn → xóa cache để lấy vị trí mới
        localStorage.removeItem("vietcloud_device_location");
      }
    }
      if (navigator.geolocation) {
  
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          // gọi API để lấy fixed_name
          const res = await fetch(
            `http://localhost:8000/api/weather/?lat=${lat}&lon=${lon}`
          );
          const data = await res.json();
          if (res.ok) {
            // lưu duy nhất 1 vị trí thiết bị
            const cache = {
              fixed_name: data.location,
              lat,
              lon,
              timestamp: Date.now()
            };
            localStorage.setItem("vietcloud_device_location", JSON.stringify(cache));
            this.applyWeatherData(data);
          } else {
            this.errorMessage = "Cannot fetch weather from your location.";
          }
        },
        () => {
          this.errorMessage = `Sorry, but we couldn't find your exact location. Please try:\n- Refresh your browser.\n- Allow your browser to access your location and try again.`;
          this.errorGif = "location-pin.gif";
        }
      );
    } else {
      this.errorMessage = `Sorry, but we couldn't find your exact location. Please try:\n- Refresh your browser.\n- Allow your browser to access your location and try again.`;
      this.errorGif = "location-pin.gif";
    }
  },
  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped src="@/assets/Home.css"></style>
