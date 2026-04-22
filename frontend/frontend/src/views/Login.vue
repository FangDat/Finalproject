<template>
  <div class="login-container">
    <div class="login-box">
      <!-- Logo -->
      <div class="logo">
        <img :src="cloudyLogo" alt="logo" class="logo-img" />
        <h1>VietCloud</h1>
      </div>

      <p class="login-title">To continue, log into VietCloud.</p>

      <div
        v-if="alertType === 'success' && alertMessage"
        class="alert-box success"
      >
        {{ alertMessage }}
      </div>

      <!-- Login bằng Gmail (placeholder) -->
      <!-- <button class="btn-gmail" type="button">LOG IN WITH GMAIL</button>

      <p class="or-text">OR</p> -->

      <!-- Form -->
      <form @submit.prevent="handleLogin">
        <input
          v-model.trim="username"
          type="text"
          placeholder="Username"
          class="input-box"
          :class="{ 'input-error': !!errors.username }"
        />
        <p v-if="errors.username" class="error-msg">{{ errors.username }}</p>

        <input
          v-model="password"
          type="password"
          placeholder="Password"
          class="input-box"
          :class="{ 'input-error': !!errors.password }"
        />
        <p v-if="errors.password" class="error-msg">{{ errors.password }}</p>

        <button class="btn-login" type="submit" :disabled="submitting">
          <span v-if="!submitting">LOG IN</span>
          <span v-else>Processing...</span>
        </button>
      </form>

      <a href="#" class="forgot-link" @click.prevent="openForgotPassword">
        Forgot Password?
      </a>


      <hr class="divider" />
            <p class="signup-text">Don't have an account</p>
      <router-link to="/signup" class="btn-signup">Sign up now!</router-link>
    </div>
  </div>
  <!-- ================= FORGOT PASSWORD MODAL ================= -->
  <transition name="fade">
    <div v-if="showForgotPassword" class="overlay">
      <div class="modal">
        <h2>Forgot Password</h2>
        <p class="note">
          Enter your registered email to reset your password.
        </p>

        <!-- STEP 1: Email -->
        <div v-if="forgotStep === 1" class="form-group email-group">
          <label>Email</label>
         <input
          v-model.trim="forgotEmail"
          type="email"
          placeholder="Enter your email"
          required
          :class="{ 'input-error': !!forgotErrors.email }"
        />
        <p v-if="forgotErrors.email" class="error-msg">
          {{ forgotErrors.email }}
        </p>
        </div>

        <!-- STEP 3: New password -->
        <div v-if="forgotStep === 3">
          <div class="form-group password-wrapper">
            <label>New password</label>
            <input
              :type="showForgotPasswordText ? 'text' : 'password'"
              v-model="forgotNewPassword"
              placeholder="Enter new password"
            />
            <span class="toggle-icon" @click="showForgotPasswordText = !showForgotPasswordText">
              {{ showForgotPasswordText ? '🚫' : '👁' }}
            </span>
          </div>

          <div class="form-group password-wrapper">
            <label>Confirm password</label>
            <input
              :type="showForgotPasswordText ? 'text' : 'password'"
              v-model="forgotConfirmPassword"
              placeholder="Confirm new password"
            />
             <span
              class="toggle-icon"
              @click="showForgotPasswordText = !showForgotPasswordText"
            >
              {{ showForgotPasswordText ? '🚫' : '👁' }}
            </span>
          </div>
        </div>

        <!-- Alert -->
        <div
          class="alert-box"
          v-if="forgotAlert"
          :class="{ success: forgotSuccess, error: !forgotSuccess }"
        >
          {{ forgotAlert }}
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="closeForgotPassword">Close</button>
          <button class="btn-primary" @click="handleForgotPassword" :disabled="forgotLoading">
            <span v-if="!forgotLoading">
              {{ forgotStep === 1 ? 'Send OTP' : 'Reset password' }}
            </span>
            <span v-else>Processing...</span>
          </button>
        </div>
      </div>
    </div>
  </transition>

  <!-- ================= OTP MODAL ================= -->
  <div v-if="showForgotOtp" class="otp-modal-overlay">
    <div class="otp-modal">
      <h2>Enter verification code</h2>

      <div class="otp-inputs" ref="forgotOtpInputs">
        <input
          v-for="(digit, index) in forgotOtpDigits"
          :key="index"
          v-model="forgotOtpDigits[index]"
          maxlength="1"
          @input="focusNextForgot(index)"
          @keydown.backspace="focusPrevForgot(index, $event)"
        />
      </div>

      <button class="btn-verify" @click="verifyForgotOtp" :disabled="verifyingForgotOtp">
        Verify
      </button>

      <p class="resend-text">
        Didn’t receive code?
        <span v-if="resendTimer > 0">Resend in {{ resendTimer }}s</span>
        <span v-else class="resend-link" @click="resendForgotOtp">
          Resend code
        </span>
      </p>

      <p class="otp-error" v-if="forgotOtpError">{{ forgotOtpError }}</p>
    </div>
  </div>
