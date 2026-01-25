<template>
  <div v-if="user" class="admin-user-detail">
    <h2 class="username">{{ user.username }}</h2>

    <div class="info-row">
      <span class="label">Email</span>
      <span>{{ user.email }}</span>
    </div>

    <div class="info-row">
      <span class="label">Premium until</span>
      <span>
        {{ user.premium_expires_at_ts
          ? formatTimestamp(user.premium_expires_at_ts)
          : "Not premium" }}
      </span>
    </div>

    <!-- UPDATE PREMIUM -->
    <div class="premium-box">
      <label class="premium-label">Extend premium (days)</label>

      <input
        v-model.number="days"
        type="number"
        min="1"
        class="premium-input"
      />

      <button
        class="btn-update"
        @click="grantPremium"
      >
        Update Premium
      </button>
    </div>
  </div>
</template>
<script>
import { fetchUserDetail, updatePremium } from "@/services/adminApi";

export default {
  data() {
    return {
      user: null,
      days: 30,
    };
  },

  async mounted() {
    await this.reloadUser();
  },

  methods: {
    // 🔄 RELOAD USER (DÙNG LẠI)
    async reloadUser() {
      this.user = await fetchUserDetail(this.$route.params.id);
    },

    // ⏰ FORMAT UNIX TIMESTAMP → YYYY-MM-DD HH:mm
    formatTimestamp(ts) {
      const date = new Date(ts * 1000); // seconds → ms
      return date.toLocaleString("vi-VN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    },

    // ⭐ UPDATE PREMIUM
    async grantPremium() {
      if (this.days <= 0) {
        alert("Days must be greater than 0");
        return;
      }

      await updatePremium(this.user.user_id, this.days);
      alert("Premium updated successfully");

      // ✅ F5 DATA
      await this.reloadUser();
    },
  },
};
</script>
<style scoped>.admin-user-detail {
  max-width: 520px;
  background: white;
  padding: 24px;
  border-radius: 14px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
}

.username {
  margin-bottom: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.label {
  font-weight: 600;
  color: #555;
}

/* ===========================
   PREMIUM BOX
=========================== */
.premium-box {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.premium-label {
  font-weight: 600;
}

.premium-input {
  padding: 12px;
  font-size: 1rem;
  border-radius: 10px;
  border: 1px solid #ccc;
}

.premium-input:focus {
  border-color: #2196f3;
  outline: none;
}

.btn-update {
  padding: 12px;
  border-radius: 10px;
  border: none;
  background: #2196f3;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.btn-update:hover {
  background: #1976d2;
}
</style>