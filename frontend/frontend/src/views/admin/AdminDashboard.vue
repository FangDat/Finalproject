<template>
  <div class="admin-layout">

    <!-- ☰ MOBILE TOGGLE -->
    <button class="sidebar-toggle" @click="toggleSidebar">☰</button>

    <!-- OVERLAY -->
    <div
      v-if="showSidebar"
      class="sidebar-overlay"
      @click="closeSidebar"
    ></div>

    <!-- SIDEBAR -->
    <AdminSidebar :open="showSidebar" @close="closeSidebar" />

    <!-- MAIN CONTENT -->
    <main class="content">
      <router-view />
    </main>

  </div>
</template>


<script>
import AdminSidebar from "./AdminSidebar.vue";

export default {
  name: "AdminDashboard",
  components: { AdminSidebar },
  data() {
    return {
      showSidebar: false,
    };
  },
  methods: {
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },
    closeSidebar() {
      this.showSidebar = false;
    },
  },
};
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 220px;
  background: #1e1e2f;
  color: white;
  padding: 20px;
}

.sidebar a {
  display: block;
  color: white;
  margin: 12px 0;
  text-decoration: none;
}

.sidebar a.router-link-active {
  font-weight: bold;
  color: #4fc3f7;
}

/* Content */
.content {
  flex: 1;
  padding: 25px;
  background: #f5faff;
}

.sidebar-toggle {
  display: none;
  position: fixed;
  top: 70px;
  left: 18px;
  z-index: 1500;
  background: #2196f3;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 22px;
  padding: 8px 14px;
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 1100;   /* ⭐ thấp hơn sidebar */
}


@media (max-width: 768px) {
  .sidebar-toggle {
    display: block;
  }
}

</style>
