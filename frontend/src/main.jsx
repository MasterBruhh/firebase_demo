/**
 * Punto de entrada principal de la aplicación React
 * 
 * Este archivo es responsable de montar la aplicación React en el DOM.
 * Configura el renderizado inicial y las optimizaciones para producción.
 * 
 * Características:
 * - Renderizado eficiente con createRoot (React 18+)
 * - Importación de estilos globales
 * - Configuración para modo StrictMode en desarrollo
 * - Optimizaciones para producción
 * 
 * @author Firebase Demo Project
 * @version 1.0.0
 * @since 2024
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// Obtener el elemento root del DOM
const rootElement = document.getElementById("root");

// Verificar que el elemento root existe
if (!rootElement) {
  throw new Error(
    "No se encontró el elemento 'root' en el DOM. " +
    "Verifica que el archivo HTML contiene un elemento con id='root'."
  );
}

// Crear la raíz de React y renderizar la aplicación
const root = createRoot(rootElement);

/**
 * Renderizar la aplicación con configuraciones apropiadas
 * 
 * En desarrollo: Incluye StrictMode para detección de problemas
 * En producción: Renderizado optimizado sin controles adicionales
 */
if (import.meta.env.DEV) {
  // Modo desarrollo con StrictMode para debugging
  root.render(
    <StrictMode>
      <App />
    </StrictMode>
  );
} else {
  // Modo producción optimizado
  root.render(<App />);
}

// Registro de errores globales para producción
if (!import.meta.env.DEV) {
  window.addEventListener('error', (event) => {
    console.error('Error global capturado:', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error?.stack
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Promise rechazada no manejada:', {
      reason: event.reason,
      promise: event.promise
    });
  });
}
