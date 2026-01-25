<template>
  <div class="reload-overlay">
    <div class="reload-box">
      <h2>⚠️ Account status changed</h2>
      <p>
        Your account has been updated or suspended.<br />
        Please log in again to continue.
      </p>
      <button @click="goLogin">Go to Login</button>
    </div>
  </div>
</template>

<script>
export default {
  name: "ReloadPage",
  mounted() {
    // đảm bảo không còn cookie UI
    document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "email=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  },
  methods: {
    goLogin() {
      this.$router.replace("/login");
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.reload-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.reload-box {
  background: white;
  padding: 30px;
  border-radius: 18px;
  text-align: center;
  max-width: 420px;
}
.reload-box button {
  margin-top: 20px;
  padding: 12px 24px;
  border-radius: 20px;
  border: none;
  background: #2196f3;
  color: white;
  font-weight: bold;
}
</style>
