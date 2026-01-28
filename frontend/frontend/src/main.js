import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import VueApexCharts from "vue3-apexcharts";
// import axios from "axios";
import '@/assets/global.css'

// ✅ Import CSS của Leaflet
import "leaflet/dist/leaflet.css";
// axios.defaults.withCredentials = true;
const app = createApp(App);
app.use(VueApexCharts);
app.use(router);
app.mount("#app");
// axios.defaults.withCredentials = true;