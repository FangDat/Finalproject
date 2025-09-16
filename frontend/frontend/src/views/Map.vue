<template>
  <div class="map-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 Viet Cloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn active">🗺️ Maps</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="map-main">
      <!-- Thanh trên cùng -->
      <header class="top-bar">
        <input type="text" placeholder="Search" class="search-bar" />
        <button class="btn-flash">⚡</button>
      </header>

      <!-- Danh sách city weather -->
      <section class="city-weather-list">
        <div v-for="(city, index) in cities" :key="index" class="city-weather-card">
          <div class="icon">{{ city.icon }}</div>
          <div class="city-info">
            <h4>{{ city.name }}</h4>
            <p class="time">{{ city.time }}</p>
          </div>
          <div class="temp">{{ city.temp }}°C</div>
        </div>
      </section>

      <!-- Khung bản đồ (placeholder) -->
      <section class="map-box">
        <p>🗺️ Map area</p>
      </section>
    </main>
  </div>
</template>

<script>
export default {
  name: "Map",
  data() {
    return {
      cities: [
        { name: "Ha Noi", time: "10:23", temp: 18, icon: "🌧️" },
        { name: "Ho Chi Minh", time: "10:23", temp: 28, icon: "⛅" },
        { name: "Da Nang", time: "10:23", temp: 36, icon: "☀️" },
      ],
    };
  },
};
</script>

<!-- <style src="@/assets/common.css"></style> -->
<style src="@/assets/Map.css"></style>
