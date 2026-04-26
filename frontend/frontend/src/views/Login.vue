<template>
  <div class="login-container">
    <div class="login-box">
      <!-- Logo -->
      <div class="logo">
        <img src="@/assets/cloudy.png" alt="logo" class="logo-img" />
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
      <form @submit.prevent="handleLogin">  <!-- Submit form and prevent page reload, call handleLogin -->
        <input
          v-model.trim="username" 
          type="text"
          placeholder="Username"
          class="input-box"
          :class="{ 'input-error': !!errors.username }"
        />
        <p v-if="errors.username" class="error-msg">{{ errors.username }}</p> <!-- Show error message if exists -->

        <input
          v-model="password"
          type="password"
          placeholder="Password"
          class="input-box"
          :class="{ 'input-error': !!errors.password }" 
        />
        <p v-if="errors.password" class="error-msg">{{ errors.password }}</p> <!-- Show error message if exists -->

        <button class="btn-login" type="submit" :disabled="submitting"> <!-- Disable button when submitting -->
          <span v-if="!submitting">LOG IN</span>  <!-- Show normal text -->
          <span v-else>Processing...</span> <!-- Show loading text -->
        </button>
      </form>

      <a href="#" class="forgot-link" @click.prevent="openForgotPassword">
        Forgot Password?
      </a>


      <hr class="divider" />
            <p class="signup-text">Don't have an account</p>
      <router-link to="/signup" class="btn-signup">Sign up for VietCloud</router-link>
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

export default {
  name: "Login",
  data() {
    return {
      username: "",
      password: "",
      submitting: false,

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

    async handleForgotPassword() {  // Handle forgot password flow
      this.forgotAlert = "";  // Clear alert
      this.forgotErrors = { email: "" };  // Reset email error

      // ===== FRONTEND VALIDATION =====
      if (this.forgotStep === 1) {
        if (!this.forgotEmail) {
          this.forgotErrors.email = "Please enter your email.";
          return;
        }

        const emailInput = document.createElement("input"); // Create temp input
        emailInput.type = "email";  // Set type email
        emailInput.value = this.forgotEmail;  // Assign value

        if (!emailInput.checkValidity()) {  // Validate email format
          this.forgotErrors.email = "Please enter a valid email address.";
          return;
        }
      }

      this.forgotLoading = true;  // Enable loading

      try {
        // STEP 1: SEND OTP
        if (this.forgotStep === 1) {  // Send OTP step
          await apiClient.post("/api/forgot-password/send-otp/", {  
            email: this.forgotEmail,  // Send email
          });

          this.showForgotPassword = false;  // Hide modal
          this.showForgotOtp = true;  // Show OTP modal
          this.startResendCountdown();  // Start timer
        }

        // STEP 3: RESET PASSWORD
        else {
          if (this.forgotNewPassword !== this.forgotConfirmPassword) {  // Check match
            this.forgotAlert = "Passwords do not match."; 
            this.forgotSuccess = false; 
            return;
          }

          await apiClient.post("/api/forgot-password/reset/", { // Call API
            email: this.forgotEmail,
            new_password: this.forgotNewPassword,
            confirm_password: this.forgotConfirmPassword,
          });

          this.forgotAlert = "Password reset successfully.";  // Success message
          this.forgotSuccess = true;  // Mark success

          setTimeout(() => this.closeForgotPassword(), 2000); // Close modal
        }
      } catch (err) { // Handle error
        if (
          this.forgotStep === 1 &&
          err.response?.status === 400 &&
          err.response.data?.error  // Show error related to email if exists
        ) {
          this.forgotErrors.email = err.response.data.error;  // Disable loading
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


    async handleLogin() { // Main function to process login
      this.resetErrors(); // Clear previous errors and alerts

      if (!this.username || !this.password) { // Check if fields are empty
        if (!this.username) // If username missing
          this.errors.username = "Please enter your username."; // Set username error
        if (!this.password)
          this.errors.password = "Please enter your password.";

        this.alertMessage = "Please fill in all required fields.";  // Show warning message
        this.alertType = "warning";
        return; // Stop execution
      }

      this.submitting = true; // Enable loading state

      try {
        const payload = { // Prepare request data
          username: this.username,
          password: this.password,
        };


        const res = await apiClient.post("/api/login/", payload); // Send login request

        const user = res.data?.user || this.username; 
        const email = res.data?.email || "";
        const role = res.data?.role || "user";

        Cookies.set("username", user, { expires: 7 });  // Save username in cookie
        Cookies.set("email", email, { expires: 7 });
        Cookies.set("role", role, { expires: 7 });

        this.alertMessage = "Login successful! Redirecting..."; // Show success message
        this.alertType = "success";

        setTimeout(() => {  // Delay redirect
          if (role === "admin") { // If admin
            this.$router.push("/admin");  // Go to admin page
          } else {
            this.$router.push("/"); // Go to home page
          }
        }, 800);
      } catch (err) {
        if (err.response) {
          const { status, data } = err.response;  // Extract status and data

          if (data?.username || data?.password) { // Validation errors
            if (data.username?.length)
              this.errors.username = data.username[0];  // Set username error
            if (data.password?.length)
              this.errors.password = data.password[0];  // Set password error

            this.alertMessage =
              data.username?.[0] ||
              data.password?.[0] ||
              "Login failed.";  // Show message
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
            this.errors.password =
              "Your account has been temporarily suspended. Please contact support."; // Show suspension message
          }
        } else {
          this.alertMessage =
            "Cannot connect to server. Please try again.";
          this.alertType = "error";
        }
      } finally {
        this.submitting = false;  // Disable loading state
      }
    },
  },
};
</script>
