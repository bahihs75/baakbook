import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const required = [
  "FIREBASE_API_KEY",
  "FIREBASE_AUTH_DOMAIN",
  "FIREBASE_PROJECT_ID",
  "FIREBASE_STORAGE_BUCKET",
  "FIREBASE_MESSAGING_SENDER_ID",
  "FIREBASE_APP_ID"
];

const missing = required.filter((name) => !process.env[name]);
if (missing.length > 0) {
  throw new Error(`Missing runtime configuration: ${missing.join(", ")}`);
}

const config = {
  API_BASE: process.env.PUBLIC_API_BASE || "/api",
  FIREBASE: {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: process.env.FIREBASE_AUTH_DOMAIN,
    projectId: process.env.FIREBASE_PROJECT_ID,
    storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.FIREBASE_APP_ID
  }
};

const output = `/* Generated during the Pages build. Do not edit manually. */\nwindow.BAAK_RUNTIME = Object.freeze(${JSON.stringify(config, null, 2)});\n`;
const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
await writeFile(path.join(frontendRoot, "..", "runtime-config.js"), output, "utf8");
console.log("Generated runtime-config.js for the current Pages environment.");
