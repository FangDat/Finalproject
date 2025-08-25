<template>
  <div class="card">
    <h2>{{ city }}</h2>
    <div v-if="weather">
      <p>🌡 Temp: {{ weather.temp }}°C</p>
      <p>☀️ Condition: {{ weather.condition }}</p>
      <p>💧 Humidity: {{ weather.humidity }}%</p>
    </div>
    <div v-else>
      <p>Loading...</p>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    city: String,
    weather: Object,
  },
};
</script>

<style>
.card {
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 15px 20px;
  width: 180px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
</style>
