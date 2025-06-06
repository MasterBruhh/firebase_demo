/**
 * Configuración de Firebase - Inicialización y Servicios
 * 
 * Este módulo se encarga de la configuración e inicialización de Firebase
 * para la aplicación frontend. Proporciona acceso a los servicios de
 * Authentication, Storage y otros servicios de Firebase necesarios.
 * 
 * Servicios de Firebase utilizados:
 * - Firebase Authentication: Autenticación de usuarios
 * - Firebase Storage: Almacenamiento de archivos
 * - Firebase Firestore: Base de datos (si se añade en el futuro)
 * 
 * Configuración de seguridad:
 * - Validación de configuración de Firebase
 * - Manejo seguro de errores de inicialización
 * - Configuración separada para desarrollo y producción
 * - Logging de estado de inicialización
 * 
 * Variables de entorno requeridas:
 * - VITE_FIREBASE_API_KEY: Clave API de Firebase
 * - VITE_FIREBASE_AUTH_DOMAIN: Dominio de autenticación
 * - VITE_FIREBASE_PROJECT_ID: ID del proyecto Firebase
 * - VITE_FIREBASE_STORAGE_BUCKET: Bucket de almacenamiento
 * - VITE_FIREBASE_MESSAGING_SENDER_ID: ID del remitente de mensajes
 * - VITE_FIREBASE_APP_ID: ID de la aplicación
 * 
 * Características de seguridad:
 * - Validación de configuración antes de inicialización
 * - Manejo graceful de errores de conexión
 * - Configuración específica para desarrollo vs producción
 * - Logging controlado de información sensible
 * 
 * Uso:
 * ```javascript
 * import { auth, storage } from '../services/firebase';
 * 
 * // Usar autenticación
 * import { signInWithEmailAndPassword } from 'firebase/auth';
 * await signInWithEmailAndPassword(auth, email, password);
 * 
 * // Usar almacenamiento
 * import { ref, uploadBytes } from 'firebase/storage';
 * const storageRef = ref(storage, 'path/to/file');
 * await uploadBytes(storageRef, file);
 * ```
 * 
*/

import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getStorage, connectStorageEmulator } from 'firebase/storage';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

// ===== CONFIGURACIÓN =====

/**
 * Configuración de Firebase obtenida desde variables de entorno
 * 
 * En producción, estas variables deben estar configuradas en el
 * servidor o en el archivo .env. Para desarrollo local, se puede
 * usar un archivo .env.local.
 */
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAnlMW-lOQg3YmssadJp86apbtnokeu_8s",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "indexador-demo-gemini.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "indexador-demo-gemini",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "indexador-demo-gemini.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1054037908225",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1054037908225:web:cf279981cb093e3a19d900",
  // Configuración opcional para Analytics y otros servicios
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || undefined
};

/**
 * Configuración para emuladores de Firebase (desarrollo)
 */
const emulatorConfig = {
  auth: {
    host: 'localhost',
    port: 9099
  },
  firestore: {
    host: 'localhost',
    port: 8080
  },
  storage: {
    host: 'localhost',
    port: 9199
  }
};

// ===== VARIABLES GLOBALES =====

/** Instancia principal de la aplicación Firebase */
let app = null;

/** Servicio de autenticación Firebase */
let auth = null;

/** Servicio de almacenamiento Firebase */
let storage = null;

/** Servicio de base de datos Firestore */
let firestore = null;

/** Estado de inicialización */
let isInitialized = false;

/** Errores de inicialización */
let initializationError = null;

// ===== FUNCIONES AUXILIARES =====

/**
 * Valida que la configuración de Firebase sea válida
 * 
 * @param {Object} config - Configuración a validar
 * @returns {boolean} True si la configuración es válida
 */
