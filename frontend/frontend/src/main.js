import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// import axios from "axios";

// ✅ Import CSS của Leaflet
import 'leaflet/dist/leaflet.css'
// axios.defaults.withCredentials = true;
createApp(App).use(router).mount('#app')
// axios.defaults.withCredentials = true;
