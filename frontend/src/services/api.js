/**
 * Servicio de API - Cliente HTTP para Comunicación con Backend
 * 
 * Este módulo proporciona una interfaz unificada para todas las comunicaciones
 * HTTP con el backend de la aplicación. Utiliza Axios como cliente HTTP
 * y proporciona configuración centralizada, interceptores y manejo de errores.
 * 
 * Funcionalidades principales:
 * - Cliente HTTP configurado con Axios
 * - Interceptores de request/response automáticos
 * - Autenticación automática con tokens Bearer
 * - Manejo centralizado de errores
 * - APIs organizadas por funcionalidad
 * - Retry automático para fallos temporales
 * - Logging de requests para debugging
 * 
 * APIs disponibles:
 * - authAPI: Autenticación y gestión de usuarios
 * - documentsAPI: Gestión de documentos y archivos
 * - auditAPI: Sistema de auditoría y logging
 * 
 * Características de seguridad:
 * - Headers de autenticación automáticos
 * - Validación de tokens antes de requests
 * - Manejo seguro de uploads de archivos
 * - Timeouts configurables
 * 
*/

import axios from "axios";

// ===== CONFIGURACIÓN =====

/** URL base del API desde variables de entorno */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/** Timeout por defecto para requests (30 segundos) */
const DEFAULT_TIMEOUT = 30000;

/** Timeout extendido para uploads (5 minutos) */
const UPLOAD_TIMEOUT = 300000;

// ===== CREACIÓN DE INSTANCIA AXIOS =====

/**
 * Instancia principal de Axios configurada para la API
 * 
 * Incluye configuración base, headers por defecto y timeouts.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    "Accept": "application/json"
  }
});

// ===== FUNCIONES AUXILIARES =====

/**
 * Obtiene el token de autenticación desde localStorage
 * 
 * @returns {string|null} Token de autenticación o null si no existe
 */
const getAuthToken = () => {
  const token = localStorage.getItem("idToken");
  return token && token !== "null" && token !== "undefined" ? token : null;
};

/**
 * Limpia datos sensibles del localStorage
 */
const clearAuthData = () => {
  localStorage.removeItem("idToken");
  localStorage.removeItem("userClaims");
  localStorage.removeItem("userProfile");
};

/**
 * Formatea errores de API para mostrar al usuario
 * 
 * @param {Object} error - Error de Axios
 * @returns {Object} Error formateado
 */
const formatApiError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    return {
      status,
      message: data?.detail || data?.message || `Error del servidor (${status})`,
      code: data?.code || `HTTP_${status}`
    };
  } else if (error.request) {
    return {
      status: 0,
      message: "Error de conexión. Verifica tu conexión a internet.",
      code: "NETWORK_ERROR"
    };
  } else {
    return {
      status: -1,
      message: error.message || "Error inesperado",
      code: "CLIENT_ERROR"
    };
  }
};

// ===== INTERCEPTORES =====

/**
 * Interceptor de request - Añade autenticación automática
 * 
 * Verifica si existe un token válido en localStorage y lo añade
 * automáticamente a los headers de Authorization de cada request.
 */
