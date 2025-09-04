<template>
  <div class="profile-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">🌤 Viet Cloud</h2>
      <nav class="nav-menu">
        <router-link to="/" class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <button class="nav-btn active">👤 Profile</button>
      </nav>
    </aside>

    <!-- Nội dung chính -->
    <main class="main-content">
      <!-- Thanh trên cùng -->
      <header class="top-bar">
        <h1 class="section-title">Personal info</h1>
        <router-link to="/" class="btn-logout">Logout</router-link>
      </header>

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
            <input type="text" value="abcde@gmail.com" readonly />
            <span class="change-link">change email</span>
          </div>
        </div>
        <div class="info-row">
          <label>Username</label>
          <div class="inline-input">
            <input type="text" value="abcde" readonly class="readonly-input" />
            <span class="note">cannot be changed</span>
          </div>
        </div>
      </section>

      <!-- Security -->
      <section class="card" id="security">
        <h2 class="sub-title">Security</h2>
        <p>Password</p>
        <p class="note">Last change on DD/MM/YYYY</p>
        <p>
          Protect your VietCloud account from unauthorized access. Use a strong
          password !!!
        </p>
        <div class="card-actions">
          <button class="btn-danger" @click="handleAction('change-password')">Change password</button>
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
          <button class="btn-danger" @click="handleAction('delete-account')">Delete your account</button>
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
        <p>
          Your premium package has expired, please click the "Renew" button to
          continue using VietCloud's exclusive features.
        </p>
        <div class="card-actions">
          <button class="btn-primary" @click="handleAction('renew')">Renew</button>
        </div>
      </section>

      <!-- Feedback -->
      <section class="card" id="support">
        <h2 class="sub-title">Support</h2>
        <p>
          Need feedback or assistance? Leave a comment below or email
          <b>abc@gmail.com</b>
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
  </div>
</template>

<script>
export default {
  name: "Profile",
  data() {
    return {
      activeTab: "basic",
    };
  },
  methods: {
    scrollTo(section) {
      this.activeTab = section;
      const el = document.getElementById(section);
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    },
    handleAction(action) {
      alert(`Action triggered: ${action}`);
    },
  },
};
</script>

<style src="@/assets/Profile.css"></style>
