<template>
  <WeatherBackground :mode="resolvedMode" :video-src="videoSrc">
    <slot />
  </WeatherBackground>
</template>

<script>
import WeatherBackground from "@/components/WeatherBackground.vue";
import nightSky from "@/assets/night_sky.mp4";

export default {
  name: "DynamicBackground",
  props: {
    iconCode: { type: String, required: true }, // ví dụ "01d" hoặc "03n"
  },
  components: { WeatherBackground },
  computed: {
    resolvedMode() {
      const map = {
        "01d": "day",
        "02d": "day",
        "01n": "night",
        "02n": "night",
        "03d": "cloudDay",
        "04d": "cloudDay",
        "03n": "cloudNight",
        "04n": "cloudNight",
        "09d": "rain",
        "09n": "rain",
        "10d": "rain",
        "10n": "rain",
        "11d": "thunderstorm",
        "11n": "thunderstorm",
        "13d": "snowDay",
        "13n": "snowDay",
      };
      return map[this.iconCode] || "default"; // fallback cuối cùng
    },
    videoSrc() {
      return this.resolvedMode === "night" ? nightSky : "";
    },
  },
};
</script>
