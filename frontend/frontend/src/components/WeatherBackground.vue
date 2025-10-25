<template>
  <div class="weather-bg" ref="vantaContainer">
    <!-- Night video background -->
    <video
      v-if="(mode === 'night' || mode === 'mist') && videoSrc"
      class="bg-video"
      autoplay
      muted
      loop
      playsinline
      preload="auto"
      :src="videoSrc"
    ></video>

    <!-- Static backgrounds for particles / thunderstorm -->
    <div
      v-else-if="['day', 'rain', 'snowDay', 'thunderstorm'].includes(mode)"
      id="particles-js"
      :style="containerBgStyle"
    ></div>

    <!-- Placeholder for Vanta clouds -->
    <div
      v-else-if="mode === 'cloudDay' || mode === 'cloudNight'"
      ref="vantaArea"
      class="vanta-area"
    ></div>

    <!-- Particle count (optional) -->
    <div class="count-particles" v-if="showStats">
      <span class="js-count-particles">--</span> particles
    </div>

    <!-- Slot for app content -->
    <div class="content-slot" :class="{ 'night-mode': mode === 'night' }">
      <slot />
    </div>
  </div>
</template>

<script>
import * as THREE from "three";
import CLOUDS from "vanta/dist/vanta.clouds.min";
import CLOUDS2 from "vanta/dist/vanta.clouds2.min";

export default {
  name: "WeatherBackground",
  props: {
    mode: { type: String, default: "day" },
    showStats: { type: Boolean, default: false },
    videoSrc: { type: String, default: "" },
  },
  data() {
    return { vantaEffect: null };
  },
  computed: {
    containerBgStyle() {
      const backgrounds = {
        day: "https://img1.teletype.in/files/45/ec/45ecbec5-20c2-4a30-a487-69ee0e0d31a6.gif",
        rain: "https://i.pinimg.com/originals/52/07/68/5207680e1eafd7233ab094b5f910e6af.gif",
        snowDay:
          "https://images.unsplash.com/photo-1589218112660-81ef972e89e3?auto=format&fit=crop&q=80&w=1930",
        thunderstorm: "https://giffiles.alphacoders.com/178/17850.gif",
      };

      const url = backgrounds[this.mode];
      if (url) {
        return {
          backgroundImage: `url(${url})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        };
      }
      return { backgroundColor: "#000" };
    },
  },
  methods: {
    loadScriptOnce(src) {
      return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) return resolve();
        const s = document.createElement("script");
        s.src = src;
        s.async = true;
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
      });
    },

    async ensureParticlesLibs() {
      if (!window.particlesJS) {
        await this.loadScriptOnce(
          "https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"
        );
      }
      if (this.showStats && !window.Stats) {
        await this.loadScriptOnce(
          "https://threejs.org/examples/js/libs/stats.min.js"
        );
      }
    },

    destroyParticles() {
      if (window.pJSDom && Array.isArray(window.pJSDom)) {
        window.pJSDom.forEach((entry) => {
          try {
            entry.pJS.fn.vendors.destroypJS();
          } catch {}
        });
        window.pJSDom = [];
      }
      const el = document.getElementById("particles-js");
      if (el) el.innerHTML = "";
    },

    destroyVanta() {
      if (this.vantaEffect) {
        this.vantaEffect.destroy();
        this.vantaEffect = null;
      }
    },

    async initParticlesForMode(mode) {
      this.destroyParticles();
      this.destroyVanta();

      // === NIGHT VIDEO ===
      if (mode === "night") return;

      // === CLOUD DAY ===
      if (mode === "cloudDay") {
        await this.$nextTick();
        if (!this.$refs.vantaArea) return;
        this.vantaEffect = CLOUDS({
          el: this.$refs.vantaArea,
          THREE,
          mouseControls: false,
          touchControls: false,
          gyroControls: false,
          skyColor: 0x6faed9,
          cloudColor: 0xdde6f1,
          speed: 1,
        });
        return;
      }

      // === CLOUD NIGHT ===
      if (mode === "cloudNight") {
        await this.$nextTick();
        if (!this.$refs.vantaArea) return;
        this.vantaEffect = CLOUDS2({
          el: this.$refs.vantaArea,
          THREE,
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          skyColor: 0x4a5c70,
          cloudColor: 0x202a3a,
          speed: 1,
          texturePath: "/vanta/noise.png",
        });
        return;
      }

      // === THUNDERSTORM === ⚡
      if (mode === "thunderstorm") {
        await this.ensureParticlesLibs();
        window.particlesJS("particles-js", {
          particles: {
            number: { value: 600, density: { enable: true, value_area: 200 } },
            color: { value: "#81cbeb" },
            shape: { type: "circle" },
            opacity: { value: 0.5, random: true },
            size: { value: 3.5, random: true },
            line_linked: { enable: false },
            move: {
              enable: true,
              speed: 20,
              direction: "bottom",
              straight: true,
              out_mode: "out",
            },
          },
          interactivity: {
            detect_on: "canvas",
            events: { onhover: { enable: false }, onclick: { enable: false } },
          },
          retina_detect: true,
        });
        return;
      }

      // === SNOW DAY ===
      if (mode === "snowDay") {
        await this.ensureParticlesLibs();
        window.particlesJS("particles-js", {
          particles: {
            number: { value: 800, density: { enable: true, value_area: 800 } },
            color: { value: "#fff" },
            shape: { type: "circle" },
            opacity: { value: 0.5, random: true },
            size: { value: 8, random: true },
            line_linked: { enable: false },
            move: {
              enable: true,
              speed: 8,
              direction: "bottom",
              straight: false,
              out_mode: "out",
            },
          },
          interactivity: { events: { onhover: { enable: false } } },
          retina_detect: true,
        });
        return;
      }

      // === DAY / RAIN ===
      await this.ensureParticlesLibs();
      const baseRain = {
        particles: {
          number: { value: 500, density: { enable: true, value_area: 800 } },
          color: { value: "#b5dbf5" },
          shape: { type: "circle" },
          opacity: { value: 0.4 },
          size: { value: 2.5 },
          move: { enable: true, speed: 29, direction: "bottom-right", straight: true },
          line_linked: { enable: false },
        },
        interactivity: {
          events: { onhover: { enable: false }, onclick: { enable: false } },
        },
        retina_detect: true,
      };

      const baseDay = {
        particles: {
          number: { value: 0 },
          color: { value: "#fff176" },
          shape: { type: "circle" },
          opacity: { value: 0.6 },
          size: { value: 4 },
          move: { enable: true, speed: 1.5, direction: "top", random: true },
        },
        retina_detect: true,
      };

      const cfg = mode === "rain" ? baseRain : baseDay;
      if (window.particlesJS) window.particlesJS("particles-js", cfg);
    },
  },
  mounted() {
    this.initParticlesForMode(this.mode);
  },
  watch: {
    mode(newMode) {
      this.initParticlesForMode(newMode);
    },
  },
  beforeUnmount() {
    this.destroyParticles();
    this.destroyVanta();
  },
};
</script>

<style scoped>
.weather-bg {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
.vanta-area,
#particles-js,
.bg-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.bg-video {
  object-fit: cover;
  z-index: 0;
}
#particles-js {
  z-index: 1;
}
.content-slot {
  position: relative;
  z-index: 2;
  pointer-events: auto;
}
</style>
