/**
 * Contexto de Autenticación - Gestión Global del Estado de Usuario
 * 
 * Este contexto proporciona la gestión completa del estado de autenticación
 * para toda la aplicación React. Integra Firebase Authentication con
 * funcionalidades avanzadas de gestión de sesiones y roles.
 * 
 * Funcionalidades principales:
 * - Autenticación con Firebase Auth
 * - Gestión de tokens ID con renovación automática
 * - Sistema de roles (admin/usuario)
 * - Auditoría automática de eventos de autenticación
 * - Persistencia de sesión con localStorage
 * - Manejo de estados de carga
 * - Renovación automática de tokens
 * - Limpieza segura de sesiones
 * 
 * Estados manejados:
 * - currentUser: Usuario actual autenticado
 * - idToken: Token ID de Firebase para autenticación
 * - isAdmin: Indicador de permisos de administrador
 * - loading: Estado de carga durante autenticación
 * 
 * Métodos proporcionados:
 * - signup: Registro de nuevos usuarios
 * - login: Inicio de sesión
 * - logout: Cierre de sesión seguro
 * - getFreshToken: Obtención de token actualizado
 * - refreshTokenAndClaims: Renovación completa de credenciales
 * 
 * Características de seguridad:
 * - Renovación automática de tokens cada 50 minutos
 * - Limpieza completa de datos en logout
 * - Validación de claims personalizados
 * - Auditoría de todos los eventos de autenticación
 * - Manejo seguro de errores
 * 
 * Integración:
 * - Firebase Authentication para autenticación
 * - Sistema de auditoría para logging
 * - localStorage para persistencia
 * - Claims personalizados para roles
 * 
 * Uso:
 * ```jsx
 * import { useAuth } from '../contexts/AuthContext';
 * 
 * function MyComponent() {
 *   const { currentUser, isAdmin, login, logout } = useAuth();
 *   // ... usar funcionalidades de autenticación
 * }
 * ```
 * 
*/

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo
} from "react";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile
} from "firebase/auth";
import { auth } from "../services/firebase";
import { auditAPI } from "../services/api";

// ===== CONFIGURACIÓN =====

/** Intervalo de renovación de token (50 minutos en milisegundos) */
const TOKEN_REFRESH_INTERVAL = 50 * 60 * 1000;

/** Tiempo de expiración para mostrar advertencia (5 minutos antes) */
const TOKEN_WARNING_THRESHOLD = 5 * 60 * 1000;

// ===== CREACIÓN DEL CONTEXTO =====

/**
 * Contexto de autenticación para la aplicación
 * 
 * Proporciona estado y funciones de autenticación a todos los componentes
 * descendientes que lo necesiten.
 */
const AuthContext = createContext(undefined);

/**
 * Hook personalizado para usar el contexto de autenticación
 * 
 * @returns {Object} Objeto con estado y funciones de autenticación
 * @throws {Error} Si se usa fuera del AuthProvider
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};

// ===== PROVIDER DEL CONTEXTO =====

/**
 * Proveedor del contexto de autenticación
 * 
 * Envuelve la aplicación y proporciona funcionalidades de autenticación
 * a todos los componentes descendientes.
 * 
 * @param {Object} props - Props del componente
 * @param {React.ReactNode} props.children - Componentes hijos
 * @returns {JSX.Element} Provider del contexto
 */
