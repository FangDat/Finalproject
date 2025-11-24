// // src/axios.js
// import axios from "axios";

// // tạo instance axios mặc định cho toàn app
// const api = axios.create({
//   baseURL: "http://localhost:8000/api",
//   withCredentials: true, // ⚠️ gửi cookie HttpOnly kèm request
// });

// // ---------------------------
// // Interceptor: handle 401 → tự refresh token
// // ---------------------------
// let isRefreshing = false;
// let failedQueue = [];

// const processQueue = (error, token = null) => {
//   failedQueue.forEach(prom => {
//     if (error) {
//       prom.reject(error);
//     } else {
//       prom.resolve(token);
//     }
//   });
//   failedQueue = [];
// };

// api.interceptors.response.use(
//   response => response, // success thì trả về bình thường
//   async error => {
//     const originalRequest = error.config;

//     // nếu lỗi 401 và chưa retry
//     if (error.response && error.response.status === 401 && !originalRequest._retry) {
//       if (isRefreshing) {
//         // nếu đang refresh, queue lại request này
//         return new Promise((resolve, reject) => {
//           failedQueue.push({ resolve, reject });
//         })
//           .then(() => api(originalRequest))
//           .catch(err => Promise.reject(err));
//       }

//       originalRequest._retry = true;
//       isRefreshing = true;

//       try {
//         // gọi API refresh token
//         await api.post("/refresh/", {}); // cookie HttpOnly tự gửi kèm
//         isRefreshing = false;
//         processQueue(null); // retry tất cả queued request

//         // retry request gốc
//         return api(originalRequest);
//       } catch (err) {
//         isRefreshing = false;
//         processQueue(err, null);
//         return Promise.reject(err);
//       }
//     }

//     return Promise.reject(error);
//   }
// );

// export default api;
