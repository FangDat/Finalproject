<template>
  <div class="signup-container">
    <div class="signup-card">
      <!-- Logo -->
      <div class="logo-section">
        <img src="@/assets/clouds.png" alt="VietCloud" class="logo" />
        <h2>VietCloud</h2>
      </div>

      <!-- Title -->
      <h3 class="signup-title">
        Sign up now to experience exclusive features from VietCloud
      </h3>

      <!-- Sign in link -->
      <p class="signin-text">
        Already have an account?
        <router-link to="/login" class="signin-link">Sign in</router-link>
      </p>

      <!-- Alert box -->
      <div v-if="alertMessage" :class="['alert-box', alertType]">
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
        By clicking the "Sign up" button, you are creating an account, and you agree to the
        <router-link to="/terms" class="terms-link">Terms of Use</router-link>.
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Cookies from "js-cookie";

export default {
  name: "SignUp",
  data() {
    return {
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
      submitting: false,

      // alert UI
      alertMessage: "",
      alertType: "info",

      // field errors
      errors: {
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
      },
    };
  },
  methods: {
    resetErrors() {
      this.errors = { username: "", email: "", password: "", confirmPassword: "" };
      this.alertMessage = "";
      this.alertType = "info";
    },

    async handleSignup() {
      this.resetErrors();

      // ✅ Client-side validation
      if (!this.username || !this.email || !this.password || !this.confirmPassword) {
        if (!this.username) this.errors.username = "Please enter your username.";
        if (!this.email) this.errors.email = "Please enter your email.";
        if (!this.password) this.errors.password = "Please enter your password.";
        if (!this.confirmPassword) this.errors.confirmPassword = "Please confirm your password.";
        this.alertMessage = "Please fill in all required fields.";
        this.alertType = "warning";
        return;
      }

      if (this.password !== this.confirmPassword) {
        this.errors.confirmPassword = "Passwords do not match.";
        this.alertMessage = "Passwords do not match.";
        this.alertType = "warning";
        return;
      }

      this.submitting = true;
      try {
        const payload = {
          username: this.username,
          email: this.email,
          password: this.password,
        };

        const res = await axios.post("http://127.0.0.1:8000/api/signup/", payload, {
          headers: { "Content-Type": "application/json" },
          withCredentials: true, // cookie gửi kèm nếu backend hỗ trợ
        });

        // ✅ Lưu thông tin vào cookie (chỉ lưu thông tin cần thiết)
        const user = res.data?.user || this.username;
        const email = res.data?.email || this.email;

        Cookies.set("username", user, { expires: 7 });
        Cookies.set("email", email, { expires: 7 });

        this.alertMessage = "Signup successful! Redirecting to Payment Page..";
        this.alertType = "success";

        setTimeout(() => {
          this.$router.push("/credit-card");
        }, 3000);
      } catch (err) {
        if (err.response && err.response.status === 400 && err.response.data) {
          const data = err.response.data;
          if (data.email?.[0]?.includes("already exists")) {
            this.errors.email = "This email is already in use!";
            this.alertMessage = "This email is already in use!";
            this.alertType = "warning";
          } else if (data.username?.[0]?.includes("already exists")) {
            this.errors.username = "Username already exists!";
            this.alertMessage = "Username already exists!";
            this.alertType = "warning";
          } else {
            this.alertMessage = "Signup failed. Please check your inputs.";
            this.alertType = "error";
          }
        } else {
          this.alertMessage = "Signup failed. Please try again.";
          this.alertType = "error";
        }
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>

<style scoped>
/* Layout tổng thể */
.signup-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f4f0ff;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

/* Card đăng ký */
.signup-card {
  background: #fff;
  padding: 40px;
  border-radius: 20px;
  width: 420px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  text-align: center;
}

/* Logo */
.logo-section {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}
.logo {
  width: 40px;
  height: 40px;
}

/* Title */
.signup-title {
  font-size: 1.2rem;
  margin-bottom: 15px;
  font-weight: bold;
}

/* Sign in text */
.signin-text {
  margin-bottom: 20px;
  font-size: 1rem;
}
.signin-link {
  color: #2196f3;
  font-weight: bold;
  text-decoration: none;
}
.signin-link:hover {
  text-decoration: underline;
}

/* Form */
.signup-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}
.signup-form label {
  font-size: 1rem;
  font-weight: 500;
}
.signup-form input {
  padding: 12px 15px;
  border-radius: 10px;
  border: 1px solid #ccc;
  font-size: 1rem;
  outline: none;
}
.signup-form input:focus {
  border-color: #2196f3;
  box-shadow: 0 0 4px rgba(33, 150, 243, 0.3);
}

/* Input error */
.input-error {
  border-color: #e53935 !important;
  box-shadow: 0 0 4px rgba(229, 57, 53, 0.2) !important;
}
.error-msg {
  color: #e53935;
  font-size: 0.9rem;
  margin: -6px 0 8px 2px;
}

/* Alert box */
.alert-box {
  padding: 12px 15px;
  border-radius: 10px;
  margin-bottom: 15px;
  font-size: 0.95rem;
  text-align: center;
}
.alert-box.success {
  background: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #c8e6c9;
}
.alert-box.error {
  background: #ffebee;
  color: #c62828;
  border: 1px solid #ffcdd2;
}
.alert-box.warning {
  background: #fff8e1;
  color: #f57f17;
  border: 1px solid #ffe082;
}

/* Button */
.btn-signup {
  margin-top: 10px;
  padding: 12px 30px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  align-self: center;
}
.btn-signup[disabled] {
  opacity: 0.7;
  cursor: not-allowed;
}
.btn-signup:hover {
  background: #1976d2;
}
.lock-icon {
  font-size: 1.2rem;
}

.terms-link {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}
.terms-link:hover {
  text-decoration: underline;
}
</style>
