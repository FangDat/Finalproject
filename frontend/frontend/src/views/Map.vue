<template>
  <div class="map-container">
    <!-- Mobile: Toggle sidebar button -->
    <button class="sidebar-toggle" @click="toggleSidebar">☰</button>

    <!-- Mobile overlay -->
    <div v-if="showSidebar" class="sidebar-overlay" @click="closeSidebar"></div>
    <!-- Sidebar trái -->
    <aside class="sidebar-left" :class="{ open: showSidebar }">
      <h2 class="logo">🌤 VietCloud</h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn" @click.native="closeSidebar"
          >☁️ Weather</router-link
        >
        <router-link
          to="/map"
          class="nav-btn active"
          @click.native="closeSidebar"
          >🗺️ Maps</router-link
        >
        <router-link
          v-if="username"
          to="/chatbot"
          class="nav-btn"
          @click.native="closeSidebar"
          >🤖 Chatbot</router-link
        >
        <router-link to="/settings" class="nav-btn" @click.native="closeSidebar"
          >⚙️ Settings</router-link
        >
        <router-link
          v-if="username"
          to="/profile"
          class="nav-btn"
          @click.native="closeSidebar"
          >👤 Profile</router-link
        >
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="map-main">
      <!-- Thanh tìm kiếm -->
      <header class="top-bar">
        <div class="left-header">
          <div
            class="search-container"
            ref="searchContainer"
            style="position: relative"
          >
            <input
              type="text"
              v-model="searchQuery"
              @input="onSearchInput"
              @focus="onFocusInput"
              @keyup.enter="onEnterSearch"
              placeholder="Search city..."
              class="search-bar"
            />
            <span class="search-icon" @click="onClickSearch">🔍</span>

            <ul
              v-if="showSuggestions && suggestions.length"
              class="suggestions"
            >
              <li
                v-for="(s, idx) in suggestions"
                :key="idx"
                @click="selectSuggestion(s)"
                class="suggestion-item"
              >
                {{ s.name }} <small v-if="!s.is_vn">· {{ s.raw }}</small>
              </li>
            </ul>
            <!-- Search History dropdown (chỉ cho premium) -->
            <ul
              v-if="is_premium && showHistory && searchHistory.length"
              class="search-dropdown"
            >
              <li
                v-for="(h, idx) in searchHistory"
                :key="h.id || idx"
                class="dropdown-item"
              >
                <div
                  @click="selectHistory(h)"
                  style="
                    flex: 1;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                  "
                >
                  {{ h.name }}
                </div>

                <!-- nút X: dùng class đã có trong Home.css (.dropdown-delete-icon) -->
                <button
                  class="dropdown-delete-icon"
                  :title="'Delete ' + h.name"
                  @click.stop="deleteHistory(h)"
                  aria-label="Delete history item"
                  style="background: none; border: none"
                >
                  x
                </button>
              </li>
            </ul>
          </div>
        </div>
      </header>

      <!-- 🌍 Gợi ý thành phố -->
      <section class="city-weather-list" v-if="!errorMessage">
        <h3 class="section-subtitle">
          🌍 Some places you may be interested in:
        </h3>
        <div
          v-for="(city, index) in cities"
          :key="index"
          class="city-weather-card"
        >
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
            <!-- dùng formatTemp và tempUnitSymbol để đổi đơn vị -->
            {{
              city.temp !== null
                ? Math.round(formatTemp(city.temp_origin ?? city.temp)) +
                  tempUnitSymbol
                : "—"
            }}
          </div>
        </div>
      </section>

      <!-- 🗺️ Bản đồ chính -->
      <section class="map-box" v-if="!errorMessage">
        <div id="leaflet-map" class="leaflet-map"></div>

        <!-- ⚙️ Control Panel -->
        <div class="overlay-panel">
          <h4>Weather Layers</h4>
          <label
            ><input
              type="radio"
              name="weatherLayer"
              value="precipitation"
              v-model="activeLayer"
              @change="toggleLayer"
            />
            🌧️ Rainfall</label
          >
          <label
            ><input
              type="radio"
              name="weatherLayer"
              value="temp"
              v-model="activeLayer"
              @change="toggleLayer"
            />
            🌡️ Temperature</label
          >
          <label
            ><input
              type="radio"
              name="weatherLayer"
              value="wind"
              v-model="activeLayer"
              @change="toggleLayer"
            />
            💨 Wind Speed</label
          >
          <h5>24-hour forecast</h5>

          <!-- 🕒 Time-lapse control -->
          <div class="timelapse-control">
            <input
              type="range"
              min="0"
              :max="timelapseTimestamps.length - 1"
              step="1"
              v-model="currentIndex"
              @input="onSliderChange"
              class="timelapse-slider"
            />
            <div class="timelapse-info">
              <button @click="toggleTimelapse" class="timelapse-btn">
                {{ isPlaying ? "⏸️" : "▶️" }}
              </button>
            </div>
          </div>

          <!-- 🧭 Legend -->
          <div v-if="activeLayer" class="legend-box">
            <img
              v-if="activeLayer === 'temp'"
              :src="require('@/assets/legend_temperature.png')"
              alt="Temperature legend"
              class="legend-img"
            />
            <img
              v-if="activeLayer === 'precipitation'"
              :src="require('@/assets/legend_rainfall.png')"
              alt="Rainfall legend"
              class="legend-img"
            />
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
import { cToF, msToKmh, msToMph, mToKm, mToMiles } from "@/utils.js";
import apiClient from "@/services/apiClient";
import { getUserInfo } from "@/services/authService";
export default {
  name: "Map",
  components: { WeatherError },
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
      searchHistory: [],
      showSidebar: false,
      showHistory: false,
      searchQuery: "",
      suggestions: [],
      showSuggestions: false,
      map: null,
      baseLayer: null,
      activeLayer: "precipitation",
      prevLayer: null,
      layerRefs: { clouds: null, temp: null, wind: null, precipitation: null },
      errorMessage: "",
      errorGif: "",
      isPlaying: false,
      animationFrame: null,
      timelapseTimestamps: [],
      currentIndex: 0,
      sliderProgress: 0,
      lastFrameTime: null,
      cities: [
        // city objects will have:
        // { name, temp (converted for display), temp_origin (raw C), icon, time }
        { name: "—", temp: null, temp_origin: null, icon: null, time: "--:--" },
        { name: "—", temp: null, temp_origin: null, icon: null, time: "--:--" },
        { name: "—", temp: null, temp_origin: null, icon: null, time: "--:--" },
      ],

      // ✅ Thêm các biến lưu lại city cuối cùng
      lastCity: "",
      lastLat: null,
      lastLon: null,

      // settings (load from localStorage)
      settings: {
        temperature: "Celsius",
        windSpeed: "Km/h",
        Visibility: "Kilometers",
      },
    };
  },

  async mounted() {
    // load settings early so fetchCityWeather shows converted values
    document.addEventListener("click", this.handleClickOutside);
    const saved = localStorage.getItem("vietcloud_settings");
    if (saved) {
      try {
        this.settings = JSON.parse(saved);
      } catch (e) {
        // ignore parse error
      }
    }

    // listen for setting changes from other tabs / settings page
    window.addEventListener("storage", this.onStorageChange);

    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) this.username = cookieUsername;
    }, 1000);

    const randomCities = this.getRandomCities();
    for (let i = 0; i < 3; i++) this.cities[i].name = randomCities[i];
    // fetch city weather AFTER we set settings
    for (const city of randomCities) await this.fetchCityWeather(city);

    await this.initLeafletMap();
    this.prepareTimestamps();
    this.toggleLayer();
    await this.restoreFromLocalStorage();
    await this.fetchUserInfo();
  },

  beforeUnmount() {
    document.removeEventListener("click", this.handleClickOutside);
    window.removeEventListener("storage", this.onStorageChange);
    clearInterval(this.cookieCheckInterval);
    cancelAnimationFrame(this.animationFrame);
    if (this.map) {
      this.map.off();
      this.map.remove();
    }
  },

  computed: {
    tempUnitSymbol() {
      return this.settings.temperature === "Fahrenheit" ? "°F" : "°C";
    },
    windUnitSymbol() {
      return this.settings.windSpeed === "Mph" ? " mph" : " km/h";
    },
    distanceUnitSymbol() {
      return this.settings.Visibility === "Miles" ? " miles" : " km";
    },
  },

  methods: {
    // storage event handler -> update settings when changed elsewhere
    onStorageChange(e) {
      if (!e) return;
      if (e.key === "vietcloud_settings") {
        try {
          const parsed = JSON.parse(e.newValue || "{}");
          this.settings = parsed;
        } catch (err) {
          // ignore
        }
      }
    },

    /* ===============================
   📱 MOBILE SIDEBAR (GIỐNG PROFILE)
================================ */
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },

    closeSidebar() {
      this.showSidebar = false;
    },

    /* ======================================================
        ⭐⭐ CLICK OUTSIDE 
       ====================================================== */
    handleClickOutside(event) {
      const container = this.$refs.searchContainer;
      if (!container) return;

      if (!container.contains(event.target)) {
        this.showSuggestions = false;
        this.showHistory = false;
      }
    },
    /* ======================================================
        ⭐⭐ FOCUS INPUT — show history nếu input rỗng
       ====================================================== */
    onFocusInput() {
      if (this.searchQuery.trim() === "" && this.is_premium) {
        this.showSuggestions = false;
        this.showHistory = true;
      }
    },

    // formatting helpers using utils.js
    formatTemp(tempC) {
      if (tempC === null || tempC === undefined || tempC === "") return tempC;
      const raw = Number(tempC);
      if (Number.isNaN(raw)) return tempC;
      return this.settings.temperature === "Fahrenheit" ? cToF(raw) : raw;
    },
    formatSpeed(speedMs) {
      if (speedMs === null || speedMs === undefined || speedMs === "")
        return speedMs;
      const raw = Number(speedMs);
      if (Number.isNaN(raw)) return speedMs;
      return this.settings.windSpeed === "Mph" ? msToMph(raw) : msToKmh(raw);
    },
    formatDistance(meters) {
      if (meters == null) return "—";
      const raw = Number(meters);
      if (Number.isNaN(raw)) return "—";
      return this.settings.Visibility === "Miles"
        ? Math.round(mToMiles(raw))
        : Math.round(mToKm(raw));
    },

    getCookie(name) {
      const match = document.cookie.match(
        new RegExp("(^| )" + name + "=([^;]+)"),
      );
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
        const res = await apiClient.get("/api/weather/", {
          params: { city },
        });
        const data = res.data;

        const now = new Date();
        const icon = data.icon || "01d";
        const timeStr = now.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });

        const idx = this.cities.findIndex(
          (c) => c.name === "—" || c.name === city,
        );

        if (idx !== -1) {
          const tempOrigin =
            data.temperature != null ? Number(data.temperature) : null;

          this.cities[idx] = {
            name: data.location,
            temp: tempOrigin,
            temp_origin: tempOrigin,
            icon,
            time: timeStr,
          };
        }
      } catch (err) {
        console.error("Error fetching weather:", err);
      }
    },

    getRandomCities() {
      const all = [
        "Hanoi",
        "Ho Chi Minh",
        "Da Nang",
        "Hue",
        "Nha Trang",
        "Hai Phong",
        "Can Tho",
        "Phu Quoc",
        "Da Lat",
      ];
      return all.sort(() => 0.5 - Math.random()).slice(0, 3);
    },

    async initLeafletMap() {
      this.map = L.map("leaflet-map").setView([21.0285, 105.8542], 6);

      // ✅ Wrapper tileLayer để debug header
      const TileLayerWrapper = (url, options = {}) => {
        const layer = L.tileLayer(url, options);
        layer.on("tileload", (event) => {
          const xhr = event.tile._xhr;
          if (xhr) {
            const xcache = xhr.getResponseHeader("X-Cache");
            if (xcache)
              console.debug(
                `Tile ${event.coords.z}/${event.coords.x}/${event.coords.y} ${xcache}`,
              );
          }
        });
        return layer;
      };

      this.baseLayer = TileLayerWrapper(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution: "&copy; OpenStreetMap contributors",
          maxZoom: 6,
        },
      ).addTo(this.map);

      // ✅ Popup mặc định
      this.popupRef = L.popup({
        closeButton: false,
        autoClose: false,
        closeOnClick: false,
        className: "custom-popup",
      })
        .setLatLng([21.0285, 105.8542])
        .setContent("<b>Hà Nội</b><br>Default Center")
        .openOn(this.map);

      this.layerRefs = {
        precipitation: null,
        temp: null,
        wind: null,
      };
    },

    prepareTimestamps() {
      const now = Math.floor(Date.now() / 1000);
      const arr = [];
      for (let i = 0; i < 8; i++) arr.push(now + i * 3 * 3600);
      this.timelapseTimestamps = arr;
      this.currentIndex = 0;
      this.sliderProgress = 0;
    },

    async toggleLayer() {
      if (this.activeLayer !== this.prevLayer) {
        this.currentIndex = 0;
        this.sliderProgress = 0;
        this.isPlaying = false;
        cancelAnimationFrame(this.animationFrame);
        this.prevLayer = this.activeLayer;
      }

      if (!this.activeLayer || !this.map) return;

      try {
        const timestamp =
          this.timelapseTimestamps[this.currentIndex] ||
          Math.floor(Date.now() / 1000);

        // Remove previous layers
        Object.values(this.layerRefs).forEach((layer) => {
          if (layer && this.map.hasLayer(layer)) this.map.removeLayer(layer);
        });

        const tileUrl = `${apiClient.defaults.baseURL}/api/map/tile/?layer=${this.activeLayer}&z={z}&x={x}&y={y}&timestamp=${timestamp}`;

        const tileLayer = L.tileLayer(tileUrl, {
          opacity: 0.6,
          tileSize: 256,
          zIndex: 10,
          updateWhenIdle: true,
          keepBuffer: 2,
          detectRetina: true,
          crossOrigin: true,
        });

        this.layerRefs[this.activeLayer] = tileLayer;
        tileLayer.addTo(this.map);

        if (this.lastCity && this.lastLat !== null && this.lastLon !== null) {
          await this.updatePopup(this.lastCity, this.lastLat, this.lastLon);
        }
      } catch (err) {
        console.error("Error loading layer:", err);
      }
    },

    toggleTimelapse() {
      if (this.isPlaying) {
        this.isPlaying = false;
        cancelAnimationFrame(this.animationFrame);
      } else {
        this.isPlaying = true;
        this.lastFrameTime = performance.now();
        this.runAnimation();
      }
    },

    runAnimation() {
      if (!this.isPlaying) return;
      const now = performance.now();
      const delta = now - this.lastFrameTime;
      this.lastFrameTime = now;
      const durationPerFrame = 2000;
      this.sliderProgress += delta / durationPerFrame;

      if (this.sliderProgress >= 1) {
        this.sliderProgress = 0;
        this.currentIndex++;
        if (this.currentIndex >= this.timelapseTimestamps.length) {
          this.isPlaying = false;
          cancelAnimationFrame(this.animationFrame);
          this.currentIndex = this.timelapseTimestamps.length - 1;
          return;
        }
        this.toggleLayer();
      }
      this.animationFrame = requestAnimationFrame(this.runAnimation);
    },

    onSliderChange() {
      this.sliderProgress = 0;
      if (!this.isPlaying) this.toggleLayer();
    },

    /* ======================================================
        ⭐⭐ INPUT SEARCH — toggle giữa suggestions / history
       ====================================================== */
    onSearchInput() {
      if (this.suggestTimer) clearTimeout(this.suggestTimer);

      const q = this.searchQuery.trim();
      if (!q) {
        this.showSuggestions = false;
        if (this.is_premium) this.showHistory = true;
        return;
      }

      this.showHistory = false;

      this.suggestTimer = setTimeout(() => {
        this.fetchSuggestions(q);
      }, 120);
    },

    /* ======================================================
        ⭐⭐ FETCH USER INFO + HISTORY
       ====================================================== */
    async fetchUserInfo() {
      try {
        const data = await getUserInfo();

        this.username = data.username || "";
        this.is_premium = !!data.is_premium;

        if (this.is_premium) {
          await this.fetchSearchHistory();
        }
      } catch (err) {
        // 401 / 403 sẽ bị interceptor forceLogout
        this.username = "";
        this.is_premium = false;
        this.searchHistory = [];
      }
    },
    /* ======================================================
        ⭐⭐ FETCH SEARCH HISTORY (Home.vue logic)
       ====================================================== */

    async fetchSearchHistory() {
      if (!this.is_premium) return;

      try {
        const res = await apiClient.get("/api/search-history/list/");
        this.searchHistory = Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        console.error("fetchSearchHistory error:", err);
        this.searchHistory = [];
      }
    },

    /* ======================================================
        ⭐⭐ ADD SEARCH HISTORY (Home.vue logic)
       ====================================================== */
    async addSearchHistory(cityObj) {
      if (!this.is_premium || !cityObj || !cityObj.name) return;

      try {
        const payload = {
          city_name: cityObj.name,
          lat: cityObj.lat,
          lon: cityObj.lon,
        };

        await apiClient.post("/api/search-history/add/", payload);

        this.searchHistory = this.searchHistory.filter(
          (h) => h.city_name !== cityObj.name,
        );

        this.searchHistory.unshift({
          id: cityObj.id || null,
          name: cityObj.name,
          city_name: cityObj.name,
          lat: cityObj.lat,
          lon: cityObj.lon,
        });
      } catch (err) {
        console.error("addSearchHistory error:", err);
      }
    },

    /* ======================================================
        ⭐⭐ DELETE HISTORY — Home.vue logic
       ====================================================== */
    async deleteHistory(item) {
      if (!item) return;

      const id = item.id;
      if (!id) {
        this.searchHistory = this.searchHistory.filter((h) => h !== item);
        return;
      }

      const prev = [...this.searchHistory];
      this.searchHistory = this.searchHistory.filter((h) => h.id !== id);

      try {
        await apiClient.delete(
          `/api/search-history/clear/${encodeURIComponent(id)}/`,
        );
      } catch {
        this.searchHistory = prev;
      }
    },

    /* ======================================================
        ⭐⭐ SELECT HISTORY
       ====================================================== */
    selectHistory(h) {
      this.searchQuery = h.name;
      this.showHistory = false;

      if (h.lat && h.lon) {
        this.lastCity = h.name;
        this.lastLat = h.lat;
        this.lastLon = h.lon;

        this.updatePopup(h.name, h.lat, h.lon);
        if (this.map) this.map.panTo([h.lat, h.lon]);

        this.addSearchHistory(h);
      } else {
        this.fetchWeather(h.name);
      }
    },

    /* ======================================================
        ⭐⭐ SUGGESTIONS
       ====================================================== */
    async fetchSuggestions(q) {
      try {
        const res = await apiClient.get("/api/autocomplete_local/", {
          params: { q },
        });

        this.suggestions = Array.isArray(res.data) ? res.data : [];
        this.showSuggestions = this.suggestions.length > 0;
      } catch {
        this.suggestions = [];
      }
    },

    /* ======================================================
       ⭐⭐ SELECT SUGGESTION (add history)
       ====================================================== */
    async selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;

      this.lastCity = s.name;
      this.lastLat = s.lat;
      this.lastLon = s.lon;

      if (this.map) {
        await this.updatePopup(s.name, s.lat, s.lon);
        this.map.panTo([s.lat, s.lon]);
      }

      this.addSearchHistory(s);
    },

    async restoreFromLocalStorage() {
      try {
        const stored = localStorage.getItem("vietcloud_device_location");
        if (!stored) return;

        const parsed = JSON.parse(stored);
        const { fixed_name, lat, lon, timestamp } = parsed;
        const now = Date.now();

        // Cache 5 phút (300000 ms)
        if (now - timestamp > 300000) {
          console.log("🕒 Cached location expired.");
          return;
        }

        console.log("📍 Restoring from localStorage:", parsed);

        this.lastCity = fixed_name;
        this.lastLat = lat;
        this.lastLon = lon;

        // ✅ Gọi updatePopup mà không zoom (giống khi người dùng click suggestion)
        await this.updatePopup(fixed_name, lat, lon);

        // Nếu bạn muốn map pan nhẹ tới vị trí đó thì bật dòng dưới:
        // this.map.panTo([lat, lon]);
      } catch (err) {
        console.error("Error restoring from localStorage:", err);
      }
    },

    async updatePopup(cityName, lat, lon) {
      try {
        const res = await apiClient.get("/api/weather/", {
          params: { city: cityName },
        });
        const data = res.data;

        let content = `<b>${data.location}</b><br>`;

        if (this.activeLayer === "precipitation") {
          content += `🌧️ Rainfall: ${data.rainfall ?? 0} mm`;
        } else if (this.activeLayer === "temp") {
          const tempVal =
            data.temperature != null ? this.formatTemp(data.temperature) : "—";
          content += `🌡️ Temperature: ${
            tempVal !== "—" ? Math.round(tempVal) + this.tempUnitSymbol : "—"
          }`;
        } else if (this.activeLayer === "wind") {
          const windVal =
            data.wind_speed != null ? this.formatSpeed(data.wind_speed) : "—";
          content += `💨 Wind Speed: ${
            windVal !== "—" ? Math.round(windVal) + this.windUnitSymbol : "—"
          }`;
        }

        if (this.popupRef) {
          this.popupRef
            .setLatLng([lat, lon])
            .setContent(content)
            .openOn(this.map);
        } else {
          this.popupRef = L.popup({
            closeButton: false,
            autoClose: false,
            closeOnClick: false,
            className: "custom-popup",
          })
            .setLatLng([lat, lon])
            .setContent(content)
            .openOn(this.map);
        }
      } catch (err) {
        console.error("Error updating popup:", err);
      }
    },

    /* ======================================================
        ⭐⭐ FETCH WEATHER (add history)
       ====================================================== */
    async fetchWeather(city) {
      if (!city) return;

      try {
        const res = await apiClient.get("/api/weather/", {
          params: { city },
        });
        const data = res.data;

        this.errorMessage = "";

        const lat = data.lat ?? data.coord?.lat ?? null;
        const lon = data.lon ?? data.coord?.lon ?? null;

        this.lastCity = city;
        this.lastLat = lat;
        this.lastLon = lon;

        await this.updatePopup(city, lat, lon);
        if (this.map) this.map.panTo([lat, lon]);
      } catch {
        this.errorMessage = `Location '${city}' not found`;
      }
    },

    /* ======================================================
        ⭐⭐ ENTER SEARCH (add history)
       ====================================================== */
    async onEnterSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;

      try {
        const res = await apiClient.get("/api/autocomplete_local/", {
          params: { q },
        });
        const arr = res.data;

        if (Array.isArray(arr) && arr.length > 0) {
          const s = arr[0];

          this.lastCity = s.name;
          this.lastLat = s.lat;
          this.lastLon = s.lon;

          await this.updatePopup(s.name, s.lat, s.lon);
          if (this.map) this.map.panTo([s.lat, s.lon]);

          this.addSearchHistory(s);
        } else {
          await this.fetchWeather(q);
        }

        this.showSuggestions = false;
      } catch {
        await this.fetchWeather(q);
      }
    },

    onClickSearch() {
      this.onEnterSearch();
    },
  },

  watch: {
    $route() {
      this.showSidebar = false;
    },
  },
};
</script>

<style scoped src="@/assets/Map.css"></style>
