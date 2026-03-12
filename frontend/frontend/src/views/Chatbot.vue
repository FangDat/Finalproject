<template>
  <div class="chatbot-container">
    <!-- Mobile: Toggle sidebar button -->
    <button
      class="sidebar-toggle"
      @click="toggleSidebar"
    >
      ☰
    </button>

    <!-- Mobile overlay -->
    <div
      v-if="showSidebar"
      class="sidebar-overlay"
      @click="closeSidebar"
    ></div>
    <!-- Sidebar trái -->
    <aside class="sidebar-left" :class="{ open: showSidebar }">

      <h2 class="logo">
        <img src="@/assets/cloudy.png" class="logo-icon" />
        VietCloud
      </h2>

      <nav class="nav-menu">

        <router-link
          to="/"
          exact
          class="nav-btn"
          @click.native="closeSidebar"
        >
          <img src="@/assets/cloudy.png" class="sidebar-icon" />
          Weather
        </router-link>

        <router-link
          to="/map"
          class="nav-btn"
          @click.native="closeSidebar"
        >
          <img src="@/assets/map.png" class="sidebar-icon" />
          Maps
        </router-link>

        <router-link
          v-if="username"
          to="/chatbot"
          class="nav-btn"
          @click.native="closeSidebar"
        >
          <img src="@/assets/chatbotsidebar.png" class="sidebar-icon" />
          Chatbot
        </router-link>

        <router-link
          to="/settings"
          class="nav-btn"
          @click.native="closeSidebar"
        >
          <img src="@/assets/setting.png" class="sidebar-icon" />
          Settings
        </router-link>

        <router-link
          v-if="username"
          to="/profile"
          class="nav-btn"
          @click.native="closeSidebar"
        >
          <img src="@/assets/user.png" class="sidebar-icon" />
          Profile
        </router-link>

      </nav>

    </aside>

    <!-- Nội dung chính -->
    <main v-if="username" class="chat-main">
      <header class="chat-header">
        <h3 class="chat-title">
          🤖 Chat with <span class="brand">VietCloud</span>
        </h3>

        <p class="chat-reminder">
          <strong>Friendly reminder:</strong><br />
          VietCloud AI Assistant currently supports <strong>English only</strong>.<br />
          Providing the correct <strong>date</strong> and <strong>location</strong> helps improve accuracy.
        </p>
      </header>

      <!-- CHAT CONTENT -->
      <section class="chat-window" ref="chatWindow">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="chat-message"
        :class="msg.role"
        v-html="msg.role === 'bot' ? highlightWeather(msg.text) : msg.text"
      ></div>


        <!-- typing indicator -->
        <div v-if="isTyping" class="chat-message bot thinking">
          {{ thinkingText }}
        </div>
      </section>


      <div class="ai-disclaimer">
        VietCloud AI bot may make errors. Please check the important information.
      </div>
      <!-- Input -->
      <footer class="chat-input-area">
        <input
          v-model="userInput"
          type="text"
          placeholder="Ask about weather, disasters, air quality..."
          class="chat-input"
          :disabled="!is_premium || isTyping"
          @keyup.enter="sendMessage"
        />
        <button
          class="btn-send"
          :disabled="!is_premium || isTyping || !userInput.trim()"
          @click="sendMessage"
        >
          ➤
        </button>
      </footer>

      <!-- 🔒 PREMIUM OVERLAY -->
      <div v-if="!is_premium" class="premium-overlay">
        <div class="overlay-content">
          <h2>🔒 Premium Feature</h2>
          <p>
            The AI Chatbot is available for <strong>VietCloud Premium</strong> users only.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { getUserInfo } from "@/services/authService";
import apiClient from "@/services/apiClient";
if (!window.__vietcloudChatPending) {
  window.__vietcloudChatPending = {
    pending: false,
    answer: null,
    promise: null,
  };
}

