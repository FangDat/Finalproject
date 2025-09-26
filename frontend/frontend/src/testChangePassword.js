// import axios from "axios";

// export async function testChangePassword() { // ✅ export hàm
//   const accessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4ODM5Njc1LCJqdGkiOiJlYTE5YmRkZWIxOWU0YzU0YTEwYjJmMzU0YWY0NWIxZCIsInVzZXJfaWQiOiI2OGQxYWJjM2Y5NTQ0N2Q1ZGIzNjFiMDAifQ.Qo04rUmlhouFa2aEHfYYgQ1Y71NBUHMqOnu0VcrfkoQ";

//   try {
//     const response = await axios.post(
//       "http://localhost:8000/api/change-password/",
//       {
//         current_password: "D@t15112005",
//         new_password: "D@t15112004",
//         confirm_password: "D@t15112004",
//       },
//       {
//         headers: {
//           Authorization: `Bearer ${accessToken}`,
//         },
//       }
//     );

//     console.log("✅ Response:", response.data);
//   } catch (error) {
//     if (error.response) {
//       console.error("❌ Error response from backend:", error.response.data);
//     } else {
//       console.error("❌ Request error:", error.message);
//     }
//   }
// }