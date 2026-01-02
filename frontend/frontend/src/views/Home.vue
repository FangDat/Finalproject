<template>
  <DynamicBackground :icon-code="currentIcon">
    <div class="home-container">
      <!-- Sidebar trái -->
      <aside class="sidebar-left">
        <h2 class="logo">🌤 VietCloud</h2>
        <nav class="nav-menu">
          <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
          <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
          <router-link v-if="username" to="/chatbot" class="nav-btn"
            >🤖 Chatbot</router-link
          >
          <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
          <router-link v-if="username" to="/profile" class="nav-btn"
            >👤 Profile</router-link
          >
        </nav>
      </aside>

      <!-- Nội dung chính -->
      <main class="main-content">
        <!-- Thanh trên cùng -->
        <header class="top-bar">
          <div class="left-header">
            <div class="search-container" style="position: relative">
              <input
                type="text"
                v-model="searchQuery"
                @input="onSearchInput"
                @keyup.enter="onEnterSearch"
                @focus="onFocusInput"
                placeholder="Search city..."
                class="search-bar"
                autocomplete_local="off"
              />
              <span class="search-icon" @click="onClickSearch">🔍</span>

              <!-- Suggestions dropdown -->
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

              <!-- Search History dropdown -->
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

        <!-- Nếu có lỗi -->
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
              {{
                temperature !== null
                  ? Math.round(formatTemp(temperature)) + tempUnitSymbol
                  : "—"
              }}
            </h2>
          </div>
          <div class="weather-icon">
            <img :src="weatherIcon" alt="Weather Icon" />
          </div>
        </section>

        <!-- Forecast trong ngày -->
        <section class="card" v-if="!errorMessage">
          <h3 class="section-title">Today's Forecast</h3>
          <div class="forecast-today scroll-x">
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

        <!-- Điều kiện không khí với ApexCharts -->
        <!-- Điều kiện không khí với animation mượt -->
        <section class="card" v-if="!errorMessage">
          <h3 class="section-title">Air Condition</h3>

          <div class="air-condition-list">

            <!-- ================= Real Feel ================= -->
            <div class="air-item air-realfeel">
              <div class="air-header" @click="toggleAir('realFeel')">
                <div class="air-main">
                  <span class="air-icon">🌡️</span>
                  <span class="air-value">
                    {{ realFeel ? Math.round(formatTemp(realFeel)) + tempUnitSymbol : "—" }}
                  </span>
                  <span class="air-label air-label-big">Real Feel</span>
                </div>
                <span class="air-toggle">{{ airOpen.realFeel ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.realFeel" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.real_feel"
                    :points="connectedBars.real_feel.points"
                    :direction="connectedBars.real_feel.direction"
                    :avgValue="formatAvgValue('real_feel', connectedBars.real_feel.points)"
                    :unit="tempUnitSymbol"
                    :valueFormatter="(v) => formatChartValue('real_feel', v)"
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.realFeel.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.realFeel.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- ================= Humidity ================= -->
            <div class="air-item air-humidity">
              <div class="air-header" @click="toggleAir('humidity')">
                <div class="air-main">
                  <span class="air-icon">🫧</span>
                  <span class="air-value">{{ humidity ? humidity + "%" : "—" }}</span>
                  <span class="air-label air-label-big">Humidity</span>
                </div>
                <span class="air-toggle">{{ airOpen.humidity ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.humidity" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.humidity"
                    :points="connectedBars.humidity.points"
                    :direction="connectedBars.humidity.direction"
                    :avgValue="formatAvgValue('humidity', connectedBars.humidity.points)"
                    unit="%"
                    :valueFormatter="(v) => formatChartValue('humidity', v)"
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.humidity.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.humidity.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- ================= Wind ================= -->
            <div class="air-item air-wind">
              <div class="air-header" @click="toggleAir('wind')">
                <div class="air-main">
                  <span class="air-icon">💨</span>
                  <span class="air-value">
                    {{ wind ? Math.round(formatSpeed(wind)) + windUnitSymbol : "—" }}
                  </span>
                  <span class="air-label air-label-big">Wind</span>
                </div>
                <span class="air-toggle">{{ airOpen.wind ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.wind" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.wind"
                    :points="connectedBars.wind.points"
                    :direction="connectedBars.wind.direction"
                    :avgValue="formatAvgValue('wind', connectedBars.wind.points)"
                    :unit="windUnitSymbol"
                    :valueFormatter="(v) => formatChartValue('wind', v)"
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.wind.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.wind.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- ================= Visibility ================= -->
            <div class="air-item air-visibility">
              <div class="air-header" @click="toggleAir('visibility')">
                <div class="air-main">
                  <span class="air-icon">👁️</span>
                  <span class="air-value">
                    {{ formatDistance(visibility) }} {{ distanceUnitSymbol }}
                  </span>
                  <span class="air-label air-label-big">Visibility</span>
                </div>
                <span class="air-toggle">{{ airOpen.visibility ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.visibility" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.visibility"
                    :points="connectedBars.visibility.points"
                    :direction="connectedBars.visibility.direction"
                    :avgValue="formatAvgValue('visibility', connectedBars.visibility.points)"
                    :unit="distanceUnitSymbol"
                    :valueFormatter="(v) => formatChartValue('visibility', v)"
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.visibility.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.visibility.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- ================= UV ================= -->
            <div class="air-item air-uv">
              <div class="air-header" @click="toggleAir('uv')">
                <div class="air-main">
                  <span class="air-icon">🌞</span>
                  <span class="air-value">{{ uvIndex ?? "—" }}</span>
                  <span class="air-label air-label-big">UV Index</span>
                </div>
                <span class="air-toggle">{{ airOpen.uv ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.uv" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.uv_index"
                    :points="connectedBars.uv_index.points"
                    :direction="connectedBars.uv_index.direction"
                    :avgValue="formatAvgValue('uv_index', connectedBars.uv_index.points)"
                    unit=""
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.uv.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.uv.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- ================= Chance of Rain ================= -->
            <div class="air-item air-rain">
              <div class="air-header" @click="toggleAir('rain')">
                <div class="air-main">
                  <span class="air-icon">💧</span>
                  <span class="air-value">{{ chanceOfRain }}</span>
                  <span class="air-label air-label-big">Chance of Rain</span>
                </div>
                <span class="air-toggle">{{ airOpen.rain ? "−" : "+" }}</span>
              </div>

              <transition name="air-slide">
                <div v-show="airOpen.rain" class="air-expand">
                  <SparklineChart
                    v-if="connectedBars?.chance_of_rain"
                    :points="connectedBars.chance_of_rain.points"
                    :direction="connectedBars.chance_of_rain.direction"
                    :avgValue="formatAvgValue('chance_of_rain', connectedBars.chance_of_rain.points)"
                    unit="%"
                  />
                  <div class="air-info">
                    <div class="air-info-title">{{ airInfoText.chance_of_rain.title }}</div>
                    <div class="air-info-desc">{{ airInfoText.chance_of_rain.desc }}</div>
                  </div>
                </div>
              </transition>
            </div>
          </div>
        </section>
      </main>

      <!-- Sidebar phải -->
      <aside class="sidebar-right" v-if="!errorMessage">
        <h3 class="section-title">Daily Forecast</h3>
        <div
          v-for="(day, index) in forecast3days"
          :key="index"
          class="forecast-3day"
        >
          <div>{{ day.day }}</div>
          <img :src="getDayIcon(day.icon)" class="forecast-icon" />
          <div>
            {{
              day.temp
                .split("/")
                .map((t) => Math.round(formatTemp(t)))
                .join("/")
            }}{{ tempUnitSymbol }}
          </div>
        </div>
        <p v-if="!is_premium" class="premium-text">
          Want forecast for 7 days? Upgrade for VietCloud premium now!
        </p>
        <router-link v-if="!username" to="/signup" class="btn-signup"
          >Sign up</router-link
        >

        <!-- Chatbot shortcut -->
        <div
          v-if="is_premium"
          class="chatbot-shortcut"
          @click="goToChatbot"
          title="Open VietCloud Chatbot"
        >
          <img src="@/assets/chatbot.png" alt="Chatbot" class="chatbot-icon" />
        </div>
      </aside>
    </div>
  </DynamicBackground>
</template>

<script>
import { cToF, msToKmh, msToMph, kmToMiles, mToKm, mToMiles } from "@/utils.js";
import WeatherError from "@/components/WeatherError.vue";
import DynamicBackground from "@/components/DynamicBackground.vue";
import SparklineChart from "@/components/SparklineChart.vue";

export default {
  name: "Home",
  components: {
    WeatherError,
    DynamicBackground,
    SparklineChart, // ✅ Import ApexCharts component
  },
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
      searchHistory: [],
      showHistory: false,
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
      errorMessage: "",
      errorGif: "",
      settings: {
        temperature: "Celsius",
        windSpeed: "Km/h",
        Visibility: "Kilometers",
      },
      airOpen: {
        realFeel: false,
        humidity: false,
        wind: false,
        visibility: false,
        uv: false,
        rain: false,
      },
      currentIcon: "01d",
      connectedBars: null,

      airInfoText: {
        realFeel: {
          title: "About Real Feel Temperature",
          desc:
            "Real Feel describes how warm or cold the weather actually feels on your skin, not just the number shown on the thermometer. " +
            "It takes into account factors such as humidity and wind, which can make hot days feel more uncomfortable or cold days feel even colder. " +
            "This value helps you better understand how the weather may affect your body when you are outdoors.",
        },

        humidity: {
          title: "About Relative Humidity",
          desc:
            "Relative humidity shows how much moisture is in the air compared to the maximum amount the air can hold at that temperature. " +
            "Warm air can store more moisture than cold air, which is why humidity often feels higher on warm days. " +
            "Values close to 100% may lead to fog, mist, or a damp feeling in the air.",
        },

        wind: {
          title: "About Wind Speed",
          desc:
            "Wind speed represents the average movement of air over a short period of time. " +
            "Occasional gusts are brief increases in wind speed that rise above this average and usually last only a few seconds. " +
            "Stronger winds can affect comfort, outdoor activities, and how cold the weather feels.",
        },

        visibility: {
          title: "About Visibility",
          desc:
            "Visibility indicates how far you can clearly see objects such as buildings, roads, or hills. " +
            "It reflects how clear the air is and can be reduced by fog, rain, haze, or pollution. " +
            "Visibility of 10 kilometers or more is generally considered clear.",
        },

        uv: {
          title: "About the UV Index",
          desc:
            "The UV Index measures the strength of ultraviolet radiation from the sun at a given time. " +
            "Higher values mean a greater risk of skin damage and faster sunburn. " +
            "The UV Index can help you decide when sun protection, such as hats or sunscreen, may be needed.",
        },

        chance_of_rain: {
          title: "About the Chance of Rain",
          desc:
            "The chance of rain shows how likely it is that rain will occur at a specific place and time. " +
            "A higher percentage means rain is more likely, but it does not indicate how heavy or long the rain will be. " +
            "This value is best used as a general guide when planning your day or outdoor activities.",
        },
      },
    };
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
  watch: {
    condition(newVal) {
      if (newVal && typeof newVal === "string") {
        this.currentIcon = newVal;
      }
    },
  },
  methods: {
    getCookie(name) {
      const match = document.cookie.match(
        new RegExp("(^| )" + name + "=([^;]+)")
      );
      return match ? decodeURIComponent(match[2]) : null;
    },
    formatTemp(tempC) {
      return this.settings.temperature === "Fahrenheit" ? cToF(tempC) : tempC;
    },
    formatSpeed(speedMs) {
      return this.settings.windSpeed === "Mph"
        ? msToMph(speedMs)
        : msToKmh(speedMs);
    },
    formatDistance(meters) {
      if (meters == null) return "—";
      return this.settings.Visibility === "Miles"
        ? Math.round(mToMiles(meters))
        : Math.round(mToKm(meters));
    },
    toggleAir(key) {
      this.airOpen[key] = !this.airOpen[key];
    },

    formatAvgValue(type, points) {
      if (!points || !points.length) return "";
      const avg = points.reduce((s, p) => s + p.value, 0) / points.length;

      switch (type) {
        case "real_feel":
          return Math.round(this.formatTemp(avg)) + this.tempUnitSymbol;
        case "humidity":
        case "chance_of_rain":
          return Math.round(avg) + "%";
        case "wind":
          return Math.round(this.formatSpeed(avg)) + this.windUnitSymbol;
        case "visibility":
          return (
            Math.round(this.formatDistance(avg)) + " " + this.distanceUnitSymbol
          );
        case "uv":
        case "uv_index":
          return avg.toFixed(1);
        default:
          return Math.round(avg);
      }
    },
    
    formatChartValue(type, rawValue) {
    if (rawValue == null || isNaN(rawValue)) return "—";

    switch (type) {
      case "real_feel":
        return Math.round(this.formatTemp(rawValue)) + this.tempUnitSymbol;

      case "humidity":
      case "chance_of_rain":
        return Math.round(rawValue) + "%";

      case "wind":
        return Math.round(this.formatSpeed(rawValue)) + this.windUnitSymbol;

      case "visibility":
        return (
          Math.round(this.formatDistance(rawValue)) +
          " " +
          this.distanceUnitSymbol
        );

      case "uv":
      case "uv_index":
        return rawValue.toFixed(1);

      default:
        return rawValue;
    }
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
    goToChatbot() {
      this.$router.push("/chatbot");
    },
    onSearchInput() {
      if (this.suggestTimer) clearTimeout(this.suggestTimer);
      const q = this.searchQuery.trim();
      if (!q) {
        this.showSuggestions = false;
        if (this.is_premium) {
          this.showHistory = true;
        }
        return;
      }
      this.showHistory = false;
      this.suggestTimer = setTimeout(() => {
        this.fetchSuggestions(q);
      }, 120);
    },
    async fetchUserInfo() {
      try {
        const res = await fetch("http://localhost:8000/api/user-info/", {
          method: "GET",
          credentials: "include",
        });
        if (!res.ok) throw new Error("Not logged in");
        const data = await res.json();
        this.username = data.username || "";
        this.is_premium = data.is_premium || false;
        if (this.is_premium) {
          this.fetchSearchHistory();
        }
      } catch (err) {
        this.username = "";
        this.is_premium = false;
        this.searchHistory = [];
      }
    },
    async fetchSearchHistory() {
      if (!this.is_premium) return;
      try {
        const res = await fetch(
          "http://localhost:8000/api/search-history/list/",
          {
            credentials: "include",
          }
        );
        const data = await res.json();
        if (Array.isArray(data)) {
          this.searchHistory = data;
        } else {
          this.searchHistory = [];
        }
      } catch (err) {
        console.error("fetchSearchHistory error", err);
        this.searchHistory = [];
      }
    },
    async addSearchHistory(cityObj) {
      if (!this.is_premium || !cityObj || !cityObj.name) return;
      try {
        const payload = {
          city_name: cityObj.name,
          lat: cityObj.lat,
          lon: cityObj.lon,
        };
        const res = await fetch(
          "http://localhost:8000/api/search-history/add/",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload),
          }
        );
        if (res.ok) {
          this.searchHistory = this.searchHistory.filter(
            (h) => h.city_name !== cityObj.name
          );
          this.searchHistory.unshift({
            id: cityObj.id || null,
            name: cityObj.name,
            city_name: cityObj.name,
            lat: cityObj.lat,
            lon: cityObj.lon,
          });
        }
      } catch (err) {
        console.error("addSearchHistory error", err);
      }
    },
    async deleteHistory(historyItem) {
      if (!historyItem) return;
      const id = historyItem.id;
      if (!id) {
        this.searchHistory = this.searchHistory.filter(
          (h) => h !== historyItem
        );
        return;
      }
      const prev = [...this.searchHistory];
      this.searchHistory = this.searchHistory.filter((h) => h.id !== id);
      try {
        const res = await fetch(
          `http://localhost:8000/api/search-history/clear/${encodeURIComponent(
            id
          )}/`,
          {
            method: "DELETE",
            credentials: "include",
          }
        );
        if (!res.ok) {
          this.searchHistory = prev;
          const errBody = await res.text().catch(() => null);
          console.warn("deleteHistory failed:", res.status, errBody);
        } else {
          if (!this.searchHistory.length) this.showHistory = false;
        }
      } catch (err) {
        this.searchHistory = prev;
        console.error("deleteHistory error", err);
      }
    },
    selectHistory(h) {
      this.searchQuery = h.name;
      this.showHistory = false;
      if (h.lat && h.lon) {
        this.getWeatherByLocation(h.lat, h.lon, h.name);
      } else {
        this.fetchWeather(h.name);
      }
    },
    async fetchSuggestions(q) {
      try {
        const res = await fetch(
          `http://localhost:8000/api/autocomplete_local/?q=${encodeURIComponent(
            q
          )}`
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
      this.addSearchHistory(s);
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
      this.addSearchHistory({ name: this.searchQuery.trim() });
    },
    onClickSearch() {
      this.onEnterSearch();
    },
    handleClickOutside(e) {
      const box = this.$el.querySelector(".search-container");
      if (!box || box.contains(e.target)) return;
      this.showSuggestions = false;
      this.showHistory = false;
    },
    onFocusInput() {
      const q = this.searchQuery.trim();
      if (!q && this.is_premium) {
        this.showHistory = true;
      }
    },
    async fetchWeather(city = "") {
      try {
        let url = city
          ? `http://localhost:8000/api/weather/?city=${encodeURIComponent(
              city
            )}`
          : "http://localhost:8000/api/weather/";
        const response = await fetch(url, { credentials: "include" });
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
      let url = `http://localhost:8000/api/weather/?lat=${encodeURIComponent(
        lat
      )}&lon=${encodeURIComponent(lon)}`;
      if (name) url += `&name=${encodeURIComponent(name)}`;
      fetch(url, { credentials: "include" })
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
      this.chanceOfRain = data.chance_of_rain
        ? data.chance_of_rain + "%"
        : "0%";
      this.condition = data.icon;
      this.humidity = data.humidity;
      this.uvIndex = data.uv_index;
      this.visibility = data.visibility;
      if (data.icon) {
        this.weatherIcon = this.getIconSrc(data.icon);
        this.currentIcon = data.icon;
      } else {
        this.weatherIcon = require("@/assets/01d.png");
      }
      this.forecastToday = (data.upcoming_hours || []).map((item) => ({
        time: item.time.split(" ")[1].slice(0, 5),
        temp: item.temp,
        icon: item.icon,
      }));
      this.forecast3days = (data.daily_forecast || []).map((item) => ({
        day: item.day,
        temp: item.temp,
        icon: item.icon,
      }));
      if (data.connected_bars_12h) {
        this.connectedBars = data.connected_bars_12h;
      } else {
        this.connectedBars = null;
      }
    },
  },
  mounted() {
    this.fetchUserInfo();
    document.addEventListener("click", this.handleClickOutside);
    const saved = localStorage.getItem("vietcloud_settings");
    if (saved) {
      this.settings = JSON.parse(saved);
    }
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
        this.fetchUserInfo();
      }
    }, 1000);

    const cachedLoc = localStorage.getItem("vietcloud_device_location");
    if (cachedLoc) {
      const cache = JSON.parse(cachedLoc);
      const now = Date.now();
      if (now - cache.timestamp < 300000) {
        const { lat, lon, fixed_name } = cache;
        this.getWeatherByLocation(lat, lon, fixed_name);
        return;
      } else {
        localStorage.removeItem("vietcloud_device_location");
      }
    }

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const res = await fetch(
            `http://localhost:8000/api/weather/?lat=${lat}&lon=${lon}`,
            { credentials: "include" }
          );
          const data = await res.json();
          if (res.ok) {
            const cache = {
              fixed_name: data.location,
              lat,
              lon,
              timestamp: Date.now(),
            };
            localStorage.setItem(
              "vietcloud_device_location",
              JSON.stringify(cache)
            );
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

    this.autoRefreshInterval = setInterval(() => {
      console.log("🔄 Auto refreshing page due to 20-minute timer...");
      window.location.reload();
    }, 20 * 60 * 1000);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleClickOutside);
    clearInterval(this.cookieCheckInterval);
    clearInterval(this.userCheckInterval);
    clearInterval(this.autoRefreshInterval);
  },
};
</script>

<style scoped src="@/assets/Home.css"></style>