<template>
  <aside class="sidebar-left" :class="{ open: open }">
    <h2 class="logo">
      <router-link to="/" class="logo-link">
        <img src="@/assets/cloudy.png" class="logo-icon" />
        VietCloud
      </router-link>
    </h2>

    <nav class="nav-menu">
      <router-link to="/admin/users" class="nav-btn" @click.native="$emit('close')">
        <img src="@/assets/user.png" class="sidebar-icon" />
        Users
      </router-link>

      <router-link to="/admin/audit-logs" class="nav-btn" @click.native="$emit('close')">
        <img src="@/assets/audit.png" class="sidebar-icon" />
        Audit Logs
      </router-link>

      <router-link to="/" class="nav-btn" @click.native="$emit('close')">
        ⬅ Back to App
      </router-link>
    </nav>
  </aside>
</template>

<script>
export default {
  name: "AdminSidebar",
  props: {
    open: Boolean,
  },
};
</script>

<style scoped src="@/assets/AdminSidebar.css"></style>
