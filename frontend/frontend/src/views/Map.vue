<template>
  <div class="map-container">
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
    <main class="map-main">
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
        </div>
      </header>

      <!-- Danh sách city weather -->
      <section class="city-weather-list" v-if="!errorMessage">
          <h3 class="section-subtitle">🌍 Some places you may be interested in:</h3>

        <div v-for="(city, index) in cities" :key="index" class="city-weather-card">
          <img
            v-if="city.icon"
            :src="getIconSrc(city.icon)"
            class="weather-icon"
            alt="icon"
          />
          <div class="city-info">
            <h4>{{ city.name }}</h4>
            <p class="time">{{ city.time }}</p>
          </div>
          <div class="temp">
            {{ city.temp !== null ? Math.round(city.temp) + '°C' : '—' }}
          </div>
        </div>
      </section>

      <!-- Khung bản đồ -->
      <section class="map-box" v-if="!errorMessage">
        <p>🗺️ Map area</p>
      </section>

      <!-- Component lỗi -->
      <WeatherError
        v-if="errorMessage"
        :message="errorMessage"
        :gif="errorGif"
        @close="errorMessage = ''"
      />
    </main>
  </div>
</template>

<script>
import WeatherError from "@/components/WeatherError.vue";

export default {
  name: "Map",
  components: { WeatherError },
  data() {
    return {
      username: this.getCookie("username") || "",
      searchQuery: "",
      suggestions: [],
      showSuggestions: false,
      suggestTimer: null,
      errorMessage: "",
      errorGif: "",
      // 3 thành phố, dữ liệu sẽ cập nhật khi mounted()
      cities: [
        { name: "—", temp: null, icon: null, time: "--:--" },
        { name: "—", temp: null, icon: null, time: "--:--" },
        { name: "—", temp: null, icon: null, time: "--:--" },
      ],
    };
  },
  methods: {
    getCookie(name) {
      const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
      return match ? decodeURIComponent(match[2]) : null;
    },

    getIconSrc(iconCode) {
      try {
        return require(`@/assets/${iconCode}.png`);
      } catch {
        return require("@/assets/01d.png");
      }
    },

    // === SEARCH BAR ===
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
      } catch {
        this.suggestions = [];
        this.showSuggestions = false;
      }
    },

    selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;
      this.fetchCityWeather(s.name);
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
      this.fetchCityWeather(this.searchQuery.trim());
      this.showSuggestions = false;
    },

    onClickSearch() {
      this.onEnterSearch();
    },

    // === WEATHER API ===
    async fetchCityWeather(city) {
      if (!city) return;
      try {
        const res = await fetch(
          `http://localhost:8000/api/weather/?city=${encodeURIComponent(city)}`
        );
        const data = await res.json();

        if (res.ok && data) {
          const now = new Date();
          const icon = data.icon || "01d";
          const timeStr = now.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          });

          const idx = this.cities.findIndex((c) => c.name === "—" || c.name === city);
          if (idx !== -1) {
            this.cities[idx] = {
              name: data.location,
              temp: Math.round(data.temperature),
              icon: icon,
              time: timeStr,
            };
          }
        }
      } catch (err) {
        console.error("Error fetching weather:", err);
      }
    },

    getRandomCities() {
      const all = ["Hanoi", "Ho Chi Minh", "Da Nang", "Hue", "Hai Phong", "Can Tho", "Nha Trang", "Vung Tau", "Phu Quoc", "Da Lat", "Quy Nhon", "Pleiku"];
      const shuffled = all.sort(() => 0.5 - Math.random());
      return shuffled.slice(0, 3);
    },
  },

  async mounted() {
    // Sync username
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
      }
    }, 1000);

    // Random 3 thành phố
    const randomCities = this.getRandomCities();

    // Cập nhật 3 card có sẵn
    for (let i = 0; i < 3; i++) {
      this.cities[i].name = randomCities[i];
    }

    // Gọi API lấy dữ liệu thật
    for (const city of randomCities) {
      await this.fetchCityWeather(city);
    }
  },

  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped src="@/assets/Map.css"></style>
