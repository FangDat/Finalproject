<template>
  <div class="login-container">
    <div class="login-box">
      <!-- Logo -->
      <div class="logo">
        <img src="@/assets/cloudy.png" alt="logo" class="logo-img" />
        <h1>VietCloud</h1>
      </div>

      <p class="login-title">To continue, log into VietCloud.</p>

      <!-- Alert box giống SignUp -->
      <div v-if="alertMessage" :class="['alert-box', alertType]">
        {{ alertMessage }}
      </div>

      <!-- Login bằng Gmail (placeholder) -->
      <button class="btn-gmail" type="button">LOG IN WITH GMAIL</button>

      <p class="or-text">OR</p>

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

      <a href="#" class="forgot-link">Forgot Password?</a>

      <hr class="divider" />
      <router-link to="/signup" class="btn-signup">Sign up for VietCloud</router-link>
      <p class="signup-text">Don't have an account</p>
    </div>
  </div>
</template>

<script>
import "../assets/Login.css";
import axios from "axios";
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

      // field errors
      errors: {
        username: "",
        password: "",
      },
    };
  },
  methods: {
    resetErrors() {
      this.errors = { username: "", password: "" };
      this.alertMessage = "";
      this.alertType = "info";
    },
    async handleLogin() {
      this.resetErrors();

      // Validate cơ bản
      if (!this.username || !this.password) {
        if (!this.username) this.errors.username = "Please enter your username.";
        if (!this.password) this.errors.password = "Please enter your password.";
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

        // Gửi request login với cookie tự động kèm theo
        const res = await axios.post(
          "http://localhost:8000/api/login/",
          payload,
          {
            headers: { "Content-Type": "application/json" },
            withCredentials: true, // bắt buộc để gửi cookie HttpOnly
          }
        );

        // Backend trả về thông tin user (nếu cần)
        const user = res.data?.user || this.username;
        const email = res.data?.email || "";

        // Chỉ lưu vào cookie, không lưu localStorage
        Cookies.set("username", user, { expires: 7 });
        Cookies.set("email", email, { expires: 7 });

        this.alertMessage = "Login successful! Redirecting...";
        this.alertType = "success";

        // Điều hướng về Home
        setTimeout(() => {
          this.$router.push("/");
        }, 800);
      } catch (err) {
        if (err.response) {
          const { status, data } = err.response;
          if (data && typeof data === "object" && (data.username || data.password)) {
            if (data.username?.length) this.errors.username = data.username[0];
            if (data.password?.length) this.errors.password = data.password[0];
            this.alertMessage =
              [data.username?.[0], data.password?.[0]].filter(Boolean).join(" ") ||
              "Login failed.";
            this.alertType = "error";
          } else if (status === 404 && data?.error?.toLowerCase().includes("user not found")) {
            this.errors.username = "User not found.";
            this.alertMessage = "User not found.";
            this.alertType = "warning";
          } else if (status === 400 && data?.error?.toLowerCase().includes("invalid password")) {
            this.errors.password = "Incorrect password.";
            this.alertMessage = "Incorrect password.";
            this.alertType = "warning";
          } else {
            this.alertMessage = data?.error || "Login failed. Please try again.";
            this.alertType = "error";
          }
        } else {
          this.alertMessage = "Cannot connect to server. Please try again.";
          this.alertType = "error";
        }
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>
