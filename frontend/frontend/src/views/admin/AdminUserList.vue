<template>
  <div class="admin-users-page">
    <h1 class="page-title">Users</h1>

    <!-- 🔍 SEARCH BAR -->
    <div class="search-container admin-search">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Search user by username..."
        class="search-bar"
      />
      <span class="search-icon">🔍</span>
    </div>

    <!-- 📋 USER TABLE -->
    <!-- 📋 USER TABLE (DESKTOP) -->
    <div class="table-wrapper desktop-only">
      <table class="user-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Active</th>
            <th>Premium</th>
            <th class="actions-col">Actions</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="u in users" :key="u.user_id">
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>

            <td>
              <span class="badge role">
                {{ u.role === "admin" ? "Admin" : "User" }}
              </span>
            </td>

            <td>
              <span
                class="badge status"
                :class="u.is_active ? 'active' : 'inactive'"
              >
                {{ u.is_active ? "Active" : "Banned" }}
              </span>
            </td>

            <td>
              <span
                class="badge premium-status"
                :class="u.is_premium ? 'premium' : 'free'"
              >
                {{ u.is_premium ? "Premium" : "Free" }}
              </span>
            </td>

            <td class="actions">
              <button
                class="btn btn-ban"
                :disabled="u.role === 'admin'"
                @click="toggleBan(u)"
              >
                {{ u.is_active ? "Ban" : "Unban" }}
              </button>

              <button
                class="btn btn-detail"
                @click="$router.push('/admin/users/' + u.user_id)"
              >
                Detail
              </button>

              <button
                class="btn btn-delete"
                :disabled="u.role === 'admin'"
                @click="deleteUserConfirm(u)"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 📱 USER CARDS (MOBILE) -->
    <div class="user-cards mobile-only">
      <div v-for="u in users" :key="u.user_id" class="user-card">
        <h3>{{ u.username }}</h3>

        <p><b>Email:</b> {{ u.email }}</p>
        <p><b>Role:</b> {{ u.role }}</p>
        <p>
          <b>Status:</b>
          <span :class="['badge', u.is_active ? 'active' : 'inactive']">
            {{ u.is_active ? "Active" : "Banned" }}
          </span>
        </p>

        <p>
          <b>Plan:</b>
          <span :class="['badge', u.is_premium ? 'premium' : 'free']">
            {{ u.is_premium ? "Premium" : "Free" }}
          </span>
        </p>

        <!-- ✅ 3 BUTTONS -->
        <div class="card-actions">
          <button
            class="btn btn-ban"
            :disabled="u.role === 'admin'"
            @click="toggleBan(u)"
          >
            {{ u.is_active ? "Ban" : "Unban" }}
          </button>

          <button
            class="btn btn-detail"
            @click="$router.push('/admin/users/' + u.user_id)"
          >
            Detail
          </button>

          <button
            class="btn btn-delete"
            :disabled="u.role === 'admin'"
            @click="deleteUserConfirm(u)"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  fetchUsers,
  banOrUnbanUser,
  deleteUser,
} from "@/services/adminApi";


export default {
  name: "AdminUserList",

  data() {
    return {
      users: [],
      loading: false,
      searchQuery: "",
      debounceTimer: null,
    };
  },

  mounted() {
    this.fetchUsers();
  },

  watch: {
    searchQuery(newVal) {
      if (this.debounceTimer) clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.fetchUsers(newVal);
      }, 250);
    },
  },

  methods: {
    async fetchUsers(query = "") {
      this.loading = true;
      try {
        this.users = await fetchUsers(query);
      } catch (err) {
        console.error("Fetch users failed", err);
        this.users = [];
      } finally {
        this.loading = false;
      }
    },

    async toggleBan(user) {
      if (!confirm("Confirm change user status?")) return;

      await banOrUnbanUser(user.user_id);
      await this.fetchUsers(this.searchQuery);
    },

    async deleteUserConfirm(user) {
      if (!confirm("CONFIRM DELETE USER?")) return;

      await deleteUser(user.user_id);
      await this.fetchUsers(this.searchQuery);
    },
  },
};
</script>

<style scoped>
/* ===========================
   PAGE
=========================== */
.admin-users-page {
  max-width: 1400px;
}

.page-title {
  margin-bottom: 10px;
}

/* ===========================
   SEARCH
=========================== */
.admin-search {
  max-width: 420px;
  margin: 16px 0 24px 0;
}

.search-container {
  position: relative;
}

.search-bar {
  width: 100%;
  padding: 12px 45px 12px 20px;
  border-radius: 30px;
  border: 1px solid #ccc;
}

.search-icon {
  position: absolute;
  right: 42px; 
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  font-size: 1.2rem;
}
/* ===========================
   TABLE
=========================== */
.table-wrapper {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.user-table th {
  background: #f0f4ff;
  padding: 14px 16px;
  font-weight: 600;
}

.user-table td {
  padding: 14px 16px;
  border-top: 1px solid #eee;
}

.actions-col {
  text-align: center;
  width: 260px;
}

/* ===========================
   BADGES (FIX SIZE)
=========================== */
.badge {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-width: 90px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.badge.role {
  background: #ede7f6;
  color: #5e35b1;
}

.badge.active {
  background: #e6f7ed;
  color: #1b8f4c;
}

.badge.inactive {
  background: #fdecea;
  color: #c62828;
}

.badge.premium {
  background: #fff4e5;
  color: #ef6c00;
}

.badge.free {
  background: #e3f2fd;
  color: #1565c0;
}

/* ===========================
   ACTION BUTTONS
=========================== */
.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.btn-ban {
  background: #ffb300;
  color: white;
}

.btn-detail {
  background: #2196f3;
  color: white;
}

.btn-delete {
  background: #e53935;
  color: white;
}
/* ===========================
   DISABLED BUTTON (ADMIN)
=========================== */
.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  filter: grayscale(40%);
}

.btn:disabled:hover {
  transform: none;
}
.audit-cards {
  display: none;
}

@media (max-width: 768px) {
  .audit-table {
    display: none;
  }

  .audit-cards {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .audit-card {
    background: white;
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
  }
}

/* =====================
   RESPONSIVE SWITCH
===================== */
.desktop-only {
  display: block;
}

.mobile-only {
  display: none;
}

@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }

  .mobile-only {
    display: block;
  }
}
@media (max-width: 768px) {
  .admin-search {
    max-width: 260px;
    margin-bottom: 16px;
  }

  .search-bar {
    padding: 8px 38px 8px 14px;
    font-size: 0.85rem;
  }

  .search-icon {
    right: 32px; 
    font-size: 0.9rem;
  }
}
/* =====================
   MOBILE CARD
===================== */
.user-card {
  background: white;
  padding: 18px;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}

.card-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.card-actions .btn {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  font-size: 0.85rem;
}


</style>