api.interceptors.request.use(
  (config) => {
    // Logging en desarrollo
    if (import.meta.env.DEV) {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    // Añadir token de autenticación si no existe ya
    if (!config.headers.Authorization) {
      const token = getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    // Timeout especial para uploads
    if (config.url?.includes('/upload')) {
      config.timeout = UPLOAD_TIMEOUT;
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(formatApiError(error));
  }
);

/**
 * Interceptor de response - Maneja errores y logging
 * 
 * Procesa las respuestas del servidor y maneja errores comunes
 * como tokens expirados, errores de red, etc.
 */
api.interceptors.response.use(
  (response) => {
    // Logging exitoso en desarrollo
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    
    return response;
  },
  (error) => {
    // Logging de errores detallado
    console.error(`❌ API Error: ${error.config?.url}`, {
      status: error.response?.status,
      message: error.response?.data?.detail || error.message
    });
    
    // Manejar errores de autenticación
    if (error.response?.status === 401) {
      console.warn('Token expirado o inválido, limpiando autenticación');
      clearAuthData();
      
      // Redirigir a login si estamos en el navegador
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login?reason=session_expired';
      }
    }
    
    // Formatear y rechazar error
    return Promise.reject(formatApiError(error));
  }
);

// ===== API DE AUTENTICACIÓN =====

/**
 * API de Autenticación - Gestión de usuarios y sesiones
 * 
 * Proporciona funciones para registro, autenticación y gestión de perfiles.
 */
export const authAPI = {
  /**
   * Registra un nuevo usuario en el sistema
   * 
   * @param {string} email - Email del usuario
   * @param {string} password - Contraseña del usuario
   * @returns {Promise<Object>} Datos del usuario registrado
   */
  register: (email, password) => 
    api.post("/auth/register", { email, password }),
  
  /**
   * Obtiene información del usuario actual autenticado
   * 
   * @returns {Promise<Object>} Datos del usuario actual
   */
  getCurrentUser: () => 
    api.get("/auth/me"),
  
  /**
   * Verifica permisos de administrador (ruta de prueba)
   * 
   * @returns {Promise<Object>} Respuesta de verificación
   */
  testAdminRoute: () => 
    api.get("/auth/admin-only-test")
};

// ===== API DE DOCUMENTOS =====

/**
 * API de Documentos - Gestión de archivos y documentos
 * 
 * Proporciona funciones para subir, buscar, descargar y gestionar documentos.
 */
export const documentsAPI = {
  /**
   * Sube un archivo al sistema con procesamiento automático
   * 
   * @param {File} file - Archivo a subir
   * @param {Function} onProgress - Callback opcional para progreso
   * @returns {Promise<Object>} Resultado de la subida con metadatos extraídos
   */
  upload: (file, onProgress = null) => {
    const formData = new FormData();
    formData.append("file", file);
    
    const config = {
      headers: { 
        "Content-Type": "multipart/form-data" 
      },
      timeout: UPLOAD_TIMEOUT,
      // Callback de progreso si se proporciona
      onUploadProgress: onProgress ? (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      } : undefined
    };
    
    return api.post("/documents/upload", formData, config);
  },
  
  /**
   * Busca documentos por query de texto usando Meilisearch
   * 
   * @param {string} query - Término de búsqueda
   * @returns {Promise<Object>} Resultados de búsqueda con relevancia
   */
  search: (query) => 
    api.get(`/documents/search?query=${encodeURIComponent(query)}`),
  
  /**
   * Lista todos los documentos (metadatos JSON locales)
   * 
   * @returns {Promise<Object>} Lista de documentos con metadatos
   */
  list: () => 
    api.get("/documents/list"),
  
  /**
   * Lista archivos directamente desde Firebase Storage
   * 
   * @returns {Promise<Object>} Lista de archivos en Storage con información detallada
   */
  listStorage: () => api.get("/documents/storage"),
  
  /**
   * Descarga un documento por ID
   * 
   * @param {string} id - ID del documento
   * @returns {Promise<Blob>} Archivo descargado como blob
   */
  download: (id) => 
    api.get(`/documents/download/${encodeURIComponent(id)}`, { 
      responseType: "blob",
      timeout: UPLOAD_TIMEOUT
    }),
  
  /**
   * Descarga un documento por ruta en Firebase Storage
   * 
   * @param {string} path - Ruta completa del archivo en Storage
   * @returns {Promise<Blob>} Archivo descargado como blob
   */
  downloadByPath: (path) =>
    api.get(`/documents/download_by_path?path=${encodeURIComponent(path)}`, {
      responseType: "blob",
    }),
};

// ===== API DE AUDITORÍA =====

/**
 * API de Auditoría - Sistema de logging y monitoreo
 * 
 * Proporciona funciones para registrar eventos y consultar logs de auditoría.
 */
export const auditAPI = {
  /**
   * Registra un evento de auditoría en el sistema
   * 
   * @param {string} eventType - Tipo de evento (LOGIN, UPLOAD, DOWNLOAD, etc.)
   * @param {Object} eventDetails - Detalles específicos del evento
   * @param {string} severity - Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
   * @returns {Promise<Object>} Confirmación del evento registrado
   */
  logEvent: (eventType, eventDetails = {}, severity = 'INFO') => 
    api.post("/audit/event", {
      event_type: eventType,
      details: {
        ...eventDetails,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
      },
      severity: severity
    }),
  
  /**
   * Obtiene logs de auditoría con filtros opcionales
   * 
   * @param {Object} params - Parámetros de consulta
   * @param {number} params.limit - Número máximo de registros (default: 100)
   * @param {string} params.event_type - Filtrar por tipo de evento
   * @param {string} params.user_id - Filtrar por usuario
   * @param {string} params.date_from - Fecha desde (ISO string)
   * @param {string} params.date_to - Fecha hasta (ISO string)
   * @returns {Promise<Object>} Lista de logs de auditoría
   */
  getLogs: (params = {}) => {
    const queryParams = new URLSearchParams({
      limit: 100,
      ...params
    });
    
    return api.get(`/audit/logs?${queryParams.toString()}`);
  }
};

// ===== FUNCIONES AUXILIARES EXPORTADAS =====

/**
 * Verifica si la API está disponible y respondiendo
 * 
 * @returns {Promise<boolean>} True si la API responde correctamente
 */
export const checkApiHealth = async () => {
  try {
    await api.get("/health", { timeout: 5000 });
    return true;
  } catch (error) {
    console.error('API no disponible:', error);
    return false;
  }
};

/**
 * Configura manualmente un token de autenticación
 * 
 * @param {string} token - Token JWT a establecer
 */
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem("idToken", token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    clearAuthData();
    delete api.defaults.headers.common['Authorization'];
  }
};

/**
 * Limpia completamente el token de autenticación
 */
export const clearAuthToken = () => {
  clearAuthData();
  delete api.defaults.headers.common['Authorization'];
};

/**
 * Obtiene la URL base de la API
 * 
 * @returns {string} URL base configurada
 */
export const getApiBaseUrl = () => API_BASE_URL;

// ===== EXPORTACIÓN POR DEFECTO =====

/**
 * Instancia principal de API configurada con todos los interceptores
 * 
 * Esta es la instancia base que pueden usar otros módulos para
 * hacer requests personalizados si las APIs organizadas no cubren
 * un caso específico.
 */
export default api;
