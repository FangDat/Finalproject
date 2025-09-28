// src/utils.js

// Temperature
export function cToF(c) {
  return (c * 9) / 5 + 32;
}
export function fToC(f) {
  return ((f - 32) * 5) / 9;
}

// Wind speed (input m/s)
export function msToKmh(ms) {
  return ms * 3.6;
}
export function msToMph(ms) {
  return ms * 2.23694;
}

// Visibility (input in METERS from OpenWeather)
export function mToKm(m) {
  return m / 1000; // m → km
}
export function mToMiles(m) {
  return (m / 1000) * 0.621371; // m → miles
}

// Nếu vẫn cần km↔miles riêng:
export function kmToMiles(km) {
  return km * 0.621371;
}
export function milesToKm(miles) {
  return miles / 0.621371;
}
