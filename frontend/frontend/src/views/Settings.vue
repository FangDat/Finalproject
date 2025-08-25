<template>
  <div class="settings-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 Viet Cloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link to="/settings" class="nav-btn active">⚙️ Settings</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="settings-main">
      <!-- Units -->
      <section class="card">
        <h3 class="section-title">Units</h3>
        <div class="unit-group">
          <p><strong>TEMPERATURE</strong></p>
          <button
            class="unit-btn"
            :class="{ active: temperature === 'Celsius' }"
            @click="temperature = 'Celsius'"
          >
            Celsius
          </button>
          <button
            class="unit-btn"
            :class="{ active: temperature === 'Fahrenheit' }"
            @click="temperature = 'Fahrenheit'"
          >
            Fahrenheit
          </button>

          <p><strong>WIND SPEED</strong></p>
          <button
            class="unit-btn"
            :class="{ active: windSpeed === 'Km/h' }"
            @click="windSpeed = 'Km/h'"
          >
            Km/h
          </button>
          <button
            class="unit-btn"
            :class="{ active: windSpeed === 'Mph' }"
            @click="windSpeed = 'Mph'"
          >
            Mph
          </button>

          <p><strong>DISTANCE</strong></p>
          <button
            class="unit-btn"
            :class="{ active: distance === 'Kilometers' }"
            @click="distance = 'Kilometers'"
          >
            Kilometers
          </button>
          <button
            class="unit-btn"
            :class="{ active: distance === 'Miles' }"
            @click="distance = 'Miles'"
          >
            Miles
          </button>
        </div>
      </section>

      <!-- Notifications -->
      <section class="card">
        <h3 class="section-title">Notifications</h3>
        <div class="toggle-item" @click="notifications = !notifications">
          <span>Be aware of the weather</span>
          <span class="check" v-if="notifications">✔</span>
        </div>
      </section>

      <!-- General -->
      <section class="card">
        <h3 class="section-title">General</h3>
        <div class="toggle-item" @click="generalLocation = !generalLocation">
          <span>Get weather of your location</span>
          <span class="check" v-if="generalLocation">✔</span>
        </div>
      </section>
    </main>

    <!-- Sidebar phải -->
    <aside class="sidebar-right">
      <h3 class="section-title">Advanced</h3>
      <p>* Chat bot<br />* 7 days Forecast<br />* Search History</p>
      <p><strong>Try now to experience exclusive features</strong></p>

      <div class="pricing-box">
        <p>$6.96 / month</p>
        <router-link to="/signup" class="btn-signup">Sign up</router-link>
      </div>
    </aside>
  </div>
</template>

<script>
export default {
  name: "Settings",
  data() {
    return {
      temperature: "Celsius",
      windSpeed: "Km/h",
      distance: "Kilometers",
      notifications: false,
      generalLocation: false,
    };
  },
};
</script>

<style src="@/assets/common.css"></style>
<style src="@/assets/Settings.css"></style>
