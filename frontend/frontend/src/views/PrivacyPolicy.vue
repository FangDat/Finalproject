<template>
  <div class="terms-container">
    <!-- Back button -->
    <button class="back-btn" @click="$router.push('/')">
      ← Return to VietCloud
    </button>

    <!-- Content Card -->
    <div class="terms-box">
      <h1 class="title">Privacy Policy</h1>

      <div v-html="termsHtml" class="terms-content"></div>

      <p class="confirm">
        ✅ By continuing to use VietCloud, you confirm that you’ve read and accepted these Terms and Conditions.
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: "TermsAndConditions",
  data() {
    return {
      termsHtml: `
      alo
      `,
    };
  },
};
</script>