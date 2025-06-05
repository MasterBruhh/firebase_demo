// frontend/src/contexts/AuthContext.jsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from "firebase/auth";
import { auth } from "../services/firebase";
import { auditAPI } from "../services/api";

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

// ---------------------------------------------------------------------------
// PROVIDER
// ---------------------------------------------------------------------------
export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [idToken, setIdToken]       = useState(null);
  const [isAdmin, setIsAdmin]       = useState(false);
  const [loading, setLoading]       = useState(true);

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  const refreshTokenAndClaims = async (user) => {
    // ⚠️ devuelve el token para usarlo inmediatamente
    const token = await user.getIdToken(true);
    const tokenResult = await user.getIdTokenResult();
    setIdToken(token);
    setIsAdmin(Boolean(tokenResult.claims?.admin));
    localStorage.setItem("idToken", token);
    return token;
  };

  const getIdToken = async (forceRefresh = false) => {
    if (!currentUser) return null;
    const token = await currentUser.getIdToken(forceRefresh);
    setIdToken(token);
    localStorage.setItem("idToken", token);
    return token;
  };

  // establecemos getFreshToken con useCallback --> referencia estable
  const getFreshToken = useCallback(() => getIdToken(true), [currentUser]);

  // -------------------------------------------------------------------------
  // Auth flows
  // -------------------------------------------------------------------------
  const signup = async (email, password) => {
    const { user } = await createUserWithEmailAndPassword(auth, email, password);
    const token = await refreshTokenAndClaims(user);
    // Log the signup event
    try {
      await auditAPI.logEvent("SIGNUP", { email: user.email });
    } catch (error) {
      console.warn("Failed to log signup event:", error);
    }
    return user;
  };

  const login = async (email, password) => {
    const { user } = await signInWithEmailAndPassword(auth, email, password);
    const token = await refreshTokenAndClaims(user);
    // Log the login event
    try {
      await auditAPI.logEvent("LOGIN", { email: user.email });
    } catch (error) {
      console.warn("Failed to log login event:", error);
    }
    return user;
  };

  const logout = async () => {
    try {
      // Log the logout event before signing out
      if (currentUser) {
        await auditAPI.logEvent("LOGOUT", { email: currentUser.email });
      }
    } catch (error) {
      console.warn("Failed to log logout event:", error);
    }
    
    // Sign out from Firebase
    await signOut(auth);
    setCurrentUser(null);
    setIdToken(null);
    setIsAdmin(false);
    localStorage.removeItem("idToken");
  };

  // -------------------------------------------------------------------------
  // Listeners
  // -------------------------------------------------------------------------
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        await refreshTokenAndClaims(user);
      } else {
        setIdToken(null);
        setIsAdmin(false);
        localStorage.removeItem("idToken");
      }
      setLoading(false);
    });
    return unsub;
  }, []);

  // renovamos cada 50 min
  useEffect(() => {
    if (!currentUser) return;
    const int = setInterval(() => getIdToken(true), 50 * 60 * 1000);
    return () => clearInterval(int);
  }, [currentUser]);

  // -------------------------------------------------------------------------
  // Context value
  // -------------------------------------------------------------------------
  const value = {
    currentUser,
    idToken,
    isAdmin,
    signup,
    login,
    logout,
    getFreshToken, // función estable
  };

  return !loading && <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
