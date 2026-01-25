<template>
  <div class="admin-layout">
    <!-- ✅ SIDEBAR GIỐNG CHATBOT -->
    <AdminSidebar />

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
  components: {
    AdminSidebar,
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
</style>
