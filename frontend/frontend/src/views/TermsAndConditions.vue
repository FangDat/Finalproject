<template>
  <div class="terms-container">
    <!-- Back button -->
    <button class="back-btn" @click="$router.push('/')">
      ← Return to VietCloud
    </button>

    <!-- Content Card -->
    <div class="terms-box">
      <h1 class="title">Terms and Conditions</h1>

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
        <h2>1. Introduction</h2>
        <p>
          Welcome to <b>VietCloud</b> – a real-time weather forecasting application offering global forecasts, 
          travel tips, and premium features like chatbot and 10-day outlooks.
        </p>
        <p>
          By using VietCloud, you agree to follow these Terms. If you do not agree, you must stop using our services.
        </p>

        <h2>2. Services</h2>
        <p><b>Free Users</b> may:</p>
        <ul>
          <li>Check weather forecasts up to 3 days</li>
          <li>Access maps, charts, and public travel suggestions</li>
        </ul>
        <p><b>Premium Users</b> gain extra features:</p>
        <ul>
          <li>10-day forecast</li>
          <li>AI chatbot for travel advice</li>
          <li>Personal search history</li>
          <li>Payment & subscription management</li>
        </ul>

        <h2>3. Payments & Subscriptions</h2>
        <p>
          Premium features require a subscription (monthly or annual). Payments are processed securely through 
          third-party providers.
        </p>
        <p>
          Subscriptions renew automatically unless cancelled at least 48 hours before renewal. Refunds are not provided 
          for unused time.
        </p>

        <h2>4. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Copy, sell, or redistribute our data without consent</li>
          <li>Exploit, hack, or misuse our services</li>
          <li>Share accounts or attempt reverse engineering</li>
        </ul>

        <h2>5. Cancellation & Refund Policy</h2>
        <p>
          You may cancel your premium subscription anytime via account settings. Refunds are only issued for 
          verified technical faults or wrongful charges.
        </p>

        <h2>6. Privacy & Data</h2>
        <p>
          Your data (location, search history, etc.) is handled under our <b>Privacy Policy</b>. We do not sell personal data. 
          Some anonymized information may be used for analytics.
        </p>

        <h2>7. Termination</h2>
        <p>
          We may suspend or terminate accounts if users violate these Terms, commit fraud, or misuse services.
        </p>

        <h2>8. Limitation of Liability</h2>
        <p>
          VietCloud aims for accurate forecasts but does not guarantee 100% reliability. Users assume all risk 
          when using weather data for travel or decision-making.
        </p>
        <p>We are not liable for:</p>
        <ul>
          <li>Losses due to reliance on forecasts</li>
          <li>Travel disruptions</li>
          <li>Indirect or consequential damages</li>
        </ul>

        <h2>9. Governing Law</h2>
        <p>
          For Vietnam-based users: governed by Vietnamese law. <br/>
          For international users: governed by English law. <br/>
          Any disputes will be settled in competent courts.
        </p>

        <h2>10. Contact Us</h2>
        <p>
          Questions? Contact us at <a href="mailto:support@vietcloud.app">support@vietcloud.app</a>
        </p>
      `,
    };
  },
};
</script>

<style scoped>
.terms-container {
  max-width: 900px;
  margin: 40px auto;
  padding: 20px;
}

/* Back button */
.back-btn {
  background-color: #1976d2;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  padding: 10px 20px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  margin-bottom: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transition: background 0.3s ease, transform 0.2s ease;
}
.back-btn:hover {
  background-color: #1565c0;
  transform: translateY(-2px);
}

.terms-box {
  background: #fff;
  border-radius: 16px;
  padding: 30px 40px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 25px;
}

.terms-content h2 {
  font-size: 1.2rem;
  margin-top: 20px;
  color: #1976d2;
}

.terms-content p,
.terms-content li {
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 12px;
}

.terms-content ul {
  list-style: disc;
  margin-left: 20px;
}

.confirm {
  margin-top: 25px;
  font-weight: 600;
  color: #2e7d32;
}
</style>
