<template>
  <div class="checkout-container">
    <!-- LEFT -->
    <div class="checkout-left">
      <button class="back-btn" @click="goBack">← Return to VietCloud</button>

      <div class="pricing-box">
        <h2 class="price">$6.96 <span class="vat">inc. VAT (per month)</span></h2>
        <p class="billing-cycle">Billed monthly</p>
        <p class="note">Secure payment via Stripe</p>

        <div class="card-logos">
          <img src="@/assets/visa.png" alt="Visa" />
          <img src="@/assets/mastercard.png" alt="Mastercard" />
          <img src="@/assets/amex.png" alt="Amex" />
          <img src="@/assets/discover.png" alt="Apple Pay" />
        </div>

      </div>
        </div>

        <!-- RIGHT -->
        <div class="checkout-right">
          <div class="credit-card-box">
            <h2 class="billing-title">Billing Information</h2>

              <form
                @submit.prevent="handleSubmit"
                class="credit-card-form"
                novalidate
              >
                <!-- FIRST + LAST NAME -->
              <div class="form-row">
                <div class="form-group">
                  <label>First name *</label>
                  <input v-model.trim="form.first_name" />
                  <p v-if="submitted && firstNameError" class="warning-text">
                    First name is required
                  </p>
                </div>

                <div class="form-group">
                  <label>Last name *</label>
                  <input v-model.trim="form.last_name" />
                  <p v-if="submitted && lastNameError" class="warning-text">
                    Last name is required
                  </p>
                </div>
              </div>

              <!-- ADDRESS -->
              <div class="form-group">
                <label>Address *</label>
                <input v-model.trim="form.address_line1" />
                <p v-if="submitted && addressError" class="warning-text">
                  Address is required
                </p>
              </div>

              <!-- CITY + POSTAL CODE -->
              <div class="form-row">
                <div class="form-group">
                  <label>City *</label>
                  <input v-model.trim="form.city" />
                  <p v-if="submitted && cityError" class="warning-text">
                    City is required
                  </p>
                </div>

                <div class="form-group">
                  <label>Postal code *</label>
                  <input
                    v-model="form.postal_code"
                    maxlength="6"
                    inputmode="numeric"
                  />
                  <p v-if="submitted && postalCodeError" class="warning-text">
                    Postal code must be 6 digits
                  </p>
                </div>
              </div>

              <!-- PHONE -->
              <div class="form-group">
                <label>Phone *</label>
                <input v-model="form.phone" placeholder="+84xxxxxxxxx" />
                <p v-if="submitted && phoneError" class="warning-text">
                  Phone must be in format +xxxxxxxxxxx
                </p>
              </div>

              <!-- BACKEND ERROR -->
              <p v-if="error" class="error-text">{{ error }}</p>

            <button class="btn-submit" :disabled="loading">
              {{ loading ? "Processing..." : "Continue to payment" }}
            </button>
          </form>
      </div>
    </div>
  </div>
    <!-- 🔒 PREMIUM INFO POPUP -->
  <div v-if="showPremiumPopup" class="premium-popup-overlay">
    <div class="premium-popup">
      <h2>✨ VietCloud Premium</h2>
      <p>
        You are not due for the next payment yet.<br />
        Please enjoy your exclusive VietCloud Premium features.
      </p>
      <button @click="showPremiumPopup = false">
        Got it
      </button>
    </div>
  </div>

</template>

<script>
import {
  fetchUserInfo,
  fetchBillingInfo,
  saveBillingInfo,
  createCheckoutSession,
} from "@/services/billingService";


export default {
  name: "Billing",
  data() {
    return {
      loading: false,
      error: "",
      submitted: false,
          // 🆕 PREMIUM STATE
      is_premium: false,
      showPremiumPopup: false,

      form: {
        first_name: "",
        last_name: "",
        address_line1: "",
        city: "",
        postal_code: "",
        phone: "",
      },
    };
  },

  async mounted() {
    // 🔐 check user + premium
    try {
      const data = await fetchUserInfo();
      this.is_premium = data.is_premium || false;
    } catch {
      this.$router.push("/");
      return;
    }

    // 💳 load billing info cũ (GIỮ NGUYÊN HÀNH VI)
    try {
      const billing = await fetchBillingInfo();
      Object.assign(this.form, billing);
    } catch (_) {
      // ignore nếu chưa có billing info
    }
  },

    methods: {
    async handleSubmit() {
      this.submitted = true;

      // 🔒 BLOCK PREMIUM USER
      if (this.is_premium) {
        this.showPremiumPopup = true;
        return;
      }

      if (this.hasAnyError) return;

      this.loading = true;
      this.error = "";

      try {
        // 💾 save billing info
        await saveBillingInfo(this.form);

        // 💸 create stripe session
        const data = await createCheckoutSession();

        window.location.href = data.checkout_url;
      } catch (err) {
        this.error = err.message || "Billing submission failed";
      } finally {
        this.loading = false;
      }
    },

    goBack() {
      this.$router.push("/");
    },
  },

    computed: {
      firstNameError() {
        return !this.form.first_name;
      },

      lastNameError() {
        return !this.form.last_name;
      },

      addressError() {
        return !this.form.address_line1;
      },

      cityError() {
        return !this.form.city;
      },

      postalCodeError() {
        return !/^\d{6}$/.test(this.form.postal_code);
      },  

      phoneError() {
        if (!this.form.phone) return true;
        return !/^\+\d{10,15}$/.test(this.form.phone);
      },

      hasAnyError() {
        return (
          this.firstNameError ||
          this.lastNameError ||
          this.addressError ||
          this.cityError ||
          this.postalCodeError ||
          this.phoneError
        );
      },
    },

};
</script>

<style scoped src="@/assets/Billing.css"></style>
