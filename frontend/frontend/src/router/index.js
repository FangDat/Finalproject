import { createRouter, createWebHashHistory } from "vue-router";
import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import TermsAndConditions from "../views/TermsAndConditions.vue";
import Billing from "../views/Billing.vue";
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
  { path: "/billing", name: "Billing", component: Billing },
  { path: "/map", name: "Map", component: MapPage },
  { 
    path: "/chatbot", 
    name: "Chatbot", 
    component: Chatbot,
    meta: { requiresAuth: true }   // 👈 cần login
  },
  { 
    path: "/profile", 
    name: "Profile", 
    component: Profile,
    meta: { requiresAuth: true }   // 👈 cần login
  },
  { path: "/privacy", name: "Privacy", component: PrivacyPolicy },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    } else {
      return { top: 0 };
    }
  },
});

// 🔐 Helper: đọc cookie
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

// 🔐 Navigation Guard toàn cục
router.beforeEach((to, from, next) => {
  const username = getCookie("username");  // ✅ dùng cookie thay localStorage
  if (to.matched.some(record => record.meta.requiresAuth) && !username) {
    next("/");  // chưa login → về Home
  } else {
    next();
  }
});

export default router;
