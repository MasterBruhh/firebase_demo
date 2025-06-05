// frontend/src/services/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getStorage } from 'firebase/storage';

// Your Firebase configuration
// TODO: Replace these values with your actual Firebase project configuration
const firebaseConfig = {
    apiKey: "AIzaSyAnlMW-lOQg3YmssadJp86apbtnokeu_8s",
    authDomain: "indexador-demo-gemini.firebaseapp.com",
    projectId: "indexador-demo-gemini",
    storageBucket: "indexador-demo-gemini.firebasestorage.app",
    messagingSenderId: "1054037908225",
    appId: "1:1054037908225:web:cf279981cb093e3a19d900"
  };

// Check if we're in development mode and show warning
if (firebaseConfig.apiKey === "demo-api-key") {
  console.warn("⚠️  Using demo Firebase configuration. Please update frontend/src/services/firebase.js with your actual Firebase project credentials.");
}

let app, auth, storage;

try {
  // Initialize Firebase
  app = initializeApp(firebaseConfig);
  
  // Initialize Firebase Authentication and get a reference to the service
  auth = getAuth(app);
  
  // Initialize Firebase Storage and get a reference to the service
  storage = getStorage(app);
} catch (error) {
  console.error("Firebase initialization failed:", error);
  console.warn("The app will run in demo mode. Authentication features will not work until you configure Firebase properly.");
}

export { auth, storage };
export default app;