<template>
  <div class="weather-error">
    <div class="error-box">
      <p class="error-message">{{ message }}</p>
      <button class="close-btn" @click="handleReturn">Return to VietCloud</button>
    </div>
    <div class="gif-container">
      <!-- nếu có prop gif thì hiển thị gif đó -->
      <img
        v-if="gif"
        class="error-gif"
        :src="require(`@/assets/${gif}`)"
        alt="error gif"
      />
      <!-- nếu không có gif prop thì hiển thị umbrella + sad -->
      <template v-else>
        <img class="umbrella" src="@/assets/umbrella.gif" alt="umbrella" />
        <img class="sad" src="@/assets/sad.gif" alt="sad" />
      </template>
    </div>
  </div>
</template>

<script>
export default {
  name: "WeatherError",
  props: {
    message: {
      type: String,
      required: true
    },
    gif: {
      type: String,
      default: "" // nếu không truyền thì dùng umbrella + sad
    }
  },
   methods: {
    handleReturn() {
      window.location.reload();
    },
  },
};
</script>

<style scoped>
.weather-error {
  padding: 1rem;
  background: #ffffff;
  color: #a00;
  border: 1px solid rgb(253, 253, 253);
  margin: 1rem 0;
  border-radius: 8px;
  position: relative;
  text-align: center;
}
.error-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-message {
  font-size: 1.4rem;
  font-weight: bold;
  color: #a00;
  flex: 1;
  text-align: left;
  word-break: break-word;
  white-space: pre-line; /* để xuống dòng \n */
  max-width: 80%;
}
.close-btn {
  background: #f1392c;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #fff;
  padding: 0.4rem 1rem;
  border-radius: 20px;
  transition: background 0.3s ease;
}
.close-btn:hover {
  background: #c33;
}
.gif-container {
  position: relative;
  margin-top: 1rem;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
}
.error-gif {
  max-width: 200px;
}
.umbrella {
  position: relative;
  max-width: 270px;
  margin-left: 36px;
  bottom: 36px;
  top: -20px;
  left: -36px;
}
.sad {
  position: absolute;
  bottom: 30px;
  left: 0;
  width: 80px;
}
</style>
