'use client';

import { getApps, initializeApp, FirebaseApp } from 'firebase/app';
import { Auth, getAuth } from 'firebase/auth';

// Immediately log environment variables
// console.log('Environment Variables Check:', {
//   API_KEY_EXISTS: !!process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
//   AUTH_DOMAIN_EXISTS: !!process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
//   PROJECT_ID_EXISTS: !!process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
// });

// // Log actual values (be careful with API key in production)
// console.log('Actual Environment Variables:', {
//   NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
//   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
//   NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
//   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
//   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
//   NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
// });

// Create config object
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

// Log the config object
// console.log('Firebase Config Object:', firebaseConfig);

let app: FirebaseApp | undefined;
let auth: Auth | undefined;

if (typeof window !== "undefined") {
  try {
    if (!getApps().length) {
      // console.log('About to initialize Firebase with config:', firebaseConfig);
      app = initializeApp(firebaseConfig);
      // console.log('Firebase app initialized successfully');
    } else {
      // console.log('Using existing Firebase app');
      app = getApps()[0];
    }
    auth = getAuth(app);
    // console.log('Firebase Auth initialized successfully');
  } catch (error) {
    console.error('Firebase initialization error:', error);
    // console.error('Failed Firebase Config:', JSON.stringify(firebaseConfig, null, 2));
  }
}

export { app, auth };