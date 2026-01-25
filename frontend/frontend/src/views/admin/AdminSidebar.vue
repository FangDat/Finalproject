<template>
  <aside class="sidebar-left">
    <h2 class="logo">
      <router-link to="/">🌤 VietCloud</router-link>
    </h2>

    <nav class="nav-menu">
      <router-link to="/admin/users" class="nav-btn">
        👤 Users
      </router-link>

      <router-link to="/admin/audit-logs" class="nav-btn">
        📜 Audit Logs
      </router-link>

      <router-link to="/" class="nav-btn">
        ⬅ Back to App
      </router-link>
    </nav>
  </aside>
</template>

<script>
export default {
  name: "AdminSidebar",
};
</script>

<style scoped src="@/assets/AdminSidebar.css"></style>
