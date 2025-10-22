<template>
  <div class="map-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">🌤 VietCloud</h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn active">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn">🤖 Chatbot</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="map-main">
      <!-- Thanh tìm kiếm -->
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
            />
            <span class="search-icon" @click="onClickSearch">🔍</span>

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

      <!-- 🌍 Gợi ý thành phố -->
      <section class="city-weather-list" v-if="!errorMessage">
        <h3 class="section-subtitle">🌍 Some places you may be interested in:</h3>
        <div v-for="(city, index) in cities" :key="index" class="city-weather-card">
          <img v-if="city.icon" :src="getIconSrc(city.icon)" class="weather-icon" alt="icon" />
          <div class="city-info">
            <h4>{{ city.name }}</h4>
            <p class="time">{{ city.time }}</p>
          </div>
          <div class="temp">
            {{ city.temp !== null ? Math.round(city.temp) + '°C' : '—' }}
          </div>
        </div>
      </section>

      <!-- 🗺️ Bản đồ chính -->
      <section class="map-box" v-if="!errorMessage">
        <div id="leaflet-map" class="leaflet-map"></div>

        <!-- ⚙️ Control Panel -->
        <div class="overlay-panel">
          <h4>Weather Layers</h4>
          <label><input type="radio" name="weatherLayer" value="clouds" v-model="activeLayer" @change="toggleLayer" /> ☁️ Clouds</label>
          <label><input type="radio" name="weatherLayer" value="temp" v-model="activeLayer" @change="toggleLayer" /> 🌡️ Temperature</label>
          <label><input type="radio" name="weatherLayer" value="wind" v-model="activeLayer" @change="toggleLayer" /> 💨 Wind Speed</label>

          <!-- 🕒 Time-lapse toggle -->
          <div class="timelapse-toggle">
            <button @click="toggleTimelapse">
              {{ isPlaying ? "⏸️ Stop Time-lapse" : "▶️ Play Time-lapse" }}
            </button>
          </div>

          <!-- 🧭 Legend -->
          <div v-if="activeLayer" class="legend-box">
            <h5>Color Legend</h5>
            <img v-if="activeLayer === 'temp'" src="https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/temp_c_scale.png" alt="Temp legend"/>
            <img v-if="activeLayer === 'wind'" src="https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/wind_speed_scale.png" alt="Wind legend"/>
            <img v-if="activeLayer === 'clouds'" src="https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/widgets/clouds_scale.png" alt="Cloud legend"/>
          </div>
        </div>
      </section>

      <!-- ⚠️ Component lỗi -->
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
import L from "leaflet";