const validateFirebaseConfig = (config) => {
  const requiredFields = [
    'apiKey',
    'authDomain', 
    'projectId',
    'storageBucket',
    'messagingSenderId',
    'appId'
  ];
  
  for (const field of requiredFields) {
    if (!config[field] || config[field].trim() === '') {
      console.error(`❌ Firebase config: Campo requerido '${field}' está vacío o no definido`);
      return false;
    }
  }
  
  // Validaciones específicas
  if (!config.storageBucket.includes('.appspot.com')) {
    console.error('❌ Firebase config: storageBucket debe terminar con .appspot.com');
    return false;
  }
  
  if (!config.authDomain.includes('.firebaseapp.com')) {
    console.error('❌ Firebase config: authDomain debe terminar con .firebaseapp.com');
    return false;
  }
  
  return true;
};

/**
 * Verifica si estamos en modo desarrollo
 * 
 * @returns {boolean} True si estamos en desarrollo
 */
const isDevelopment = () => {
  return import.meta.env.DEV || import.meta.env.MODE === 'development';
};

/**
 * Verifica si debemos usar emuladores
 * 
 * @returns {boolean} True si debemos conectar a emuladores
 */
const shouldUseEmulators = () => {
  return isDevelopment() && import.meta.env.VITE_USE_FIREBASE_EMULATORS === 'true';
};

/**
 * Configura la conexión a emuladores de Firebase
 * 
 * @param {Object} services - Servicios de Firebase a conectar
 */
const setupEmulators = (services) => {
  if (!shouldUseEmulators()) {
    return;
  }
  
  try {
    // Conectar emulador de Authentication
    if (services.auth && !services.auth._delegate._isUsingEmulator) {
      connectAuthEmulator(
        services.auth, 
        `http://${emulatorConfig.auth.host}:${emulatorConfig.auth.port}`,
        { disableWarnings: true }
      );
      console.log('🔧 Firebase Auth conectado al emulador');
    }
    
    // Conectar emulador de Storage
    if (services.storage && !services.storage._delegate._host) {
      connectStorageEmulator(
        services.storage,
        emulatorConfig.storage.host,
        emulatorConfig.storage.port
      );
      console.log('🔧 Firebase Storage conectado al emulador');
    }
    
    // Conectar emulador de Firestore
    if (services.firestore && !services.firestore._delegate._databaseId) {
      connectFirestoreEmulator(
        services.firestore,
        emulatorConfig.firestore.host,
        emulatorConfig.firestore.port
      );
      console.log('🔧 Firebase Firestore conectado al emulador');
    }
    
  } catch (error) {
    console.warn('⚠️ Error al conectar emuladores de Firebase:', error.message);
  }
};

/**
 * Registra información de diagnóstico de Firebase
 */
const logFirebaseInfo = () => {
  if (!isDevelopment()) {
    return;
  }
  
  console.group('🔥 Firebase Configuration Info');
  console.log('📊 Project ID:', firebaseConfig.projectId);
  console.log('🔐 Auth Domain:', firebaseConfig.authDomain);
  console.log('💾 Storage Bucket:', firebaseConfig.storageBucket);
  console.log('🌍 Environment:', isDevelopment() ? 'Development' : 'Production');
  console.log('🔧 Using Emulators:', shouldUseEmulators());
  console.groupEnd();
};

// ===== INICIALIZACIÓN PRINCIPAL =====

/**
 * Inicializa Firebase con manejo de errores robusto
 * 
 * @returns {Promise<boolean>} True si la inicialización fue exitosa
 */
