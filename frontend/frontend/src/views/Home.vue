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
                @focus="onFocusInput"
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
                            <!-- Search History dropdown (chỉ cho premium) -->
              <ul v-if="is_premium && showHistory && searchHistory.length" class="search-dropdown">
                <li
                  v-for="(h, idx) in searchHistory"
                  :key="h.id || idx"
                  class="dropdown-item"
                >
                  <div @click="selectHistory(h)" style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                    {{ h.name }}
                  </div>

                  <!-- nút X: dùng class đã có trong Home.css (.dropdown-delete-icon) -->
                  <button
                    class="dropdown-delete-icon"
                    :title="'Delete ' + h.name"
                    @click.stop="deleteHistory(h)"
                    aria-label="Delete history item"
                    style="background:none; border:none;"
                  >
                    x
                  </button>
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

        <!-- Điều kiện không khí -->
        <section class="card" v-if="!errorMessage">
          <h3 class="section-title">Air Condition</h3>

          <div class="air-condition-list">

            <!-- Item -->
            <div class="air-item air-realfeel">
              <div class="air-header" @click="toggleAir('realFeel')">
                <div class="air-main">
                  <span class="air-icon">🌡️</span>
                  <span class="air-value">
                    {{ realFeel ? Math.round(formatTemp(realFeel)) + tempUnitSymbol : '—' }}
                  </span>
                  <span class="air-label air-label-big">Real Feel</span>
                </div>
                <span class="air-toggle">{{ airOpen.realFeel ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.realFeel" class="air-expand">
                <div
                  v-if="connectedBars?.real_feel"
                  class="sparkbar"
                  :class="connectedBars.real_feel.direction"
                >
                  <!-- ⭐ AVERAGE LINE (1 LẦN DUY NHẤT) -->
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.real_feel.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('real_feel', connectedBars.real_feel.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.real_feel.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>


            <div class="air-item air-humidity">
              <div class="air-header" @click="toggleAir('humidity')">
                <div class="air-main">
                  <span class="air-icon">🫧</span>
                  <span class="air-value">{{ humidity ? humidity + '%' : '—' }}</span>
                  <span class="air-label air-label-big">Humidity</span>
                </div>
                <span class="air-toggle">{{ airOpen.humidity ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.humidity" class="air-expand">
                <div
                  v-if="connectedBars?.humidity"
                  class="sparkbar"
                  :class="connectedBars.humidity.direction"
                >
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.humidity.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('humidity', connectedBars.humidity.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.humidity.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="air-item air-wind">
              <div class="air-header" @click="toggleAir('wind')">
                <div class="air-main">
                  <span class="air-icon">💨</span>
                  <span class="air-value">
                    {{ wind ? Math.round(formatSpeed(wind)) + windUnitSymbol : '—' }}
                  </span>
                  <span class="air-label air-label-big">Wind</span>
                </div>
                <span class="air-toggle">{{ airOpen.wind ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.wind" class="air-expand">
                <div
                  v-if="connectedBars?.wind"
                  class="sparkbar"
                  :class="connectedBars.wind.direction"
                >
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.wind.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('wind', connectedBars.wind.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.wind.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>


            <div class="air-item air-visibility">
              <div class="air-header" @click="toggleAir('visibility')">
                <div class="air-main">
                  <span class="air-icon">👁️</span>
                  <span class="air-value">
                    {{ formatDistance(visibility) }} {{ distanceUnitSymbol }}
                  </span>
                  <span class="air-label air-label-big">Visibility</span>
                </div>
                <span class="air-toggle">{{ airOpen.visibility ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.visibility" class="air-expand">
                <div
                  v-if="connectedBars?.visibility"
                  class="sparkbar"
                  :class="connectedBars.visibility.direction"
                >
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.visibility.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('visibility', connectedBars.visibility.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.visibility.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="air-item air-uv">
              <div class="air-header" @click="toggleAir('uv')">
                <div class="air-main">
                  <span class="air-icon">🌞</span>
                  <span class="air-value">{{ uvIndex ?? '—' }}</span>
                  <span class="air-label air-label-big">UV Index</span>
                </div>
                <span class="air-toggle">{{ airOpen.uv ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.uv" class="air-expand">
                <div
                  v-if="connectedBars?.uv_index"
                  class="sparkbar"
                  :class="connectedBars.uv_index.direction"
                >
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.uv_index.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('uv_index', connectedBars.uv_index.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.uv_index.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="air-item air-rain">
              <div class="air-header" @click="toggleAir('rain')">
                <div class="air-main">
                  <span class="air-icon">💧</span>
                  <span class="air-value">{{ chanceOfRain }}</span>
                  <span class="air-label air-label-big">Chance of Rain</span>
                </div>
                <span class="air-toggle">{{ airOpen.rain ? '−' : '+' }}</span>
              </div>

              <div v-if="airOpen.rain" class="air-expand">
                <div
                  v-if="connectedBars?.chance_of_rain"
                  class="sparkbar"
                  :class="connectedBars.chance_of_rain.direction"
                >
                  <div
                    class="spark-average-line dashed half"
                    :style="getAverageLineStyle(connectedBars.chance_of_rain.points)"
                  >
                    <span class="spark-avg-label">
                      Avg {{ formatAvgValue('chance_of_rain', connectedBars.chance_of_rain.points) }}
                    </span>
                  </div>

                  <div
                    v-for="(p, i) in connectedBars.chance_of_rain.points"
                    :key="i"
                    class="spark-col"
                  >
                    <div
                      class="spark-point"
                      :style="getSparkStyle(p)"
                    ></div>

                    <div class="spark-hour">
                      {{ formatHour(p.time) }}
                    </div>
                  </div>
                </div>
              </div>
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
            {{ day.temp.split('/').map(t => Math.round(formatTemp(t))).join('/') }}{{ tempUnitSymbol }}
          </div>
        </div>
        <p v-if="!is_premium" class="premium-text">
          Want forecast for 7 days?  Upgrade for VietCloud premium now!
        </p>
        <router-link v-if="!username" to="/signup" class="btn-signup">Sign up</router-link>
         <!-- 🤖 Chatbot quick access (CHỈ PREMIUM) -->
        <div
          v-if="is_premium"
          class="chatbot-shortcut"
          @click="goToChatbot"
          title="Open VietCloud Chatbot"
        >
          <img
            src="@/assets/chatbot.png"
            alt="Chatbot"
            class="chatbot-icon"
          />
        </div>
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
const DOT_RADIUS = 5;
const SPARK_HEIGHT = 80;  
const SPARK_COL_WIDTH = 60;
export default {
  name: "Home",
  components: { WeatherError, DynamicBackground },
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
      uvIndex: null,
      errorMessage: "",
      errorGif: "",
      settings: {
        temperature: 'Celsius',
        windSpeed: 'Km/h',
        Visibility: 'Kilometers'
      },
      airOpen: {
        realFeel: false,
        humidity: false,
        wind: false,
        visibility: false,
        uv: false,
        rain: false
      },
      currentIcon: "01d", // ✅ thêm để điều khiển nền
      connectedBars: null,
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
    toggleAir(key) {
      this.airOpen[key] = !this.airOpen[key];
    },
    // 🔹 đồng bộ bán kính dot = 10 / 2
      // const DOT_RADIUS = 5;

    getSparkStyle(point) {
      const y = (point.normalized / 100) * SPARK_HEIGHT;
      return {
        bottom: `${y - DOT_RADIUS}px`
      };
    },


getConnectorStyle(p1, p2) {
  const y1 = (p1.normalized / 100) * SPARK_HEIGHT;
  const y2 = (p2.normalized / 100) * SPARK_HEIGHT;

  const dx = SPARK_COL_WIDTH;
  const dy = y2 - y1;

  const length = Math.sqrt(dx * dx + dy * dy);

  // Góc gốc (đang bị đối xứng sai)
  let angle = Math.atan2(dy, dx) * (180 / Math.PI);

  // 🔥 FIX THỦ CÔNG THEO QUY LUẬT 15°
  // Nếu đường đang hướng lên → lật xuống
  if (dy > 0) {
    angle = -angle;
  }

  return {
    width: `${length}px`,
    bottom: `${y1}px`,
    left: `50%`,
    transform: `rotate(${angle}deg)`,
    transformOrigin: "left center"
  };
},


      // ✅ TÍNH GIÁ TRỊ NORMALIZED TRUNG BÌNH (0–100)
getAverageNormalized(points) {
  if (!points || !points.length) return 0;
  const sum = points.reduce((acc, p) => acc + p.normalized, 0);
  return sum / points.length;
},

      // ✅ STYLE CHO THANH NGANG TRUNG BÌNH
      getAverageLineStyle(points) {
        const avg = this.getAverageNormalized(points);
        const y = (avg / 100) * SPARK_HEIGHT;

        return {
          bottom: `${y}px`
        };
      },
      
      formatAvgValue(type, points) {
        if (!points || !points.length) return '';

        const avg =
          points.reduce((s, p) => s + p.value, 0) / points.length;

        switch (type) {
          case 'real_feel':
            return Math.round(this.formatTemp(avg)) + this.tempUnitSymbol;

          case 'humidity':
          case 'chance_of_rain':
            return Math.round(avg) + '%';

          case 'wind':
            return Math.round(this.formatSpeed(avg)) + this.windUnitSymbol;

          case 'visibility':
            return (
              Math.round(this.formatDistance(avg)) +
              ' ' +
              this.distanceUnitSymbol
            );

          case 'uv':
          case 'uv_index':
            return avg.toFixed(1);

          default:
            return Math.round(avg);
        }
      },


      // ✅ format giờ: 01, 02, 03
      formatHour(time) {
        if (!time) return "";
        // "05:00" → "05"
        return time.split(":")[0];
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
        // ❌ KHÔNG ĐƯỢC GÁN searchHistory → suggestions nữa
        // ✔ Khi input rỗng → show History (nếu premium)
        this.showSuggestions = false;
        if (this.is_premium) {
          this.showHistory = true;
        }
        return;
      }

      // Khi có query → show autocomplete
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

        // ✅ nếu là premium, fetch search history
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
    if (!this.is_premium) return; // chỉ fetch nếu user premium
    try {
      const res = await fetch("http://localhost:8000/api/search-history/list/", {
        credentials: "include",
      });
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
   // --- ADD SEARCH HISTORY REALTIME ---
  async addSearchHistory(cityObj) {
    if (!this.is_premium || !cityObj || !cityObj.name) return;
    try {
      const payload = {
        city_name: cityObj.name,
        lat: cityObj.lat,
        lon: cityObj.lon
      };
      const res = await fetch("http://localhost:8000/api/search-history/add/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        // Realtime update local searchHistory: nếu đã tồn tại thì remove cũ + thêm mới lên đầu
        this.searchHistory = this.searchHistory.filter(h => h.city_name !== cityObj.name);
        this.searchHistory.unshift({
          id: cityObj.id || null,
          name: cityObj.name,
          city_name: cityObj.name,
          lat: cityObj.lat,
          lon: cityObj.lon
        });
      }
    } catch (err) {
      console.error("addSearchHistory error", err);
    }
  },

  // --- DELETE HISTORY ITEM (UI + backend) ---
  async deleteHistory(historyItem) {
    if (!historyItem) return;

    // Nếu chưa có id (chỉ UI item tạm) → chỉ xóa local
    const id = historyItem.id;
    if (!id) {
      this.searchHistory = this.searchHistory.filter(h => h !== historyItem);
      return;
    }

    // optimistic update: remove ngay khỏi UI để trải nghiệm mượt
    const prev = [...this.searchHistory];
    this.searchHistory = this.searchHistory.filter(h => h.id !== id);

    try {
      const res = await fetch(`http://localhost:8000/api/search-history/clear/${encodeURIComponent(id)}/`, {
        method: "DELETE",
        credentials: "include"
      });
      if (!res.ok) {
        // nếu server báo lỗi → rollback UI và log lỗi
        this.searchHistory = prev;
        const errBody = await res.text().catch(()=>null);
        console.warn("deleteHistory failed:", res.status, errBody);
      } else {
        // success → cũng clear cache showHistory nếu list rỗng
        if (!this.searchHistory.length) this.showHistory = false;
      }
    } catch (err) {
      // network error -> rollback UI
      this.searchHistory = prev;
      console.error("deleteHistory error", err);
    }
  },


  // --- Khi chọn từ history dropdown ---
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
      // --- Override onEnterSearch / selectSuggestion để add history realtime ---
    selectSuggestion(s) {
      this.searchQuery = s.name;
      this.showSuggestions = false;
      if (s.lat && s.lon) {
        this.getWeatherByLocation(s.lat, s.lon, s.name);
      } else {
        this.fetchWeather(s.name);
      }
      // ✅ thêm vào history realtime
      this.addSearchHistory(s);
    },
    onEnterSearch() {
    if (
      this.suggestions.length > 0 &&
      this.suggestions[0].name.toLowerCase() === this.searchQuery.trim().toLowerCase()
    ) {
      this.selectSuggestion(this.suggestions[0]);
      return;
    }
    this.fetchWeather(this.searchQuery.trim());
    this.showSuggestions = false;

    // Add to search history realtime
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
          ? `http://localhost:8000/api/weather/?city=${encodeURIComponent(city)}`
          : "http://localhost:8000/api/weather/";
        const response = await fetch(url, { credentials: 'include' });
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
      fetch(url, { credentials: 'include' })
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
      if (data.connected_bars_12h) {
        this.connectedBars = data.connected_bars_12h;
      } else {
        this.connectedBars = null;
      }
    }
  },
  

  mounted() {
    this.fetchUserInfo(); // ⚡ lấy thông tin user khi mount
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
            `http://localhost:8000/api/weather/?lat=${lat}&lon=${lon}`, 
              { credentials: 'include' }
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
    // --- AUTO REFRESH EVERY 15 MINUTES ---
    this.autoRefreshInterval = setInterval(() => {
      console.log("🔄 Auto refreshing page due to 20-minute timer...");
      window.location.reload();
    }, 20 * 60 * 1000); // 20 phút

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