export default {
  name: "Chatbot",
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,
      showSidebar: false,
      // 🆕 CHAT STATE
      userInput: "",
      messages: [],
      isTyping: false,

          // 🆕 THINKING ANIMATION
      thinkingText: "VietCloud is thinking",
      thinkingDots: 0,
      thinkingTimer: null,

      welcomeMessage:
        "Hello! I'm VietCloud AI Assistant. Feel free to ask me about the weather anywhere in the world, get weather-related recommendations.",
    };
  },
  watch: {
    $route() {
      this.showSidebar = false;
    }
  },

  methods: {
    // 🔐 Helper đọc cookie (GIỮ NGUYÊN)
    getCookie(name) {
      const match = document.cookie.match(
        new RegExp("(^| )" + name + "=([^;]+)")
      );
      return match ? decodeURIComponent(match[2]) : null;
    },

      startThinkingAnimation() {
      this.thinkingDots = 0;
      this.thinkingText = "VietCloud is thinking";

      this.thinkingTimer = setInterval(() => {
        this.thinkingDots = (this.thinkingDots + 1) % 6; // 0 → 5
        this.thinkingText =
          "VietCloud is thinking" + ".".repeat(this.thinkingDots);
      }, 400);
    },

    stopThinkingAnimation() {
      if (this.thinkingTimer) {
        clearInterval(this.thinkingTimer);
        this.thinkingTimer = null;
      }
      this.thinkingText = "VietCloud is thinking";
    },
      // ===== MOBILE SIDEBAR =====
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },

    closeSidebar() {
      this.showSidebar = false;
    },

    // ✅ Giống Home.vue (GIỮ NGUYÊN)
    async fetchUserInfo() {
      try {
        const data = await getUserInfo();

        this.username = data.username || "";
        this.is_premium = data.is_premium || false;
      } catch {
        this.username = "";
        this.is_premium = false;
      }
    },

    // 🆕 LOAD CHAT FROM LOCALSTORAGE
    loadChatHistory() {
      const saved = localStorage.getItem("vietcloud_chat");

      if (saved) {
        this.messages = JSON.parse(saved);
        return;
      }

      // 🆕 Nếu chưa có chat → thêm lời chào của bot
      this.messages = [
        {
          role: "bot",
          text: this.welcomeMessage,
        },
      ];

      this.saveChatHistory();
    },

    // 🆕 SAVE CHAT
    saveChatHistory() {
      localStorage.setItem("vietcloud_chat", JSON.stringify(this.messages));
    },

    // 🆕 AUTO SCROLL
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatWindow;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
    clearChatHistory() {
      localStorage.removeItem("vietcloud_chat");
      this.messages = [
        {
          role: "bot",
          text: this.welcomeMessage,
        },
      ];
    },
    highlightWeather(text) {
      if (!text || typeof text !== "string") return "";

      let result = text;

      // 🌡 Temperature: 25°C | 25 °C | 25℃ | -3.5°C
      result = result.replace(
        /(-?\d+(?:\.\d+)?\s?(?:°\s?[CF]|℃|℉))/gi,
        '<span class="temp">$1</span>'
      );
        /* =======================
     🌡 TEMPERATURE KEYWORDS
     ======================= */
      result = result.replace(
        /\b(temperature|temperatures|hot|warm|heatwave|heat|mild|high temperature)\b/gi,
        '<span class="temp">$1</span>'
      );

      // 🌧 Rain / precipitation keywords + mm
      result = result.replace(
        /(\d+(?:\.\d+)?\s?mm|\brain\b|\brainy\b|\brainfall\b|\braining\b|\bprecipitation\b|\bcool\b|\bcold\b|\bcoldy\b)/gi,
        '<span class="rain">$1</span>'
      );
        /* =======================
     ⚠️ DISASTER KEYWORDS
     (longer phrases first)
     ======================= */
      result = result.replace(
        /\b(super typhoon|extreme weather|natural disaster|thunderstorms|hurricanes|cyclones|typhoons|tornado|earthquake|wildfires|landslide|tsunami|flood|storm|disasters|disasters)\b/gi,
        '⚠️ <span class="disaster">$1</span>'
      );

      return result;
    },

      async sendMessage() {
        if (!this.userInput.trim() || this.isTyping) return;

        const wordCount = this.userInput.trim().split(/\s+/).length;
        if (wordCount > 100) {
          alert("Message must not exceed 100 words.");
          return;
        }

        const text = this.userInput.trim();
        this.userInput = "";

        this.messages.push({ role: "user", text });
        this.saveChatHistory();
        this.scrollToBottom();

        this.isTyping = true;
        this.startThinkingAnimation();

        // 🔥 MARK PENDING (GLOBAL + LOCAL)
        window.__vietcloudChatPending.pending = true;
        window.__vietcloudChatPending.answer = null;
        localStorage.setItem("vietcloud_chat_pending", "1");

      const fetchPromise = apiClient
        .post("/api/chatbot/intent/", {
          message: text,
        })
        .then((res) => {
          const data = res.data || {};
          const botText =
            data.answer ||
            "The VietCloud system is overloaded. Please try again later.";

          window.__vietcloudChatPending.answer = botText;
          return botText;
        })
        .catch((err) => {
          // ⚠️ 401 / 403 → interceptor đã forceLogout
          if (err?.response?.status === 400) {
            const msg =
              "Sorry, your question must be in English and related to weather.";
            window.__vietcloudChatPending.answer = msg;
            return msg;
          }

          const errText =
            "Unable to connect to VietCloud server. Please try again.";
          window.__vietcloudChatPending.answer = errText;
          return errText;
        })
        .finally(() => {
          window.__vietcloudChatPending.pending = false;
          localStorage.removeItem("vietcloud_chat_pending");
        });

        window.__vietcloudChatPending.promise = fetchPromise;

        const answer = await fetchPromise;

        this.messages.push({ role: "bot", text: answer });
        this.isTyping = false;
        this.stopThinkingAnimation();
        this.saveChatHistory();
        this.scrollToBottom();
      },

    },

  mounted() {
    this.fetchUserInfo();
    this.loadChatHistory();

      // 🔁 RESUME THINKING / ANSWER
    if (localStorage.getItem("vietcloud_chat_pending") === "1") {
      this.isTyping = true;
      this.startThinkingAnimation();

      const p = window.__vietcloudChatPending.promise;
      if (p) {
        p.then((answer) => {
          if (
            answer &&
            !this.messages.some((m) => m.role === "bot" && m.text === answer)
          ) {
            this.messages.push({ role: "bot", text: answer });
            this.saveChatHistory();
            this.scrollToBottom();
          }

          this.isTyping = false;
          this.stopThinkingAnimation();
        });
      }
    }

    // 🔄 Sync cookie changes
    this.cookieCheckInterval = setInterval(() => {
      const cookieUsername = this.getCookie("username") || "";
      if (cookieUsername !== this.username) {
        this.username = cookieUsername;
        this.fetchUserInfo();
      }
      { if (!cookieUsername && this.username) {
      this.username = "";
      this.clearChatHistory();
    }
  }
    }, 1000);
  },

  beforeUnmount() {
    clearInterval(this.cookieCheckInterval);
  },
};
</script>

<style scoped src="@/assets/Chatbot.css"></style>
