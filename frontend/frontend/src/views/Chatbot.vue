<template>
  <div class="chatbot-container">
    <!-- Sidebar trái -->
    <aside class="sidebar-left">
      <h2 class="logo">
        <router-link to="/">🌤 VietCloud</router-link>
      </h2>
      <nav class="nav-menu">
        <router-link to="/" exact class="nav-btn">☁️ Weather</router-link>
        <router-link to="/map" class="nav-btn">🗺️ Maps</router-link>
        <router-link v-if="username" to="/chatbot" class="nav-btn router-link-active">
          🤖 Chatbot
        </router-link>
        <router-link to="/settings" class="nav-btn">⚙️ Settings</router-link>
        <router-link v-if="username" to="/profile" class="nav-btn">👤 Profile</router-link>
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
export default {
  name: "Chatbot",
  data() {
    return {
      username: this.getCookie("username") || "",
      is_premium: false,

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

    // ✅ Giống Home.vue (GIỮ NGUYÊN)
    async fetchUserInfo() {
      try {
        const res = await fetch("http://localhost:8000/api/user-info/", {
          method: "GET",
          credentials: "include",
        });
        if (!res.ok) throw new Error("Not logged in");

        const data = await res.json();
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
        /\b(temperature|temperatures|hot|warm|heatwave|heat|feels like|high temperature)\b/gi,
        '<span class="temp">$1</span>'
      );

      // 🌧 Rain / precipitation keywords + mm
      result = result.replace(
        /(\d+(?:\.\d+)?\s?mm|\brain\b|\brainfall\b|\braining\b|\bprecipitation\b|\bcool\b|\bcold\b)/gi,
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


    // ✅ SEND MESSAGE (NO STREAMING)
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

        try {
          const res = await fetch(
            "http://localhost:8000/api/chatbot/intent/",
            {
              method: "POST",
              credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: text }),
            }
          );

          let data = {};
          try {
            data = await res.json();
          } catch {}

          let botText = "";

          if (res.status === 200) {
            botText =
              data.answer ||
              "The VietCloud system is overloaded. Please try again few minutes later.";
          } 
          else if (res.status === 401 || res.status === 403) {
            botText =
              "Sorry, your question must be in English and related to weather, which is the domain I can work with!";
          } 
          else if ([503, 500, 429, 400].includes(res.status)) {
            botText =
              "The VietCloud system is overloaded. Please try again few minutes later.";
          } 
          else {
            botText = "Something went wrong. Please try again later.";
          }

          this.messages.push({ role: "bot", text: botText });

        } catch {
          this.messages.push({
            role: "bot",
            text:
              "Unable to connect to VietCloud server. Please check your connection and try again.",
          });
        } finally {
          this.isTyping = false;
          this.stopThinkingAnimation();
          this.saveChatHistory();
          this.scrollToBottom();
        }
      },
    },

  mounted() {
    this.fetchUserInfo();
    this.loadChatHistory();

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