export default {
  name: "Map",
  components: { WeatherError },
  data() {
    return {
      username: this.getCookie("username") || "",
      searchQuery: "",
      suggestions: [],
      showSuggestions: false,
      map: null,
      baseLayer: null,
      activeLayer: null,
      layerRefs: { clouds: null, temp: null, wind: null },
      errorMessage: "",
      errorGif: "",
      isPlaying: false,
      timelapseTimer: null,
      timelapseTimestamps: [],
      currentIndex: 0,
      cities: [
        { name: "—", temp: null, icon: null, time: "--:--" },
        { name: "—", temp: null, icon: null, time: "--:--" },
        { name: "—", temp: null, icon: null, time: "--:--" },
      ],
    };
  },

  async mounted() {
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) this.username = cookieUsername;
    }, 1000);

    const randomCities = this.getRandomCities();
    for (let i = 0; i < 3; i++) this.cities[i].name = randomCities[i];
    for (const city of randomCities) await this.fetchCityWeather(city);

    this.initLeafletMap();
    this.prepareTimestamps();
  },

  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
    if (this.timelapseTimer) clearInterval(this.timelapseTimer);
    if (this.map) {
      this.map.off();
      this.map.remove();
    }
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

    async fetchCityWeather(city) {
      if (!city) return;
      try {
        const res = await fetch(`http://localhost:8000/api/weather/?city=${encodeURIComponent(city)}`);
        const data = await res.json();
        if (res.ok && data) {
          const now = new Date();
          const icon = data.icon || "01d";
          const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          const idx = this.cities.findIndex((c) => c.name === "—" || c.name === city);
          if (idx !== -1) {
            this.cities[idx] = { name: data.location, temp: Math.round(data.temperature), icon, time: timeStr };
          }
        }
      } catch (err) {
        console.error("Error fetching weather:", err);
      }
    },

    getRandomCities() {
      const all = ["Hanoi", "Ho Chi Minh", "Da Nang", "Hue", "Nha Trang", "Hai Phong", "Can Tho", "Phu Quoc", "Da Lat"];
      return all.sort(() => 0.5 - Math.random()).slice(0, 3);
    },

    async initLeafletMap() {
      this.map = L.map("leaflet-map").setView([21.0285, 105.8542], 8);
      this.baseLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(this.map);

      // ✅ Giữ lại popup mặc định
      L.popup({ closeButton: false, autoClose: false, closeOnClick: false, className: "custom-popup" })
        .setLatLng([21.0285, 105.8542])
        .setContent("<b>Hà Nội</b><br>Default Center")
        .openOn(this.map);
    },

    // 🕒 Frame skip: mỗi frame cách nhau 3 tiếng (10800s)
    prepareTimestamps() {
      const now = Math.floor(Date.now() / 1000);
      const arr = [];
      for (let i = 0; i < 8; i++) arr.push(now + i * 3 * 3600);
      this.timelapseTimestamps = arr;
      this.currentIndex = 0;
    },

    async toggleLayer() {
      if (!this.activeLayer || !this.map) return;

      try {
        const timestamp = this.timelapseTimestamps[this.currentIndex] || Math.floor(Date.now() / 1000);
        const tileUrl = `http://localhost:8000/api/map/tile/?layer=${this.activeLayer}&z={z}&x={x}&y={y}&timestamp=${timestamp}`;

        Object.values(this.layerRefs).forEach((layer) => {
          if (layer && this.map.hasLayer(layer)) this.map.removeLayer(layer);
        });

        const newLayer = L.tileLayer(tileUrl, {
          opacity: 0.6,
          tileSize: 256,
          zIndex: 10,
        }).addTo(this.map);

        this.layerRefs[this.activeLayer] = newLayer;
      } catch (err) {
        console.error("Error loading layer:", err);
      }
    },

    toggleTimelapse() {
      if (this.isPlaying) {
        clearInterval(this.timelapseTimer);
        this.isPlaying = false;
      } else {
        this.isPlaying = true;
        this.currentIndex = 0;
        this.toggleLayer();
        // ⏱️ Frame interval 5s
        this.timelapseTimer = setInterval(() => {
          this.currentIndex++;
          if (this.currentIndex >= this.timelapseTimestamps.length) {
            clearInterval(this.timelapseTimer);
            this.isPlaying = false;
            return;
          }
          this.toggleLayer();
        }, 5000);
      }
    },

    async onSearchInput() {
      const q = this.searchQuery.trim();
      if (!q) {
        this.suggestions = [];
        this.showSuggestions = false;
        return;
      }
      const res = await fetch(`http://localhost:8000/api/autocomplete/?q=${encodeURIComponent(q)}`);
      const arr = await res.json();
      this.suggestions = Array.isArray(arr) ? arr : [];
      this.showSuggestions = this.suggestions.length > 0;
    },

    selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;
      if (this.map) this.map.setView([s.lat, s.lon], 8);
    },

    onEnterSearch() {
      if (this.suggestions.length > 0) this.selectSuggestion(this.suggestions[0]);
    },

    onClickSearch() {
      this.onEnterSearch();
    },
  },
};
</script>

<style scoped src="@/assets/Map.css"></style>