export function AuthProvider({ children }) {
  // ===== ESTADOS DEL CONTEXTO =====
  
  /** @type {[Object|null, Function]} Usuario actual autenticado */
  const [currentUser, setCurrentUser] = useState(null);
  
  /** @type {[string|null, Function]} Token ID de Firebase */
  const [idToken, setIdToken] = useState(null);
  
  /** @type {[boolean, Function]} Indicador de permisos de administrador */
  const [isAdmin, setIsAdmin] = useState(false);
  
  /** @type {[boolean, Function]} Estado de carga durante autenticación */
  const [loading, setLoading] = useState(true);
  
  /** @type {[Object|null, Function]} Información del perfil del usuario */
  const [userProfile, setUserProfile] = useState(null);
  
  /** @type {[string|null, Function]} Mensaje de error de autenticación */
  const [authError, setAuthError] = useState(null);
  
  /** @type {[boolean, Function]} Indicador de token próximo a expirar */
  const [tokenExpiring, setTokenExpiring] = useState(false);

  // ===== FUNCIONES AUXILIARES =====

  /**
   * Actualiza el token y claims del usuario
   * 
   * Obtiene un nuevo token ID de Firebase y actualiza los claims
   * personalizados (como rol de admin). Maneja la persistencia
   * en localStorage.
   * 
   * @param {Object} user - Usuario de Firebase
   * @param {boolean} forceRefresh - Forzar renovación del token
   * @returns {Promise<string>} Token ID actualizado
   */
  const refreshTokenAndClaims = async (user, forceRefresh = false) => {
    try {
      if (!user) {
        throw new Error('Usuario no proporcionado para renovación de token');
      }

      // Obtener nuevo token ID
      const token = await user.getIdToken(forceRefresh);
      
      // Obtener claims personalizados
      const tokenResult = await user.getIdTokenResult();
      const customClaims = tokenResult.claims;
      
      // Actualizar estados
      setIdToken(token);
      setIsAdmin(Boolean(customClaims?.admin));
      
      // Persistir en localStorage
      localStorage.setItem("idToken", token);
      localStorage.setItem("userClaims", JSON.stringify(customClaims));
      
      // Limpiar errores
      setAuthError(null);
      
      // Calcular tiempo de expiración y establecer advertencia
      const expirationTime = tokenResult.expirationTime;
      const timeUntilExpiration = new Date(expirationTime).getTime() - Date.now();
      
      if (timeUntilExpiration <= TOKEN_WARNING_THRESHOLD) {
        setTokenExpiring(true);
      } else {
        setTokenExpiring(false);
      }
      
      return token;
      
    } catch (error) {
      console.error('Error al renovar token y claims:', error);
      setAuthError('Error al renovar credenciales de autenticación');
      throw error;
    }
  };

  /**
   * Obtiene un token ID actualizado
   * 
   * @param {boolean} forceRefresh - Forzar renovación desde Firebase
   * @returns {Promise<string|null>} Token ID o null si no hay usuario
   */
  const getIdToken = async (forceRefresh = false) => {
    try {
      if (!currentUser) {
        return null;
      }
      
      const token = await currentUser.getIdToken(forceRefresh);
      setIdToken(token);
      localStorage.setItem("idToken", token);
      
      return token;
      
    } catch (error) {
      console.error('Error al obtener token ID:', error);
      setAuthError('Error al obtener credenciales de autenticación');
      return null;
    }
  };

  /**
   * Función estable para obtener token fresco
   * 
   * Utiliza useCallback para mantener referencia estable
   * que puede ser usada como dependencia en useEffect.
   */
  const getFreshToken = useCallback(() => {
    return getIdToken(true);
  }, [currentUser]);

  /**
   * Registra un evento de auditoría de forma segura
   * 
   * @param {string} eventType - Tipo de evento
   * @param {Object} details - Detalles del evento
   * @param {string} severity - Nivel de severidad
   */
  const logAuditEvent = async (eventType, details = {}, severity = 'INFO') => {
    try {
      await auditAPI.logEvent(eventType, {
        ...details,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        ipAddress: 'client-side' // En producción se obtendría del servidor
      }, severity);
    } catch (error) {
      console.warn(`Error al registrar evento de auditoría ${eventType}:`, error);
    }
  };

  // ===== FUNCIONES DE AUTENTICACIÓN =====

  /**
   * Registra un nuevo usuario en el sistema
   * 
   * Crea una cuenta de usuario con email y contraseña,
   * actualiza los tokens y registra el evento en auditoría.
   * 
   * @param {string} email - Dirección de correo electrónico
   * @param {string} password - Contraseña del usuario
   * @param {Object} additionalInfo - Información adicional del perfil
   * @returns {Promise<Object>} Usuario creado
   */
  const signup = async (email, password, additionalInfo = {}) => {
    try {
      setLoading(true);
      setAuthError(null);
      
      // Crear usuario en Firebase
      const { user } = await createUserWithEmailAndPassword(auth, email, password);
      
      // Actualizar perfil si se proporciona información adicional
      if (additionalInfo.displayName) {
        await updateProfile(user, {
          displayName: additionalInfo.displayName
        });
      }
      
      // Actualizar tokens y claims
      await refreshTokenAndClaims(user, true);
      
      // Registrar evento de auditoría
      await logAuditEvent("AUTHENTICATION", {
        action: "SIGNUP",
        email: user.email,
        userId: user.uid,
        success: true
      }, 'INFO');
      
      return user;
      
    } catch (error) {
      console.error('Error en registro:', error);
      
      // Registrar evento de auditoría para fallos
      await logAuditEvent("AUTHENTICATION", {
        action: "SIGNUP_FAILED",
        email: email,
        error: error.code || error.message,
        success: false
      }, 'WARNING');
      
      setAuthError(getErrorMessage(error));
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Inicia sesión de usuario existente
   * 
   * Autentica al usuario con email y contraseña,
   * actualiza tokens y registra el evento.
   * 
   * @param {string} email - Dirección de correo electrónico
   * @param {string} password - Contraseña del usuario
   * @returns {Promise<Object>} Usuario autenticado
   */
  const login = async (email, password) => {
    try {
      setLoading(true);
      setAuthError(null);
      
      // Autenticar con Firebase
      const { user } = await signInWithEmailAndPassword(auth, email, password);
      
      // Actualizar tokens y claims
      await refreshTokenAndClaims(user, true);
      
      // Registrar evento de auditoría
      await logAuditEvent("AUTHENTICATION", {
        action: "LOGIN",
        email: user.email,
        userId: user.uid,
        success: true,
        lastLoginTime: new Date().toISOString()
      }, 'INFO');
      
      return user;
      
    } catch (error) {
      console.error('Error en login:', error);
      
      // Registrar evento de auditoría para fallos
      await logAuditEvent("AUTHENTICATION", {
        action: "LOGIN_FAILED",
        email: email,
        error: error.code || error.message,
        success: false
      }, 'WARNING');
      
      setAuthError(getErrorMessage(error));
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Cierra la sesión del usuario actual
   * 
   * Registra el evento de logout, limpia todos los estados
   * y elimina datos de localStorage de forma segura.
   * 
   * @returns {Promise<void>}
   */
  const logout = async () => {
    try {
      setLoading(true);
      
      // Registrar evento de auditoría antes del logout
      if (currentUser) {
        await logAuditEvent("AUTHENTICATION", {
          action: "LOGOUT",
          email: currentUser.email,
          userId: currentUser.uid,
          success: true,
          sessionDuration: Date.now() - (currentUser.metadata?.lastSignInTime ? 
            new Date(currentUser.metadata.lastSignInTime).getTime() : Date.now())
        }, 'INFO');
      }
      
      // Cerrar sesión en Firebase
      await signOut(auth);
      
      // Limpiar todos los estados
      setCurrentUser(null);
      setIdToken(null);
      setIsAdmin(false);
      setUserProfile(null);
      setAuthError(null);
      setTokenExpiring(false);
      
      // Limpiar localStorage
      localStorage.removeItem("idToken");
      localStorage.removeItem("userClaims");
      localStorage.removeItem("userProfile");
      
    } catch (error) {
      console.error('Error en logout:', error);
      
      // Registrar evento de auditoría para fallos
      await logAuditEvent("AUTHENTICATION", {
        action: "LOGOUT_FAILED",
        error: error.code || error.message,
        success: false
      }, 'ERROR');
      
      setAuthError('Error al cerrar sesión');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Actualiza el perfil del usuario
   * 
   * @param {Object} profileData - Datos del perfil a actualizar
   * @returns {Promise<void>}
   */
  const updateUserProfile = async (profileData) => {
    try {
      if (!currentUser) {
        throw new Error('No hay usuario autenticado');
      }
      
      // Actualizar perfil en Firebase
      await updateProfile(currentUser, profileData);
      
      // Actualizar estado local
      setUserProfile(prev => ({ ...prev, ...profileData }));
      
      // Persistir en localStorage
      localStorage.setItem("userProfile", JSON.stringify({
        ...userProfile,
        ...profileData
      }));
      
      // Registrar evento de auditoría
      await logAuditEvent("USER_PROFILE", {
        action: "PROFILE_UPDATED",
        userId: currentUser.uid,
        updatedFields: Object.keys(profileData)
      }, 'INFO');
      
    } catch (error) {
      console.error('Error al actualizar perfil:', error);
      setAuthError('Error al actualizar perfil de usuario');
      throw error;
    }
  };

  // ===== FUNCIONES AUXILIARES =====

  /**
   * Convierte códigos de error de Firebase a mensajes legibles
   * 
   * @param {Object} error - Error de Firebase
   * @returns {string} Mensaje de error legible
   */
  const getErrorMessage = (error) => {
    const errorMessages = {
      'auth/user-not-found': 'Usuario no encontrado',
      'auth/wrong-password': 'Contraseña incorrecta',
      'auth/email-already-in-use': 'El email ya está en uso',
      'auth/weak-password': 'La contraseña es demasiado débil',
      'auth/invalid-email': 'Formato de email inválido',
      'auth/user-disabled': 'Cuenta de usuario deshabilitada',
      'auth/too-many-requests': 'Demasiados intentos fallidos. Intenta más tarde',
      'auth/network-request-failed': 'Error de conexión. Verifica tu internet',
      'auth/invalid-credential': 'Credenciales inválidas'
    };
    
    return errorMessages[error.code] || error.message || 'Error desconocido';
  };

  /**
   * Limpia el error de autenticación
   */
  const clearAuthError = () => {
    setAuthError(null);
  };

  // ===== EFECTOS =====

  /**
   * Efecto para escuchar cambios en el estado de autenticación
   * 
   * Se ejecuta cuando Firebase detecta cambios en la autenticación
   * y actualiza todos los estados correspondientes.
   */
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      try {
        setCurrentUser(user);
        
        if (user) {
          // Usuario autenticado - actualizar tokens y claims
          await refreshTokenAndClaims(user);
          
          // Cargar perfil desde localStorage si existe
          const savedProfile = localStorage.getItem("userProfile");
          if (savedProfile) {
            try {
              setUserProfile(JSON.parse(savedProfile));
            } catch (e) {
              console.warn('Error al cargar perfil desde localStorage:', e);
            }
          }
          
        } else {
          // Usuario no autenticado - limpiar estados
          setIdToken(null);
          setIsAdmin(false);
          setUserProfile(null);
          setAuthError(null);
          setTokenExpiring(false);
          
          // Limpiar localStorage
          localStorage.removeItem("idToken");
          localStorage.removeItem("userClaims");
          localStorage.removeItem("userProfile");
        }
        
      } catch (error) {
        console.error('Error en listener de autenticación:', error);
        setAuthError('Error al procesar cambio de autenticación');
      } finally {
        setLoading(false);
      }
    });

    return unsubscribe;
  }, []);

  /**
   * Efecto para renovación automática de tokens
   * 
   * Establece un intervalo para renovar el token cada 50 minutos
   * y prevenir expiraciones inesperadas.
   */
  useEffect(() => {
    if (!currentUser) return;
    
    const intervalId = setInterval(async () => {
      try {
        await getIdToken(true);
        console.log('Token renovado automáticamente');
      } catch (error) {
        console.error('Error en renovación automática de token:', error);
        setAuthError('Error al renovar sesión automáticamente');
      }
    }, TOKEN_REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [currentUser]);

  /**
   * Efecto para advertencia de expiración de token
   * 
   * Monitorea el token y muestra advertencias cuando está próximo a expirar.
   */
  useEffect(() => {
    if (!idToken || !currentUser) return;
    
    const checkTokenExpiration = async () => {
      try {
        const tokenResult = await currentUser.getIdTokenResult();
        const expirationTime = new Date(tokenResult.expirationTime).getTime();
        const timeUntilExpiration = expirationTime - Date.now();
        
        if (timeUntilExpiration <= TOKEN_WARNING_THRESHOLD && timeUntilExpiration > 0) {
          setTokenExpiring(true);
        } else {
          setTokenExpiring(false);
        }
      } catch (error) {
        console.error('Error al verificar expiración de token:', error);
      }
    };
    
    checkTokenExpiration();
    const intervalId = setInterval(checkTokenExpiration, 60000); // Verificar cada minuto
    
    return () => clearInterval(intervalId);
  }, [idToken, currentUser]);

  // ===== VALOR DEL CONTEXTO =====

  /**
   * Valor memoizado del contexto para optimizar re-renders
   */
  const contextValue = useMemo(() => ({
    // Estados
    currentUser,
    idToken,
    isAdmin,
    loading,
    userProfile,
    authError,
    tokenExpiring,
    
    // Funciones de autenticación
    signup,
    login,
    logout,
    updateUserProfile,
    
    // Funciones de token
    getFreshToken,
    getIdToken: () => getIdToken(false),
    refreshToken: () => getIdToken(true),
    
    // Funciones auxiliares
    clearAuthError,
    
    // Información de estado
    isAuthenticated: !!currentUser,
    hasValidToken: !!idToken,
    userRole: isAdmin ? 'admin' : 'user'
  }), [
    currentUser,
    idToken,
    isAdmin,
    loading,
    userProfile,
    authError,
    tokenExpiring,
    getFreshToken
  ]);

  // ===== RENDERIZADO =====

  /**
   * No renderizar hijos hasta que termine la carga inicial
   * Esto previene flickering y comportamientos inesperados
   */
  if (loading) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-loading-spinner">
          <div className="spinner">⏳</div>
          <p>Verificando autenticación...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}
