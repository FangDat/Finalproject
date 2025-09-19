<template>
  <div class="checkout-container">
    <!-- Cột trái -->
    <div class="checkout-left">
      <button class="back-btn" @click="goBack">← Return to VietCloud</button>

      <div class="pricing-box">
        <h2 class="price">
          $6.96 <span class="vat">inc. VAT</span>
        </h2>
        <p class="billing-cycle">Billed monthly</p>
        <p class="note">Automatically subscribed, cancel anytime if you want</p>

        <div class="pricing-details">
          <div class="row"><span>Subtotal</span><span class="value">$6.264</span></div>
          <div class="row"><span>VAT</span><span class="value">$0.696</span></div>
          <hr />
          <div class="row total"><span>Total</span><span class="value">$6.96</span></div>
        </div>
      </div>
    </div>

    <!-- Cột phải -->
    <div class="checkout-right">
      <div class="credit-card-box">
        <h2 class="billing-title">Billing Information</h2>
       <!-- <h5 class="warning-text">Warning: Invalid input will be cleared!</h5> -->

        <div class="card-logos">
          <img src="@/assets/visa.png" alt="Visa" />
          <img src="@/assets/mastercard.png" alt="Mastercard" />
          <img src="@/assets/discover.png" alt="Discover" />
          <img src="@/assets/amex.png" alt="Amex" />
        </div>

        <form @submit.prevent="handleSubmit" class="credit-card-form">
          <!-- Name -->
          <div class="form-group">
            <label for="cardName">Name on card</label>
            <input
              type="text"
              id="cardName"
              v-model="cardName"
              placeholder="John Doe"
              autocomplete="cc-name"
              required
            />
          </div>

          <!-- Card Number -->
          <div class="form-group">
            <label for="cardNumber">Card number</label>
            <input
              type="text"
              id="cardNumber"
              v-model="cardNumber"
              placeholder="#### #### #### ####"
              maxlength="19"
              inputmode="numeric"
              @keydown="onlyDigits($event)"
              @input="formatCardNumber"
              @paste.prevent="onPasteCard"
              autocomplete="cc-number"
              required
            />
          </div>

          <!-- Exp + CVV -->
          <div class="form-row">
            <div class="form-group small">
              <label for="expDate">Exp. date</label>
              <input
                type="text"
                id="expDate"
                v-model="expDate"
                placeholder="MM/YY"
                maxlength="5"
                inputmode="numeric"
                @keydown="onlyDigitsOrSlash($event)"
                @input="formatExpDate"
                @paste.prevent="onPasteExp"
                autocomplete="cc-exp"
                required
              />
              <p v-if="expError" class="error-text">{{ expError }}</p>
            </div>

            <div class="form-group small">
              <label for="cvv">CVV</label>
              <input
                type="password"
                id="cvv"
                v-model="cvv"
                placeholder="***"
                maxlength="3"
                inputmode="numeric"
                pattern="[0-9]*"
                @beforeinput="guardDigits($event)"
                @input="cvv = cvv.replace(/[^0-9]/g, '').slice(0, 4)"
                @paste.prevent="onPasteDigits('cvv', 4)"
                autocomplete="cc-csc"
                required
              />
            </div>
          </div>

          <!-- ZIP -->
          <div class="form-group">
            <label for="zip">ZIP / Postal code</label>
            <input
              type="text"
              id="zip"
              v-model="zip"
              placeholder="10001"
              maxlength="5"
              inputmode="numeric"
              @keydown="onlyDigits($event)"
              @input="zip = zip.replace(/[^0-9]/g, '').slice(0, 6)"
              @paste.prevent="onPasteDigits('zip', 6)"
              autocomplete="postal-code"
              required
            />
          </div>

          <!-- Submit -->
          <button type="submit" class="btn-submit">🔒 Add card</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CreditCard",
  data() {
    return {
      cardName: "",
      cardNumber: "",
      expDate: "",
      cvv: "",
      zip: "",
      expError: ""
    };
  },
  methods: {
    /* ======= CHẶN PHÍM ======= */
    onlyDigits(e) {
      if (
        (e.key >= "0" && e.key <= "9") ||
        ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab"].includes(e.key)
      ) {
        return;
      }
      e.preventDefault();
    },
    onlyDigitsOrSlash(e) {
      if (
        (e.key >= "0" && e.key <= "9") ||
        e.key === "/" ||
        ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab"].includes(e.key)
      ) {
        return;
      }
      e.preventDefault();
    },
    guardDigits(e) {
      if (e.inputType !== "insertText") return;
      if (e.data && /\D/.test(e.data)) {
        e.preventDefault();
      }
    },

    /* ======= PASTE HANDLERS ======= */
    onPasteDigits(field, maxLen) {
      const text = (event.clipboardData || window.clipboardData).getData("text");
      const digits = text.replace(/\D/g, "").slice(0, maxLen);
      this[field] = digits;
    },
    onPasteCard(event) {
      const text = (event.clipboardData || window.clipboardData).getData("text");
      const digits = text.replace(/\D/g, "").slice(0, 16);
      this.cardNumber = digits.replace(/(.{4})/g, "$1 ").trim();
    },
    onPasteExp(event) {
      const text = (event.clipboardData || window.clipboardData).getData("text");
      const digits = text.replace(/\D/g, "").slice(0, 4);
      this.expDate = this.buildValidExpFromDigits(digits);
    },

    /* ======= FORMATTERS ======= */
    formatCardNumber() {
      const digits = this.cardNumber.replace(/\D/g, "").slice(0, 16);
      this.cardNumber = digits.replace(/(.{4})/g, "$1 ").trim();
    },
    formatExpDate() {
      const digits = this.expDate.replace(/\D/g, "").slice(0, 4);
      this.expDate = this.buildValidExpFromDigits(digits);
      this.expError = "";
    },
    buildValidExpFromDigits(d) {
      if (d.length === 0) return "";
      let mm = d.slice(0, 2);
      if (d.length === 1) {
        const first = d[0];
        if (parseInt(first, 10) > 1) {
          return `0${first}/`;
        }
        return first;
      }
      let m1 = parseInt(mm[0], 10);
      let m2 = parseInt(mm[1], 10);
      if (m1 === 0) {
        if (m2 === 0) mm = "01";
      } else if (m1 === 1) {
        if (m2 > 2) mm = "12";
      } else {
        mm = `0${m1}`;
      }
      if (d.length <= 2) {
        return mm.length === 2 ? `${mm}/` : mm;
      }
      const yy = d.slice(2, 4);
      return `${mm}/${yy}`;
    },

    /* ======= VALIDATION ======= */
    validateExpDate() {
      if (!/^\d{2}\/\d{2}$/.test(this.expDate)) {
        this.expError = "Invalid format (MM/YY)";
        return false;
      }
      const [month, year] = this.expDate.split("/").map(Number);
      const now = new Date();
      const currentYear = now.getFullYear() % 100;
      const currentMonth = now.getMonth() + 1;

      if (month < 1 || month > 12) {
        this.expError = "Month must be 01–12";
        return false;
      }
      if (year < currentYear || (year === currentYear && month < currentMonth)) {
        this.expError = "Card is expired";
        return false;
      }
      this.expError = "";
      return true;
    },

    /* ======= SUBMIT ======= */
    handleSubmit() {
      if (!this.validateExpDate()) return;
      alert("✅ Card saved successfully!");
    },

    goBack() {
      this.$router.push("/");
    }
  }
};
</script>

<style scoped src="@/assets/CreditCard.css"></style>
