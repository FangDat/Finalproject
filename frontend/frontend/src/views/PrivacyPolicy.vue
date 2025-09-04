<template>
  <div class="privacy-container">
    <!-- Back button -->
    <button class="back-btn" @click="$router.push('/')">
      ← Return to VietCloud
    </button>

    <!-- Content -->
    <div class="privacy-box">
      <h1 class="title">Privacy Policy</h1>

      <div v-html="privacyHtml" class="privacy-content"></div>

      <p class="confirm">
        ✅ By using VietCloud, you agree to this Privacy Policy.
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: "PrivacyPolicy",
  data() {
    return {
      privacyHtml: `
        <h2>1. Introduction</h2>
        <p>
          VietCloud (“we”, “our”, “the service”) is committed to protecting your privacy 
          and safeguarding your personal information. This Privacy Policy explains what 
          types of data we collect, how we use it, how we share it, and the choices you 
          have regarding your information. 
        </p>
        <p>
          By using VietCloud, you consent to the practices described here. If you disagree 
          with any part of this Policy, you should stop using the service immediately.
        </p>

        <h2>2. Information We Collect</h2>
        <p>We may collect the following categories of information when you interact with VietCloud:</p>
        <ul>
          <li><b>Account Information:</b> email address, username, encrypted password, and optional profile settings.</li>
          <li><b>Location Data:</b> approximate or precise geolocation if you enable it. Used to deliver local forecasts, 
          maps, and weather alerts. You can disable sharing at any time via device/browser settings.</li>
          <li><b>Usage Data:</b> search queries, chatbot interactions, click logs, app navigation patterns, browser/device type, 
          IP address, and operating system details.</li>
          <li><b>Payment Information:</b> subscription or premium transactions processed securely 
          by third-party payment gateways (e.g., PayPal, MoMo, VNPay). VietCloud does not store credit card details.</li>
          <li><b>Cookies & Tracking:</b> small files used to remember login, preferences (dark/light mode, language), 
          measure performance, and analyze aggregated usage statistics.</li>
        </ul>

        <h2>3. How We Use Your Data</h2>
        <p>Your data helps us provide, improve, and personalize VietCloud services. Specifically, we use it to:</p>
        <ul>
          <li>Deliver accurate forecasts, radar maps, and severe weather alerts.</li>
          <li>Offer personalization features such as search history, favorite locations, and chatbot responses.</li>
          <li>Process payments and manage subscription billing securely.</li>
          <li>Improve performance, detect bugs, and enhance reliability of the platform.</li>
          <li>Send important updates, service notifications, and—if you consent—marketing communications.</li>
        </ul>

        <h2>4. Data Sharing</h2>
        <p>We never sell your personal data. We only share information in these limited cases:</p>
        <ul>
          <li><b>Infrastructure & Hosting:</b> with cloud providers that host our servers and databases.</li>
          <li><b>Analytics:</b> with trusted providers in an aggregated and anonymized form to study traffic patterns.</li>
          <li><b>Payments:</b> with payment processors to complete subscription transactions.</li>
          <li><b>Legal:</b> if required by law, regulation, or to respond to valid legal requests from authorities.</li>
        </ul>

        <h2>5. Data Retention</h2>
        <p>
          We retain personal information only as long as necessary to deliver our services or meet legal obligations. 
          For example, account data is kept while your account remains active. You may request deletion at any time. 
          After deletion, some minimal backup or anonymized data may remain for compliance or technical purposes.
        </p>

        <h2>6. Security Measures</h2>
        <p>
          VietCloud applies industry-standard safeguards including SSL encryption, firewalls, 
          secure database storage, and restricted staff access. While we work hard to protect your 
          data, no system is completely secure, and we cannot guarantee absolute protection 
          against unauthorized access or breaches.
        </p>

        <h2>7. Your Rights</h2>
        <p>Depending on your jurisdiction, you may have the following rights:</p>
        <ul>
          <li>Request a copy of the personal data we hold about you.</li>
          <li>Request correction of inaccurate or incomplete data.</li>
          <li>Request deletion of your account and personal data.</li>
          <li>Withdraw consent for optional services (e.g., location sharing, marketing emails).</li>
          <li>Request restriction of data processing or portability of your data to another provider.</li>
        </ul>
        <p>
          To exercise these rights, please contact us at 
          <a href="mailto:privacy@vietcloud.app">privacy@vietcloud.app</a>.
        </p>

        <h2>8. International Users</h2>
        <p>
          VietCloud is accessible worldwide. If you are accessing the service from outside Vietnam, 
          be aware that your data may be processed and stored in jurisdictions with different data 
          protection laws than your home country.
        </p>

        <h2>9. Children's Privacy</h2>
        <p>
          VietCloud is not directed at children under 13 (or under 16 in some regions). 
          We do not knowingly collect personal data from minors. If we become aware that we 
          have unintentionally collected such data, we will delete it promptly.
        </p>

        <h2>10. Service Integrations & Third-Party Links</h2>
        <p>
          VietCloud integrates APIs and services such as OpenWeather, WeatherAPI, and OpenCage. 
          These providers may collect data subject to their own privacy policies. VietCloud is not 
          responsible for the practices of external websites linked within the app.
        </p>

        <h2>11. Changes to This Policy</h2>
        <p>
          We may revise this Privacy Policy periodically to reflect new features, services, or 
          legal requirements. Updates will be posted here with a “last updated” date. For major changes, 
          we will notify you by email or in-app alerts.
        </p>

        <h2>12. Contact Us</h2>
        <p>
          If you have questions, concerns, or privacy-related requests, please contact us at: 
          <a href="mailto:privacy@vietcloud.app">privacy@vietcloud.app</a>
        </p>
      `,
    };
  },
};
</script>

<style scoped>
.privacy-container {
  max-width: 950px;
  margin: 40px auto;
  padding: 20px;
}

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

.privacy-box {
  background: #fff;
  border-radius: 16px;
  padding: 35px 45px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
}

.title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 25px;
}

.privacy-content h2 {
  font-size: 1.3rem;
  margin-top: 25px;
  color: #1976d2;
}

.privacy-content p,
.privacy-content li {
  font-size: 1rem;
  line-height: 1.7;
  margin-bottom: 12px;
}

.privacy-content ul {
  list-style: disc;
  margin-left: 22px;
}

.confirm {
  margin-top: 25px;
  font-weight: 600;
  color: #2e7d32;
}
</style>
