<template>
  <div class="profile-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">🌤 Viet Cloud</h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn">🤖 Chatbot</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link to="/profile" class="nav-btn">👤 Profile</router-link>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="main-content">
      <!-- Tabs -->
      <div class="tab-bar">
        <button class="tab" @click="scrollTo('basic')" :class="{ active: activeTab === 'basic' }">
          👤 Basic information
        </button>
        <button class="tab" @click="scrollTo('security')" :class="{ active: activeTab === 'security' }">
          🔒 Security
        </button>
        <button class="tab" @click="scrollTo('subscriptions')" :class="{ active: activeTab === 'subscriptions' }">
          💳 Subscriptions
        </button>
        <button class="tab" @click="scrollTo('support')" :class="{ active: activeTab === 'support' }">
          🧑‍💻 Support
        </button>
      </div>

      <!-- Basic information -->
      <section class="card" id="basic">
        <h2 class="sub-title">Basic information</h2>
        <div class="info-row">
          <label>Email</label>
          <div class="inline-input">
            <input type="text" :value="email || 'No email found'" readonly />
            <span class="change-link">change email</span>
          </div>
        </div>
        <div class="info-row">
          <label>Username</label>
          <div class="inline-input">
            <input type="text" :value="username || 'Not logged in'" readonly class="readonly-input" />
            <span class="note" v-if="username">cannot be changed</span>
          </div>
        </div>
      </section>

      <!-- Security -->
      <section class="card" id="security">
        <h2 class="sub-title">Security</h2>
        <p>Password</p>
        <p class="note">Last change on DD/MM/YYYY</p>
        <p>Protect your VietCloud account from unauthorized access. Use a strong password !!!</p>
        <div class="card-actions">
          <button class="btn-danger" @click="openChangePassword">Change password</button>
        </div>
      </section>

      <!-- Delete account -->
      <section class="card">
        <h2 class="sub-title">Delete VietCloud account</h2>
        <p>This action will delete your account and log you out.</p>
        <p class="note">
          You can delete your account at any time. Recovery is not possible.
          <b>This action is irreversible</b>.
        </p>
        <div class="card-actions">
          <button class="btn-danger" @click="logout">Delete your account</button>
        </div>
      </section>

      <!-- Subscriptions -->
      <section class="card" id="subscriptions">
        <h2 class="sub-title">Subscriptions</h2>
        <div class="payment-method">
          <p>Payment cards added and available:</p>
          <div class="card-row">
            <span>💳 XXXX XXXX XXXX XX69</span>
            <button class="btn-danger small" @click="handleAction('remove-card')">Remove</button>
          </div>
        </div>
        <div class="card-actions">
          <button class="btn-primary" @click="handleAction('add-card')">Add card</button>
        </div>
      </section>

      <!-- Premium -->
      <section class="card">
        <h2 class="sub-title">Premium</h2>
        <p>Your premium package has expired, please click the "Renew" button to continue using VietCloud's exclusive features.</p>
        <div class="card-actions">
          <button class="btn-primary" @click="handleAction('renew')">Renew</button>
        </div>
      </section>

      <!-- Feedback -->
      <section class="card" id="support">
        <h2 class="sub-title">Support</h2>
        <p>
          Need feedback or assistance? Leave a comment below or email
          <b>{{ email || 'support@vietcloud.com' }}</b>
        </p>
        <textarea rows="3" placeholder="Enter your message..."></textarea>
        <div class="card-actions">
          <button class="btn-primary" @click="handleAction('send-feedback')">Send</button>
        </div>
      </section>

      <!-- Footer links -->
      <footer class="footer-links">
        <router-link to="/privacy">Privacy Policy</router-link> |
        <router-link to="/terms">Terms & Conditions</router-link>
      </footer>
    </main>

    <!-- Overlay + Change Password Modal -->
    <div v-if="showChangePassword" class="overlay">
      <div class="modal">
        <h2>Change Password</h2>
        <p class="note">
          Password needs to be at least <b>8 characters long</b> and contain at least one <b>lowercase letter</b>, one <b>uppercase letter</b>, and a <b>number</b>.
        </p>

        <div class="form-group">
          <label>Current Password:</label>
          <input type="password" v-model="current_password" placeholder="Enter current password" />
        </div>
        <div class="form-group">
          <label>New Password:</label>
          <input type="password" v-model="new_password" placeholder="Enter new password" />
        </div>
        <div class="form-group">
          <label>Confirm New Password:</label>
          <input type="password" v-model="confirm_password" placeholder="Re-enter new password" />
        </div>

        <!-- Hiển thị thông báo -->
        <div class="alert-box" v-if="passwordAlert" :class="{'success': passwordSuccess, 'error': !passwordSuccess}">
          {{ passwordAlert }}
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="closeChangePassword">Close</button>
          <button class="btn-danger" @click="submitChangePassword" :disabled="submittingPassword">
            <span v-if="!submittingPassword">Set password</span>
            <span v-else>Processing...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "Profile",
  data() {
    return {
      activeTab: "basic",
      showChangePassword: false,
      username: null,
      email: null,
      current_password: "",
      new_password: "",
      confirm_password: "",
      passwordAlert: "",
      passwordSuccess: false,
      submittingPassword: false,
    };
  },
  created() {
    this.username = localStorage.getItem("username");
    this.email = localStorage.getItem("email");
    if (!this.username) {
      this.$router.push("/");
    }
  },
  methods: {
    scrollTo(section) {
      this.activeTab = section;
      const el = document.getElementById(section);
      if (el) el.scrollIntoView({ behavior: "smooth" });
    },
    handleAction(action) {
      alert(`Action triggered: ${action}`);
    },
    openChangePassword() {
      this.showChangePassword = true;
    },
    closeChangePassword() {
      this.showChangePassword = false;
      this.passwordAlert = "";
      this.passwordSuccess = false;
      this.current_password = "";
      this.new_password = "";
      this.confirm_password = "";
    },
    logout() {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      localStorage.removeItem("username");
      localStorage.removeItem("email");
      this.username = null;
      this.email = null;
      this.$router.push("/");
      window.location.reload();
    },
    async submitChangePassword() {
      this.passwordAlert = "";
      this.passwordSuccess = false;
      this.submittingPassword = true;

      try {
        const res = await axios.post(
          "http://127.0.0.1:8000/api/change-password/",
          {
            current_password: this.current_password,
            new_password: this.new_password,
            confirm_password: this.confirm_password,
          },
          {
            headers: { Authorization: `Bearer ${localStorage.getItem("access")}` },
          }
        );

        if (res.status === 200 && res.data.message) {
          this.passwordAlert = res.data.message;
          this.passwordSuccess = true;

          // Logout sau 2 giây
          setTimeout(() => {
            localStorage.removeItem("access");
            localStorage.removeItem("refresh");
            localStorage.removeItem("username");
            localStorage.removeItem("email");
            this.$router.push("/");
            window.location.reload();
          }, 3000);
        }
      } catch (err) {
        if (err.response?.data?.error) {
          this.passwordAlert = err.response.data.error; // Hiện đúng lỗi từ backend
        } else {
          this.passwordAlert = "Unexpected error. Please try again.";
        }
        this.passwordSuccess = false;
      } finally {
        this.submittingPassword = false;
      }
    },
  },
};
</script>

<style scoped src="@/assets/Profile.css"></style>
