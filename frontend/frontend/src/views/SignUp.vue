<template>
  <div class="signup-container">
    <div class="signup-card">
      <!-- Logo -->
      <div class="logo-section">
        <img src="@/assets/cloudy.png" alt="VietCloud" class="logo" />
        <h2>VietCloud</h2>
      </div>

      <!-- Title -->
      <h3 class="signup-title">
        Sign up now to experience exclusive features from VietCloud
      </h3>

      <!-- Sign in link -->
      <p class="signin-text">
        Already have an account?
        <router-link to="/login" class="signin-link">Log in</router-link>
      </p>

      <div
      v-if="alertType === 'success' && alertMessage"
      class="alert-box success"
    >
      {{ alertMessage }}
    </div>

      <!-- Form -->
      <form class="signup-form" @submit.prevent="handleSignup">
        <label>Username</label>
        <input
          v-model.trim="username"
          type="text"
          placeholder="Enter your username"
          :class="{ 'input-error': !!errors.username }"
        />
        <p v-if="errors.username" class="error-msg">{{ errors.username }}</p>

        <label>Email</label>
        <input
          v-model.trim="email"
          type="email"
          placeholder="Enter your email"
          :class="{ 'input-error': !!errors.email }"
        />
        <p v-if="errors.email" class="error-msg">{{ errors.email }}</p>

        <label>Password</label>
        <input
          v-model="password"
          type="password"
          placeholder="Enter your password"
          :class="{ 'input-error': !!errors.password }"
        />
        <p v-if="errors.password" class="error-msg">{{ errors.password }}</p>

        <label>Confirm password</label>
        <input
          v-model="confirmPassword"
          type="password"
          placeholder="Re-enter your password"
          :class="{ 'input-error': !!errors.confirmPassword }"
        />
        <p v-if="errors.confirmPassword" class="error-msg">{{ errors.confirmPassword }}</p>

        <button type="submit" class="btn-signup" :disabled="submitting">
          <span class="lock-icon">🔒</span>
          <span v-if="!submitting">Sign up</span>
          <span v-else>Processing...</span>
        </button>
      </form>

      <!-- Terms -->
      <p class="agreement-text">
        By clicking the "Sign up" button, you agree to the
        <router-link to="/terms" class="terms-link">Terms of Use</router-link>.
      </p>
    </div>

    <!-- OTP Modal -->
    <div v-if="showOtpModal" class="otp-modal-overlay">
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
        <button class="btn-verify" @click="verifyOtp" :disabled="verifying">
          <span v-if="!verifying">Verify</span>
          <span v-else>Verifying...</span>
        </button>
        <p class="resend-text">
          Didn’t receive code?
          <span v-if="resendTimer > 0">
            Resend in {{ resendTimer }}s
          </span>
          <span v-else class="resend-link" @click="resendOtp">
            Resend code
          </span>
        </p>
        <p class="otp-error" v-if="otpError">{{ otpError }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import {
  signup,
  verifySignupOtp,
  resendSignupOtp,
} from "@/services/authService";

import Cookies from "js-cookie";
function cleanCookieValue(value) {
  if (!value) return "";
  try {
    // Nếu giá trị dạng JSON chuỗi, parse thử
    const parsed = JSON.parse(value);
    if (typeof parsed === "string") return parsed;
  } catch (_) {}
  // Xoá ngoặc kép/thừa khoảng trắng
  return value.replace(/^["']+|["']+$/g, "").trim();
}

export default {
  name: "SignUp",
  data() {
    return {
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
      submitting: false,
      verifying: false,

      alertMessage: "",
      alertType: "info",

      errors: {
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
      },

      // OTP modal states
      showOtpModal: false,
      otpDigits: ["", "", "", "", "", ""],
      resendTimer: 600,
      otpError: null,
      otpInterval: null,
    };
  },
  mounted() {
    const rawEmail = Cookies.get("email");
    const cleanEmail = cleanCookieValue(rawEmail);
    if (cleanEmail && cleanEmail !== rawEmail) {
      Cookies.set("email", cleanEmail, { path: "/" });
    }
  },

  methods: {
    resetErrors() {
      this.errors = { username: "", email: "", password: "", confirmPassword: "" };
      this.alertMessage = "";
      this.alertType = "info";
    },

    async handleSignup() {
      this.resetErrors();

      if (!this.username || !this.email || !this.password || !this.confirmPassword) {
        if (!this.username) this.errors.username = "Please enter your username.";
        if (!this.email) this.errors.email = "Please enter your email.";
        if (!this.password) this.errors.password = "Please enter your password.";
        if (!this.confirmPassword)
          this.errors.confirmPassword = "Please confirm your password.";
        return;
      }

      if (this.password !== this.confirmPassword) {
        this.errors.confirmPassword = "Passwords do not match.";
        return;
      }

      if (this.password.length < 8) {
        this.errors.password = "Password must be at least 8 characters long.";
        return;
      }

      this.submitting = true;

      try {
        await signup({
          username: this.username,
          email: this.email,
          password: this.password,
        });

        this.showOtpModal = true;
        this.startResendCountdown();
      } catch (err) {
        this.handleSignupError(err);
      } finally {
        this.submitting = false;
      }
    },

    handleSignupError(err) {
      const status = err?.response?.status;
      const data = err?.response?.data;

      if (status === 400 && data) {
        if (data.email?.[0]?.toLowerCase().includes("already")) {
          this.errors.email = "This email is already in use!";
        } else if (data.username?.[0]?.toLowerCase().includes("already")) {
          this.errors.username = "Username already exists!";
        } else {
          this.alertMessage = "Signup failed. Please check your inputs.";
          this.alertType = "error";
        }
      } else {
        this.alertMessage = "Signup failed. Please try again.";
        this.alertType = "error";
      }
    },

    async verifyOtp() {
      this.verifying = true;
      this.otpError = null;

      const otpCode = this.otpDigits.join("");
      if (otpCode.length !== 6) {
        this.otpError = "Please enter all 6 digits.";
        this.verifying = false;
        return;
      }

      try {
        await verifySignupOtp(this.email, otpCode);

        this.showOtpModal = false;
        this.alertMessage = "Verification successful! Redirecting...";
        this.alertType = "success";
        setTimeout(() => this.$router.push("/billing"), 3500);
      } catch (err) {
          this.otpError =
            err?.response?.data?.message ||
            "Invalid or expired OTP. Please try again.";
        }
      finally {
        this.verifying = false;
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

    startResendCountdown() {
      this.resendTimer = 60;
      if (this.otpInterval) clearInterval(this.otpInterval);
      this.otpInterval = setInterval(() => {
        if (this.resendTimer > 0) this.resendTimer--;
        else clearInterval(this.otpInterval);
      }, 1000);
    },

    async resendOtp() {
      try {
        await resendSignupOtp(this.email);
        this.resendTimer = 600;
        this.startResendCountdown();
      } catch (err) {
        this.otpError = "Failed to resend OTP. Please try again.";
      }
    },
  },
  beforeUnmount() {
    if (this.otpInterval) clearInterval(this.otpInterval);
  },
};
</script>
<style scoped src="@/assets/Signup.css"></style>