const initializeFirebase = async () => {
  try {
    // Validar configuración antes de inicializar
    if (!validateFirebaseConfig(firebaseConfig)) {
      throw new Error('Configuración de Firebase inválida');
    }
    
    // Verificar si ya está inicializado
    if (isInitialized) {
      console.log('✅ Firebase ya está inicializado');
      return true;
    }
    
    console.log('🚀 Inicializando Firebase...');
    
    // Inicializar aplicación Firebase
    app = initializeApp(firebaseConfig);
    
    // Inicializar servicios
    auth = getAuth(app);
    storage = getStorage(app);
    firestore = getFirestore(app);
    
    // Configurar emuladores si es necesario
    setupEmulators({ auth, storage, firestore });
    
    // Marcar como inicializado
    isInitialized = true;
    initializationError = null;
    
    // Log de información en desarrollo
    logFirebaseInfo();
    
    console.log('✅ Firebase inicializado correctamente');
    return true;
    
  } catch (error) {
    console.error('❌ Error al inicializar Firebase:', error);
    
    // Almacenar error para diagnóstico
    initializationError = error;
    isInitialized = false;
    
    // En desarrollo, mostrar información adicional
    if (isDevelopment()) {
      console.group('🔍 Diagnóstico de Error Firebase');
      console.error('Error completo:', error);
      console.log('Configuración utilizada:', {
        ...firebaseConfig,
        apiKey: '***OCULTA***' // No mostrar API key completa
      });
      console.groupEnd();
      
      console.warn(
        '⚠️ La aplicación funcionará en modo limitado. ' +
        'Las características de Firebase no estarán disponibles hasta ' +
        'que se configure correctamente.'
      );
    }
    
    return false;
  }
};

// ===== FUNCIONES PÚBLICAS =====

/**
 * Obtiene el estado de inicialización de Firebase
 * 
 * @returns {Object} Estado de inicialización
 */
export const getFirebaseStatus = () => ({
  isInitialized,
  error: initializationError,
  config: {
    projectId: firebaseConfig.projectId,
    authDomain: firebaseConfig.authDomain,
    usingEmulators: shouldUseEmulators()
  }
});

/**
 * Reinicia la conexión a Firebase
 * 
 * @returns {Promise<boolean>} True si el reinicio fue exitoso
 */
export const reinitializeFirebase = async () => {
  console.log('🔄 Reiniciando Firebase...');
  isInitialized = false;
  initializationError = null;
  
  return await initializeFirebase();
};

/**
 * Verifica si Firebase está listo para usar
 * 
 * @returns {boolean} True si Firebase está inicializado y listo
 */
export const isFirebaseReady = () => {
  return isInitialized && !initializationError;
};

/**
 * Obtiene información de configuración para debugging
 * 
 * @returns {Object} Información de configuración (sin datos sensibles)
 */
export const getFirebaseConfigInfo = () => {
  if (!isDevelopment()) {
    return { message: 'Información no disponible en producción' };
  }
  
  return {
    projectId: firebaseConfig.projectId,
    authDomain: firebaseConfig.authDomain,
    storageBucket: firebaseConfig.storageBucket,
    environment: 'development',
    emulators: shouldUseEmulators(),
    initialized: isInitialized,
    hasError: !!initializationError
  };
};

// ===== INICIALIZACIÓN AUTOMÁTICA =====

// Inicializar Firebase automáticamente al cargar el módulo
initializeFirebase().then(success => {
  if (success) {
    console.log('🎉 Firebase listo para usar');
  } else {
    console.warn('⚠️ Firebase no pudo inicializarse completamente');
  }
}).catch(error => {
  console.error('💥 Error crítico en inicialización de Firebase:', error);
});

// ===== EXPORTACIONES =====

/**
 * Servicio de autenticación Firebase
 * 
 * Utilizado para todas las operaciones de autenticación:
 * login, logout, registro, gestión de sesiones, etc.
 */
export { auth };

/**
 * Servicio de almacenamiento Firebase Storage
 * 
 * Utilizado para subir, descargar y gestionar archivos
 * en Firebase Storage.
 */
export { storage };

/**
 * Servicio de base de datos Firestore
 * 
 * Utilizado para operaciones de base de datos NoSQL,
 * especialmente para almacenar metadatos y logs de auditoría.
 */
export { firestore };

/**
 * Instancia principal de la aplicación Firebase
 * 
 * Esta es la instancia raíz de Firebase que puede ser
 * utilizada para inicializar servicios adicionales.
 */
export default app;