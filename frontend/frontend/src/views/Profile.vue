<template>
  <div class="profile-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 VietCloud</router-link>
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
            <span class="change-link" @click="openChangeEmail">change email</span>
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

      <!-- Billing & Invoices -->
      <section class="card" id="subscriptions">
        <h2 class="sub-title">Billing history</h2>

        <table class="invoice-table" v-if="invoices.length">
          <thead>
            <tr>
              <th>Invoice ID</th>
              <th>Date</th>
              <th>Amount</th>
              <th></th>
            </tr>
          </thead>
            <tbody is="transition-group" name="invoice">
              <tr
                v-for="inv in visibleInvoices"
                :key="inv.invoice_number"
              >
                <td>Invoice #{{ inv.invoice_number }}</td>
                <td>{{ inv.created_at }}</td>
                <td>{{ inv.amount }}</td>
                <td>
                  <button class="btn-link" @click="openInvoice(inv.hosted_invoice_url)">
                    View
                  </button>
                </td>
              </tr>
            </tbody>
        </table>

        <p v-if="!invoices.length" class="note">
          No invoices found.
        </p>

        <div class="card-actions" v-if="invoices.length > 3">
          <button class="show-more-btn" @click="toggleInvoices">
            {{ showAllInvoices ? "− Show less" : "+ Show more" }}
          </button>
        </div>
      </section>

      <!-- Premium -->
      <section class="card">
        <h2 class="sub-title">Premium</h2>

        <!-- ✅ PREMIUM ACTIVE -->
        <p v-if="is_premium">
          🎉 Your <strong>VietCloud Premium</strong> subscription is active.<br />
          You have <strong>{{ premiumDaysLeft }}</strong> day<span v-if="premiumDaysLeft > 1">s</span> remaining.
          Enjoy all exclusive features without limits.
        </p>

        <!-- ❌ PREMIUM INACTIVE -->
        <p v-else>
          🚫 Your <strong>VietCloud Premium</strong> subscription is not active.<br />
          Please click the <strong>"Renew"</strong> button to purchase and unlock premium features.
        </p>

        <div class="card-actions">
          <button
            class="btn-primary"
            :disabled="is_premium"
            @click="goToBilling"
          >
            {{ is_premium ? "Premium Active" : "Renew" }}
          </button>
        </div>
      </section>

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
    <!-- Overlay + Change Email Modal -->
    <transition name="fade">
      <div v-if="showChangeEmail" class="overlay">
        <div class="modal">
          <h2>Change Email</h2>

          <!-- STEP 1: Verify password -->
          <div v-if="changeEmailStep === 1" class="form-group password-wrapper">
            <label>Current password</label>
            <input
              :type="showEmailPassword ? 'text' : 'password'"
              v-model="email_password"
              placeholder="Enter your password"
            />
            <span class="toggle-icon" @click="showEmailPassword = !showEmailPassword">
              {{ showEmailPassword ? '🙈' : '👁' }}
            </span>
          </div>

          <!-- STEP 2: New email -->
          <div v-if="changeEmailStep === 2" class="form-group">
            <label>New email</label>
            <input
              type="email"
              v-model.trim="new_email"
              placeholder="Enter new email"
            />
          </div>

          <!-- Alert -->
          <div class="alert-box" v-if="changeEmailAlert" :class="{'success': changeEmailSuccess, 'error': !changeEmailSuccess}">
            {{ changeEmailAlert }}
          </div>

          <div class="modal-actions">
            <button class="btn-secondary" @click="closeChangeEmail">Close</button>
            <button class="btn-primary" @click="handleChangeEmail" :disabled="changeEmailLoading">
              <span v-if="!changeEmailLoading">
                {{ changeEmailStep === 1 ? 'Verify' : 'Send OTP' }}
              </span>
              <span v-else>Processing...</span>
            </button>
          </div>
        </div>
      </div>
    </transition>
    <div v-if="showChangeEmailOtp" class="otp-modal-overlay">
      <div class="otp-modal">
        <h2>Please enter the verification code sent to your email</h2>

        <div class="otp-inputs">
          <input
            v-for="(digit, index) in otpDigits"
            :key="index"
            v-model="otpDigits[index]"
            maxlength="1"
            @input="focusNext(index)"
            @keydown.backspace="focusPrev(index, $event)"
          />
        </div>

        <button class="btn-verify" @click="verifyChangeEmailOtp" :disabled="verifyingOtp">
          <span v-if="!verifyingOtp">Verify</span>
          <span v-else>Verifying...</span>
        </button>

        <p class="resend-text">
          Didn’t receive code?
          <span v-if="resendTimer > 0">Resend in {{ resendTimer }}s</span>
          <span v-else class="resend-link" @click="resendChangeEmailOtp">
            Resend code
          </span>
        </p>

        <p class="otp-error" v-if="otpError">{{ otpError }}</p>
      </div>
    </div>



    <!-- Overlay + Change Password Modal -->
    <transition name="fade">
      <div v-if="showChangePassword" class="overlay">
        <div class="modal">
          <h2>Change Password</h2>
          <p class="note">
            Password needs to be at least <b>8 characters long</b> 
            <!-- Password needs to be at least <b>8 characters long</b> and contain at least one <b>lowercase letter</b>, one <b>uppercase letter</b>, and a <b>number</b>. -->
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

    <!-- Overlay + Popup notification -->
    <transition name="fade">
      <div v-if="showPopup" class="overlay">
        <div class="popup-box" :class="popupSuccess ? 'popup-success' : 'popup-error'">
          <h3>{{ popupMessage }}</h3>
          <button class="btn-primary" @click="showPopup=false">OK</button>
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
      invoices: [],
      showAllInvoices: false,
      is_premium: false,
      premium_expires_at_ts: null,
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
      // popup
      showPopup: false,
      popupMessage: "",
      popupSuccess: true,
      // ===== Change Email =====
      showChangeEmail: false,
      changeEmailStep: 1,
      email_password: "",
      new_email: "",
      changeEmailAlert: "",
      changeEmailSuccess: false,
      changeEmailLoading: false,
      showEmailPassword: false,

      // OTP
      showChangeEmailOtp: false,
      otpDigits: ["", "", "", "", "", ""],
      resendTimer: 60,
      otpError: null,
      otpInterval: null,
      verifyingOtp: false,
    };
  },
  created() {
    const getCookie = (name) => {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    };
    this.username = getCookie("username");
    this.email = getCookie("email");
    if (!this.username) this.$router.push("/");
    this.fetchInvoices();
    this.fetchUserInfo();
  },
      computed: {
        visibleInvoices() {
          return this.showAllInvoices
            ? this.invoices
            : this.invoices.slice(0, 3);
        },
        premiumDaysLeft() {
      if (!this.is_premium || !this.premium_expires_at_ts) return 0;

      // 🔥 ÉP KIỂU LẦN CUỐI – HARD SAFETY
      let expiresTs = Number(this.premium_expires_at_ts);

      if (!Number.isFinite(expiresTs)) return 0;

      // ms → s
      if (expiresTs > 1e12) {
        expiresTs = Math.floor(expiresTs / 1000);
      }

      const nowTs = Math.floor(Date.now() / 1000);
      const diffSeconds = expiresTs - nowTs;

      if (diffSeconds <= 0) return 0;

      return Math.max(1, Math.ceil(diffSeconds / 86400));
    },
  },
  methods: {
    scrollTo(section) {
      this.activeTab = section;
      const el = document.getElementById(section);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    },
    goToBilling() {
      window.location.href = "http://localhost:8080/#/Billing";
    },

    handleAction(action) { /* giữ nguyên */ },
      openChangeEmail() {
      this.showChangeEmail = true;
      this.changeEmailStep = 1;
    },

    closeChangeEmail() {
    this.showChangeEmail = false;
    this.email_password = "";
    this.new_email = "";
    this.changeEmailAlert = "";
    this.changeEmailSuccess = false;
    this.showEmailPassword = false;

    // reset OTP state nếu user đóng giữa chừng
    this.otpDigits = ["", "", "", "", "", ""];
    this.otpError = null;
    
  },

    async fetchUserInfo() {
      try {
        const res = await axios.get(
          "http://localhost:8000/api/user-info/",
          { withCredentials: true }
        );

        this.is_premium = !!res.data.is_premium;

        // 🔥 FIX CỐT LÕI: ép Number
        this.premium_expires_at_ts = res.data.premium_expires_at_ts
          ? Number(res.data.premium_expires_at_ts)
          : null;

      } catch (err) {
        this.is_premium = false;
        this.premium_expires_at_ts = null;
      }
    },

    async handleChangeEmail() {
    this.changeEmailAlert = "";
    this.changeEmailLoading = true;

    try {
      if (this.changeEmailStep === 1) {
        await axios.post(
          "http://localhost:8000/api/change-email/verify-password/",
          { password: this.email_password },
          { withCredentials: true }
        );
        this.changeEmailStep = 2;
      } else {
        await axios.post(
          "http://localhost:8000/api/change-email/send-otp/",
          { new_email: this.new_email },
          { withCredentials: true }
        );
        this.showChangeEmail = false;
        this.showChangeEmailOtp = true;
        this.startResendCountdown();
      }
    } catch (err) {
      this.changeEmailAlert = err.response?.data?.error || "Action failed.";
      this.changeEmailSuccess = false;
    } finally {
      this.changeEmailLoading = false;
    }
  },
   async verifyChangeEmailOtp() {
    this.verifyingOtp = true;
    this.otpError = null;

    const otpCode = this.otpDigits.join("");
    if (otpCode.length !== 6) {
      this.otpError = "Please enter all 6 digits.";
      this.verifyingOtp = false;
      return;
    }

    try {
      await axios.post(
        "http://localhost:8000/api/change-email/verify-otp/",
        { otp: otpCode },
        { withCredentials: true }
      );

      // ✅ UX giống Change Password
      this.showChangeEmailOtp = false;
      this.popupMessage = "Email changed successfully.";
      this.popupSuccess = true;
      this.showPopup = true;

      // ⏳ Logout giống hệt Change Password
      setTimeout(() => {
        document.cookie.split(";").forEach(c => {
          document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });

        // reset state (tránh bug sau reload)
        this.otpDigits = ["", "", "", "", "", ""];
        this.resendTimer = 60;
        this.otpError = null;

        this.$router.push("/");
        window.location.reload();
      }, 3000);

    } catch (err) {
      this.otpError =
        err.response?.data?.error ||
        err.response?.data?.message ||
        "Invalid or expired OTP.";
    } finally {
      this.verifyingOtp = false;
    }
  },
  
  startResendCountdown() {
  this.resendTimer = 60;
  if (this.otpInterval) clearInterval(this.otpInterval);
  this.otpInterval = setInterval(() => {
    if (this.resendTimer > 0) this.resendTimer--;
    else clearInterval(this.otpInterval);
  }, 1000);
},

  async resendChangeEmailOtp() {
    try {
      await axios.post(
        "http://localhost:8000/api/change-email/resend-otp/",
        {},
        { withCredentials: true }
      );
      this.startResendCountdown();
    } catch {
      this.otpError = "Failed to resend OTP.";
    }
  },
focusNext(index) {
  if (this.otpDigits[index].length === 1 && index < 5) {
    this.$el.querySelectorAll(".otp-inputs input")[index + 1].focus();
  }
},

focusPrev(index, event) {
  if (!this.otpDigits[index] && index > 0 && event.key === "Backspace") {
    this.$el.querySelectorAll(".otp-inputs input")[index - 1].focus();
  }
},

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
            withCredentials: true,
          }
        );

        this.passwordAlert = res.data.message || "Password changed successfully.";
        this.passwordSuccess = true;

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

    openWarningModal() { this.showWarning = true; },
    closeWarning() { this.showWarning = false; },
    proceedDeleteAccount() { this.showWarning = false; this.showDeleteAccount = true; },

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
          { withCredentials: true }
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
        this.popupMessage = "Please enter your feedback message.";
        this.popupSuccess = false;
        this.showPopup = true;
        return;
      }
      if (this.sendingDisabled) return;

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
        this.popupMessage = "Feedback sent successfully! Support will respond to your email soon.";
        this.popupSuccess = true;
        this.showPopup = true;
        this.feedbackMessage = "";
      } catch (err) {
        console.error(err);
        this.popupMessage = err.response?.data?.error || err.response?.data?.detail || "Failed to send feedback.";
        this.popupSuccess = false;
        this.showPopup = true;
      }
    },
    async fetchInvoices() {
      try {
        const res = await axios.get(
          "http://localhost:8000/api/stripe/invoices/",
          { withCredentials: true }
        );
        this.invoices = res.data || [];
      } catch (err) {
        console.error("Failed to load invoices", err);
        this.invoices = [];
      }
    },

    toggleInvoices() {
      this.showAllInvoices = !this.showAllInvoices;
    },

    openInvoice(url) {
      if (!url) return;
      window.open(url, "_blank", "noopener");
    },
  }
};
</script>

<style scoped src="@/assets/Profile.css"></style>
