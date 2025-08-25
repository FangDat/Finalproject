import { createRouter, createWebHashHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import TermsAndConditions from "../views/TermsAndConditions.vue"
import CreditCard from "../views/CreditCard.vue" //
import MapPage from "../views/Map.vue"; //
import Chatbot from "../views/Chatbot.vue"; 

const routes = [
  { path: "/", name: "Home", component: Home },
  { path: "/login", name: "Login", component: Login },
  {
    path: "/signup",
    name: "SignUp",
    component: () => import("@/views/SignUp.vue"),
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("@/views/Settings.vue"), // 👈 thêm dòng này
  },
  { path: "/terms", name: "Terms", component: TermsAndConditions }, 
   {
    path: '/credit-card',   // 👉 setup route cho CreditCard.vue
    name: 'CreditCard',
    component: CreditCard
  },
  {
    path: "/map",
    name: "Map",
    component: MapPage,
  },
   { path: "/chatbot", name: "Chatbot", component: Chatbot }, 
  
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
