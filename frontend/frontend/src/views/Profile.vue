<template>
  <div class="profile-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 Viet Cloud</router-link>
      </h2>
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
          <button class="btn-danger" @click="openWarningModal">Delete your account</button>
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
      <!-- Feedback -->
      <section class="card" id="support">
        <h2 class="sub-title">Support</h2>
        <p>
          Need feedback or assistance? Leave a comment below.<br>
          Success notification will appear soon, please do not spam !!!
        </p>
        <textarea v-model="feedbackMessage" rows="3" placeholder="Enter your message..."></textarea>
        <div class="card-actions">
          <button
            class="btn-primary"
            @click="sendFeedback"
            :disabled="sendingDisabled"
          >
            <span v-if="sendingDisabled">
              Please wait {{ countdown }}s…
            </span>
            <span v-else>Send</span>
          </button>
        </div>
      </section>


      <!-- Footer links -->
      <footer class="footer-links">
        <router-link to="/privacy">Privacy Policy</router-link> |
        <router-link to="/terms">Terms & Conditions</router-link>
      </footer>
    </main>

    <!-- Overlay + Change Password Modal -->
    <transition name="fade">
      <div v-if="showChangePassword" class="overlay">
        <div class="modal">
          <h2>Change Password</h2>
          <p class="note">
            Password needs to be at least <b>8 characters long</b> and contain at least one <b>lowercase letter</b>, one <b>uppercase letter</b>, and a <b>number</b>.
          </p>

          <div class="form-group password-wrapper">
            <label>Current Password:</label>
            <input :type="showCurrentPassword ? 'text' : 'password'" v-model="current_password" placeholder="Enter current password" />
            <span class="toggle-icon" @click="showCurrentPassword = !showCurrentPassword">{{ showCurrentPassword ? '🙈' : '👁' }}</span>
          </div>
          <div class="form-group password-wrapper">
            <label>New Password:</label>
            <input :type="showNewPassword ? 'text' : 'password'" v-model="new_password" placeholder="Enter new password" />
            <span class="toggle-icon" @click="showNewPassword = !showNewPassword">{{ showNewPassword ? '🙈' : '👁' }}</span>
          </div>
          <div class="form-group password-wrapper">
            <label>Confirm New Password:</label>
            <input :type="showConfirmPassword ? 'text' : 'password'" v-model="confirm_password" placeholder="Re-enter new password" />
            <span class="toggle-icon" @click="showConfirmPassword = !showConfirmPassword">{{ showConfirmPassword ? '🙈' : '👁' }}</span>
          </div>

          <!-- Alert -->
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
    </transition>

    <!-- Overlay + Warning Modal -->
    <transition name="fade">
      <div v-if="showWarning" class="overlay">
        <div class="modal warning-modal">
          <h2>⚠️ Warning</h2>
          <p class="note">
            Deleting your account will also remove <b>all active subscriptions and services</b> linked to this account.  
            This action <b>cannot be undone</b>.
          </p>
          <div class="modal-actions">
            <button class="btn-secondary" @click="closeWarning">Cancel</button>
            <button class="btn-danger" @click="proceedDeleteAccount">I understand, continue</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Overlay + Delete Account Modal -->
    <transition name="fade">
      <div v-if="showDeleteAccount" class="overlay">
        <div class="modal">
          <h2>Delete your account</h2>
          <p class="note">
            You can delete your account at any time. Recovery is not possible.
            <b>This action is irreversible.</b>
          </p>

          <div class="form-group">
            <label>Username:</label>
            <input type="text" v-model="delete_username" placeholder="Enter your username" />
          </div>
          <div class="form-group password-wrapper">
            <label>Password:</label>
            <input :type="showDeletePassword ? 'text' : 'password'" v-model="delete_password" placeholder="Enter your password" />
            <span class="toggle-icon" @click="showDeletePassword = !showDeletePassword">{{ showDeletePassword ? '🙈' : '👁' }}</span>
          </div>
          <div class="form-group password-wrapper">
            <label>Confirm Password:</label>
            <input :type="showDeleteConfirm ? 'text' : 'password'" v-model="delete_confirm_password" placeholder="Re-enter your password" />
            <span class="toggle-icon" @click="showDeleteConfirm = !showDeleteConfirm">{{ showDeleteConfirm ? '🙈' : '👁' }}</span>
          </div>

          <!-- Alert -->
          <div class="alert-box" v-if="deleteAlert" :class="{'success': deleteSuccess, 'error': !deleteSuccess}">
            {{ deleteAlert }}
          </div>

          <div class="modal-actions">
            <button class="btn-secondary" @click="closeDeleteAccount">Close</button>
            <button class="btn-danger" @click="submitDeleteAccount" :disabled="submittingDelete">
              <span v-if="!submittingDelete">Delete my account</span>
              <span v-else>Processing...</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
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
      showWarning: false,
      showDeleteAccount: false,
      username: null,
      email: null,
      feedbackMessage: "",
      sendingDisabled: false,
      countdown: 0,
      // change password
      current_password: "",
      new_password: "",
      confirm_password: "",
      passwordAlert: "",
      passwordSuccess: false,
      submittingPassword: false,
      showCurrentPassword: false,
      showNewPassword: false,
      showConfirmPassword: false,
      // delete account
      delete_username: "",
      delete_password: "",
      delete_confirm_password: "",
      deleteAlert: "",
      deleteSuccess: false,
      submittingDelete: false,
      showDeletePassword: false,
      showDeleteConfirm: false,
    };
  },
  created() {
    // Lấy thông tin user/email từ cookie
    const getCookie = (name) => {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    };
    this.username = getCookie("username");
    this.email = getCookie("email");
    if (!this.username) this.$router.push("/");
  },
  methods: {
        scrollTo(section) {
      // set tab đang active
      this.activeTab = section;
      // cuộn tới section có id tương ứng
      const el = document.getElementById(section);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },

    handleAction(action) { /* giữ nguyên */ },

    // Change password
    openChangePassword() { this.showChangePassword = true; },
    closeChangePassword() {
      this.showChangePassword = false;
      this.passwordAlert = "";
      this.passwordSuccess = false;
      this.current_password = "";
      this.new_password = "";
      this.confirm_password = "";
      this.showCurrentPassword = false;
      this.showNewPassword = false;
      this.showConfirmPassword = false;
    },
    async submitChangePassword() {
      this.passwordAlert = "";
      this.passwordSuccess = false;
      this.submittingPassword = true;

      try {
        const res = await axios.post(
          "http://localhost:8000/api/change-password/",
          {
            current_password: this.current_password,
            new_password: this.new_password,
            confirm_password: this.confirm_password,
          },
          {
            withCredentials: true, // gửi cookie HttpOnly
          }
        );

        this.passwordAlert = res.data.message || "Password changed successfully.";
        this.passwordSuccess = true;

        // logout và redirect sau 3s
        setTimeout(() => {
          document.cookie.split(";").forEach(c => {
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
          });
          this.$router.push("/");
          window.location.reload();
        }, 3000);
      } catch (err) {
        this.passwordAlert = err.response?.data?.error || err.response?.data?.detail || err.message;
        this.passwordSuccess = false;
      } finally {
        this.submittingPassword = false;
      }
    },

    // Warning modal
    openWarningModal() { this.showWarning = true; },
    closeWarning() { this.showWarning = false; },
    proceedDeleteAccount() { this.showWarning = false; this.showDeleteAccount = true; },

    // Delete account
    closeDeleteAccount() {
      this.showDeleteAccount = false;
      this.delete_username = "";
      this.delete_password = "";
      this.delete_confirm_password = "";
      this.deleteAlert = "";
      this.deleteSuccess = false;
      this.submittingDelete = false;
      this.showDeletePassword = false;
      this.showDeleteConfirm = false;
    },
    async submitDeleteAccount() {
      this.deleteAlert = "";
      this.deleteSuccess = false;

      if (!this.delete_username || !this.delete_password || !this.delete_confirm_password) {
        this.deleteAlert = "All fields are required.";
        return;
      }
      if (this.delete_password !== this.delete_confirm_password) {
        this.deleteAlert = "Password and confirm password do not match.";
        return;
      }

      this.submittingDelete = true;
      try {
        const res = await axios.post(
          "http://localhost:8000/api/delete-account/",
          {
            username: this.delete_username,
            password: this.delete_password,
            confirm_password: this.delete_confirm_password,
          },
          { withCredentials: true } // gửi cookie HttpOnly
        );

        this.deleteAlert = res.data.message || "Account deleted successfully.";
        this.deleteSuccess = true;

        setTimeout(() => {
          document.cookie.split(";").forEach(c => {
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
          });
          this.$router.push("/");
          window.location.reload();
        }, 3000);
      } catch (err) {
        this.deleteAlert = err.response?.data?.error || err.response?.data?.detail || err.message;
        this.deleteSuccess = false;
      } finally {
        this.submittingDelete = false;
      }
    },
        async sendFeedback() {
  if (!this.feedbackMessage.trim()) {
    alert("Please enter your feedback message.");
    return;
  }

  // nếu đang cooldown thì thoát
  if (this.sendingDisabled) return;

  // BẮT ĐẦU cooldown ngay khi click
  this.sendingDisabled = true;
  this.countdown = 8;
  const interval = setInterval(() => {
    this.countdown--;
    if (this.countdown <= 0) {
      this.sendingDisabled = false;
      clearInterval(interval);
    }
  }, 1000);

  try {
    await axios.post(
      "http://localhost:8000/api/send-feedback/",
      {
        message: this.feedbackMessage,
        email: this.email || "",
      },
      { withCredentials: true }
    );
    alert("Feedback sent successfully!");
    this.feedbackMessage = "";
  } catch (err) {
    console.error(err);
    alert(
      err.response?.data?.error ||
        err.response?.data?.detail ||
        "Failed to send feedback."
        );
      }
    }
  }
};
</script>


<style scoped src="@/assets/Profile.css"></style>