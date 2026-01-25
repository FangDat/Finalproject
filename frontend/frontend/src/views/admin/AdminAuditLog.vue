<template>
  <div class="audit-page">
    <h1 class="page-title">Audit Logs</h1>

    <table class="audit-table">
      <thead>
        <tr>
          <th>Time</th>
          <th>Action</th>
          <th>Admin</th>
          <th>Target User</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="l in logs" :key="l.log_id">
          <td>{{ formatTime(l.created_at_ts) }}</td>

          <td>
            <span class="badge action">
              {{ humanAction(l.action) }}
            </span>
          </td>

          <td>{{ l.admin_username }}</td>

          <td>
            {{ l.target_username || "—" }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { fetchAuditLogs } from "@/services/adminApi";

export default {
  data() {
    return {
      logs: [],
    };
  },

  async mounted() {
    this.logs = await fetchAuditLogs();
  },

  methods: {
    formatTime(ts) {
      return new Date(ts * 1000).toLocaleString("vi-VN");
    },

    humanAction(action) {
      const map = {
        BAN_USER: "Ban user",
        UNBAN_USER: "Unban user",
        UPDATE_PREMIUM: "Update premium",
        DELETE_USER: "Delete user",
      };
      return map[action] || action;
    },
  },
};
</script>

<style scoped>
.audit-page {
  max-width: 1200px;
}

.audit-table {
  width: 100%;
  background: white;
  border-radius: 14px;
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}

.audit-table th {
  background: #f0f4ff;
  padding: 14px;
  text-align: left;
}

.audit-table td {
  padding: 14px;
  border-top: 1px solid #eee;
}

.badge.action {
  padding: 6px 12px;
  border-radius: 20px;
  background: #e3f2fd;
  color: #1565c0;
  font-weight: 600;
}
</style>
