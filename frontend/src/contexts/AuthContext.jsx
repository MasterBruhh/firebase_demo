import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged 
} from 'firebase/auth';
import { auth } from '../services/firebase';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState(null);

  // Register a new user
  async function signup(email, password) {
    if (!auth) {
      throw new Error("Firebase not initialized. Please configure your Firebase credentials.");
    }
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const token = await userCredential.user.getIdToken(true); // Force refresh
      setIdToken(token);
      localStorage.setItem('idToken', token);
      return userCredential;
    } catch (error) {
      throw error;
    }
  }

  // Sign in an existing user
  async function login(email, password) {
    if (!auth) {
      throw new Error("Firebase not initialized. Please configure your Firebase credentials.");
    }
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const token = await userCredential.user.getIdToken(true); // Force refresh
      setIdToken(token);
      localStorage.setItem('idToken', token);
      return userCredential;
    } catch (error) {
      throw error;
    }
  }

  // Sign out the current user
  async function logout() {
    if (!auth) {
      throw new Error("Firebase not initialized. Please configure your Firebase credentials.");
    }
    try {
      await signOut(auth);
      setIdToken(null);
      localStorage.removeItem('idToken');
    } catch (error) {
      throw error;
    }
  }

  // Get the current user's ID token (always fresh)
  async function getIdToken(forceRefresh = false) {
    if (currentUser) {
      try {
        const token = await currentUser.getIdToken(forceRefresh);
        setIdToken(token);
        localStorage.setItem('idToken', token);
        return token;
      } catch (error) {
        console.error('Error getting ID token:', error);
        throw error;
      }
    }
    return null;
  }

  // Get a fresh token for API calls
  async function getFreshToken() {
    return await getIdToken(true); // Always force refresh
  }

  useEffect(() => {
    if (!auth) {
      // Firebase not initialized, set loading to false
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      
      if (user) {
        // Get fresh ID token when user signs in
        try {
          const token = await user.getIdToken(true); // Force refresh
          setIdToken(token);
          localStorage.setItem('idToken', token);
        } catch (error) {
          console.error('Error getting ID token:', error);
        }
      } else {
        setIdToken(null);
        localStorage.removeItem('idToken');
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Auto-refresh token every 50 minutes (10 minutes before expiration)
  useEffect(() => {
    if (!currentUser) return;

    const interval = setInterval(async () => {
      try {
        await getIdToken(true); // Force refresh token
        console.log('Token refreshed automatically');
      } catch (error) {
        console.error('Error auto-refreshing token:', error);
      }
    }, 50 * 60 * 1000); // 50 minutes

    return () => clearInterval(interval);
  }, [currentUser]);

  const value = {
    currentUser,
    idToken,
    signup,
    login,
    logout,
    getIdToken,
    getFreshToken
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
} 