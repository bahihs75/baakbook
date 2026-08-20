/*
 * Safe template for local/staging builds.
 * Copy to frontend/runtime-config.js and replace the Firebase placeholders.
 * Never place Firebase Admin credentials, service-account JSON, or ImgBB keys here.
 */
window.BAAK_RUNTIME = Object.freeze({
  API_BASE: "/api",
  FIREBASE: {
    apiKey: "replace-with-baakbook-77c00-web-api-key",
    authDomain: "baakbook-77c00.firebaseapp.com",
    projectId: "baakbook-77c00",
    storageBucket: "baakbook-77c00.firebasestorage.app",
    messagingSenderId: "replace-with-baakbook-77c00-sender-id",
    appId: "replace-with-baakbook-77c00-app-id"
  }
});
