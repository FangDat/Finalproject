import { createRouter, createWebHashHistory } from "vue-router";
import Cookies from "js-cookie"; // ✅ [THÊM]

import Home from "../views/Home.vue";
import Login from "../views/Login.vue";
import TermsAndConditions from "../views/TermsAndConditions.vue";
import Billing from "../views/Billing.vue";
import MapPage from "../views/Map.vue";
import Chatbot from "../views/Chatbot.vue";
import Profile from "../views/Profile.vue";
import PrivacyPolicy from "../views/PrivacyPolicy.vue";


// Admin views
import AdminDashboard from "@/views/admin/AdminDashboard.vue";
import AdminUserList from "@/views/admin/AdminUserList.vue";
import AdminUserDetail from "@/views/admin/AdminUserDetail.vue";
import AdminAuditLog from "@/views/admin/AdminAuditLog.vue";


// ================= ROUTES =================
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
    // meta: { requiresAuth: true },
  },

  { path: "/terms", name: "Terms", component: TermsAndConditions },

  {
    path: "/billing",
    name: "Billing",
    component: Billing,
    meta: { requiresAuth: true },
  },

  { path: "/map", name: "Map", component: MapPage },

  {
    path: "/chatbot",
    name: "Chatbot",
    component: Chatbot,
    meta: { requiresAuth: true },
  },

  {
    path: "/profile",
    name: "Profile",
    component: Profile,
    meta: { requiresAuth: true },
  },

  { path: "/privacy", name: "Privacy", component: PrivacyPolicy },

  // ================= ADMIN =================
  {
    path: "/admin",
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true },

    redirect: "/admin/users",

    children: [
      { path: "users", component: AdminUserList },
      { path: "users/:id", component: AdminUserDetail },
      { path: "audit-logs", component: AdminAuditLog },
    ],
  },

];


// ================= ROUTER =================
const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition;
    return { top: 0 };
  },
});


// 🔐 Helper: đọc cookie (GIỮ NGUYÊN)
function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(^| )" + name + "=([^;]+)")
  );
  return match ? decodeURIComponent(match[2]) : null;
}


// ================= GLOBAL GUARD =================
router.beforeEach((to, from, next) => {
  const username = getCookie("username");   // auth
  const role = Cookies.get("role");         // admin

  // 🔐 REQUIRE LOGIN
  if (to.matched.some(r => r.meta.requiresAuth) && !username) {
    return next("/");
  }

  // 🔐 REQUIRE ADMIN (DÙNG COOKIE – KHÔNG CALL API)
  if (to.matched.some(r => r.meta.requiresAdmin) && role !== "admin") {
    return next("/"); // hoặc /403
  }

  next();
});

export default router;
