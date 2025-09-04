import { createRouter, createWebHashHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import TermsAndConditions from "../views/TermsAndConditions.vue";
import CreditCard from "../views/CreditCard.vue";
import MapPage from "../views/Map.vue";
import Chatbot from "../views/Chatbot.vue";
import Profile from "../views/Profile.vue";
import PrivacyPolicy from "../views/PrivacyPolicy.vue";

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
    component: () => import("@/views/Settings.vue"),
  },
  { path: "/terms", name: "Terms", component: TermsAndConditions },
  {
    path: "/credit-card",
    name: "CreditCard",
    component: CreditCard,
  },
  {
    path: "/map",
    name: "Map",
    component: MapPage,
  },
  { path: "/chatbot", name: "Chatbot", component: Chatbot },
  { path: "/profile", name: "Profile", component: Profile },
  { path: "/privacy", name: "Privacy", component: PrivacyPolicy },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Nếu dùng back/forward thì giữ nguyên vị trí
    if (savedPosition) {
      return savedPosition;
    } else {
      // Còn khi vào route mới thì scroll lên đầu
      return { top: 0 };
    }
  },
});

export default router;
