import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// ✅ Import CSS của Leaflet
import 'leaflet/dist/leaflet.css'

createApp(App).use(router).mount('#app')
