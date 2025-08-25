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
          Welcome to <b>VietCloud</b> – a real-time weather forecasting web application offering weather information,
          travel suggestions, and premium features like chatbot and 10-day forecast.
        </p>
        <p>
          These Terms and Conditions ("Agreement") are a legal contract between you ("User") and VietCloud ("we",
          "our", or "us") regarding the use of our website and services.
        </p>
        <p>
          By using VietCloud, you agree to these terms. If you do not agree, please do not use the service.
        </p>

        <h2>2. Services</h2>
        <p><b>Free Users</b> can:</p>
        <ul>
          <li>Search and view weather forecast (up to 3 days)</li>
          <li>See weather charts, icons, and maps</li>
          <li>Receive public travel suggestions</li>
        </ul>
        <p><b>Premium Users</b> additionally:</p>
        <ul>
          <li>Access 10-day forecast</li>
          <li>Use chatbot for travel advice</li>
          <li>View personal search history</li>
          <li>Make and manage subscription payments</li>
        </ul>

        <h2>3. Payments & Subscriptions</h2>
        <p>
          Premium features require a subscription, billed monthly or annually. All payments are processed securely via
          third-party payment providers.
        </p>
        <p>
          Your subscription will automatically renew unless cancelled at least 48 hours before the billing cycle ends.
          No refunds for unused time. You may cancel anytime and retain access until the end of the paid period.
        </p>

        <h2>4. Use of Digital Content</h2>
        <p>
          By using our forecast data, weather charts, or downloading app content, you agree:
        </p>
        <ul>
          <li>Not to reproduce, sell, or redistribute without permission</li>
          <li>To use information for personal and non-commercial purposes</li>
        </ul>

        <h2>5. Cancellation and Refund Policy</h2>
        <p>
          If you're not satisfied, you may cancel your premium subscription through your account settings or by
          contacting support.
        </p>
        <p>
          Refunds are only granted if there's a verified technical issue or wrongful billing and will be evaluated
          case-by-case.
        </p>

        <h2>6. Privacy and Data</h2>
        <p>
          Your data (location, queries, etc.) is handled according to our <b>[Privacy Policy]</b>.
        </p>
        <p>
          We do not sell your personal information. Some anonymized weather queries may be used to improve service or
          analytics.
        </p>

        <h2>7. Termination</h2>
        <p>We reserve the right to suspend or terminate your access if:</p>
        <ul>
          <li>You violate these Terms</li>
          <li>Fraud or abuse is detected</li>
          <li>We discontinue or significantly alter the service</li>
        </ul>

        <h2>8. Limitation of Liability</h2>
        <p>
          VietCloud does not guarantee 100% accurate forecasts or uninterrupted service. You use VietCloud at your own
          risk.
        </p>
        <p>We are not liable for:</p>
        <ul>
          <li>Loss from decisions based on our forecasts</li>
          <li>External travel issues</li>
          <li>Indirect or consequential damages</li>
        </ul>

        <h2>9. Governing Law</h2>
        <p>
          For users in Vietnam: governed by Vietnamese law. <br />
          For international users: governed by the laws of England and Wales. <br />
          Any disputes will be resolved by competent courts in your jurisdiction or ours.
        </p>

        <h2>10. Contact Us</h2>
        <p>Have questions? Reach out at <a href="mailto:support@vietcloud.app">support@vietcloud.app</a></p>
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

/* Nút Return: xanh, bo tròn, to */
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
