// billingService.js
import apiClient from "./apiClient";

// 👤 lấy thông tin user (premium hay không)
export async function fetchUserInfo() {
  const res = await apiClient.get("/api/user-info/");
  return res.data;
}

// 💳 lấy billing info cũ
export async function fetchBillingInfo() {
  const res = await apiClient.get("/api/billing-info/");
  return res.data;
}

// 💾 lưu billing info
export async function saveBillingInfo(payload) {
  try {
    await apiClient.post("/api/billing-info/save/", payload);
    return true;
  } catch (err) {
    const msg =
      err?.response?.data?.error || "Save billing failed";
    throw new Error(msg);
  }
}

// 💸 tạo Stripe checkout session
export async function createCheckoutSession() {
  const res = await apiClient.post(
    "/api/stripe/create-checkout-session/"
  );
  return res.data; // { checkout_url }
}