</template>

<script>
import "../assets/Login.css";
import apiClient from "@/services/apiClient";
import Cookies from "js-cookie";
import cloudyLogo from "@/assets/cloudy.png";

export default {
  name: "Login",
  data() {
    return {
      username: "",
      password: "",
      submitting: false,
      cloudyLogo,

      // UI state
      alertMessage: "",
      alertType: "info", // success | error | warning
      // forgotEmailError: "",
      // field errors
      forgotErrors: {
        email: "",
      },
      errors: {
        username: "",
        password: "",
      },
      // ===== Forgot Password =====
      showForgotPassword: false,
      forgotStep: 1,
      forgotEmail: "",
      forgotNewPassword: "",
      forgotConfirmPassword: "",
      forgotAlert: "",
      forgotSuccess: false,
      forgotLoading: false,
      showForgotPasswordText: false,

      // OTP
      showForgotOtp: false,
      forgotOtpDigits: ["", "", "", "", "", ""],
      forgotOtpError: null,
      verifyingForgotOtp: false,
      resendTimer: 600,
      otpInterval: null,
    };
  },
  methods: {
    resetErrors() {
      this.errors = { username: "", password: "" };
      this.alertMessage = "";
      this.alertType = "info";
    },
    openForgotPassword() {
      this.showForgotPassword = true;
      this.forgotStep = 1;
      this.forgotErrors = { email: "" };
    },

    closeForgotPassword() {
      this.showForgotPassword = false;
      this.showForgotOtp = false;
      this.forgotEmail = "";
      this.forgotNewPassword = "";
      this.forgotConfirmPassword = "";
      this.forgotAlert = "";
      this.forgotOtpDigits = ["", "", "", "", "", ""];
      this.forgotOtpError = null;
    },

    async handleForgotPassword() {
      this.forgotAlert = "";
      this.forgotErrors = { email: "" };

      // ===== FRONTEND VALIDATION =====
      if (this.forgotStep === 1) {
        if (!this.forgotEmail) {
          this.forgotErrors.email = "Please enter your email.";
          return;
        }

        const emailInput = document.createElement("input");
        emailInput.type = "email";
        emailInput.value = this.forgotEmail;

        if (!emailInput.checkValidity()) {
          this.forgotErrors.email = "Please enter a valid email address.";
          return;
        }
      }

      this.forgotLoading = true;

      try {
        // STEP 1: SEND OTP
        if (this.forgotStep === 1) {
          await apiClient.post("/api/forgot-password/send-otp/", {
            email: this.forgotEmail,
          });

          this.showForgotPassword = false;
          this.showForgotOtp = true;
          this.startResendCountdown();
        }

        // STEP 3: RESET PASSWORD
        else {
          if (this.forgotNewPassword !== this.forgotConfirmPassword) {
            this.forgotAlert = "Passwords do not match.";
            this.forgotSuccess = false;
            return;
          }

          await apiClient.post("/api/forgot-password/reset/", {
            email: this.forgotEmail,
            new_password: this.forgotNewPassword,
            confirm_password: this.forgotConfirmPassword,
          });

          this.forgotAlert = "Password reset successfully.";
          this.forgotSuccess = true;

          setTimeout(() => this.closeForgotPassword(), 2000);
        }
      } catch (err) {
        if (
          this.forgotStep === 1 &&
          err.response?.status === 400 &&
          err.response.data?.error
        ) {
          this.forgotErrors.email = err.response.data.error;
          return;
        }

        this.forgotAlert =
          err.response?.data?.error || "Action failed.";
        this.forgotSuccess = false;
      } finally {
        this.forgotLoading = false;
      }
    },

    async verifyForgotOtp() {
      this.verifyingForgotOtp = true;
      this.forgotOtpError = null;

      const otp = this.forgotOtpDigits.join("");
      if (otp.length !== 6) {
        this.forgotOtpError = "Please enter all 6 digits.";
        this.verifyingForgotOtp = false;
        return;
      }

      try {
        await apiClient.post("/api/forgot-password/verify-otp/", {
          email: this.forgotEmail,
          otp,
        });

        this.showForgotOtp = false;
        this.showForgotPassword = true;
        this.forgotStep = 3;
      } catch (err) {
        this.forgotOtpError =
          err.response?.data?.error || "Invalid or expired OTP.";
      } finally {
        this.verifyingForgotOtp = false;
      }
    },

    startResendCountdown() {
      this.resendTimer = 600;
      if (this.otpInterval) clearInterval(this.otpInterval);
      this.otpInterval = setInterval(() => {
        if (this.resendTimer > 0) this.resendTimer--;
        else clearInterval(this.otpInterval);
      }, 1000);
    },

    async resendForgotOtp() {
      await apiClient.post("/api/forgot-password/resend-otp/", {
        email: this.forgotEmail,
      });
      this.startResendCountdown();
    },

    focusNextForgot(index) {
      if (
        this.forgotOtpDigits[index] &&
        index < this.forgotOtpDigits.length - 1
      ) {
        const inputs = this.$refs.forgotOtpInputs?.querySelectorAll("input");
        inputs?.[index + 1]?.focus();
      }
    },

    focusPrevForgot(index, event) {
      if (
        event.key === "Backspace" &&
        !this.forgotOtpDigits[index] &&
        index > 0
      ) {
        const inputs = this.$refs.forgotOtpInputs?.querySelectorAll("input");
        inputs?.[index - 1]?.focus();
      }
    },


    async handleLogin() {
      this.resetErrors();

      if (!this.username || !this.password) {
        if (!this.username)
          this.errors.username = "Please enter your username.";
        if (!this.password)
          this.errors.password = "Please enter your password.";

        this.alertMessage = "Please fill in all required fields.";
        this.alertType = "warning";
        return;
      }

      this.submitting = true;

      try {
        const payload = {
          username: this.username,
          password: this.password,
        };

        // 🔥 DÙNG apiClient (cookie tự gửi)
        const res = await apiClient.post("/api/login/", payload);

        const user = res.data?.user || this.username;
        const email = res.data?.email || "";
        const role = res.data?.role || "user";

        Cookies.set("username", user, { expires: 7 });
        Cookies.set("email", email, { expires: 7 });
        Cookies.set("role", role, { expires: 7 });

        this.alertMessage = "Login successful! Redirecting...";
        this.alertType = "success";

        setTimeout(() => {
          if (role === "admin") {
            this.$router.push("/admin");
          } else {
            this.$router.push("/");
          }
        }, 800);
      } catch (err) {
        if (err.response) {
          const { status, data } = err.response;

          if (data?.username || data?.password) {
            if (data.username?.length)
              this.errors.username = data.username[0];
            if (data.password?.length)
              this.errors.password = data.password[0];

            this.alertMessage =
              data.username?.[0] ||
              data.password?.[0] ||
              "Login failed.";
            this.alertType = "error";
          } else if (status === 404) {
            this.errors.username = "User not found.";
            this.alertMessage = "User not found.";
            this.alertType = "warning";
          } else if (status === 400) {
            this.errors.password = "Incorrect password.";
            this.alertMessage = "Incorrect password.";
            this.alertType = "warning";
          } else if (status === 403) {
            // 👇 hiển thị giống "Please enter your password."
            this.errors.password =
              "Your account has been temporarily suspended. Please contact support.";
          }
        } else {
          this.alertMessage =
            "Cannot connect to server. Please try again.";
          this.alertType = "error";
        }
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>
