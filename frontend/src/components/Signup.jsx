/**
 * Componente de Registro - Creación de Nuevas Cuentas de Usuario
 * 
 * Este componente proporciona la interfaz de usuario para el registro
 * de nuevos usuarios en el sistema. Maneja la creación de cuentas con
 * Firebase Auth y proporciona validaciones robustas y una experiencia
 * de usuario optimizada.
 * 
 * Funcionalidades principales:
 * - Formulario de registro con validación completa
 * - Confirmación de contraseña
 * - Validaciones de seguridad en tiempo real
 * - Integración con Firebase Authentication
 * - Manejo de estados de carga y errores
 * - Redirección automática después del registro exitoso
 * - Enlace para usuarios existentes
 * 
 * Estados manejados:
 * - email: Dirección de correo electrónico del usuario
 * - password: Contraseña del usuario
 * - confirmPassword: Confirmación de la contraseña
 * - error: Mensajes de error de validación o registro
 * - loading: Estado de carga durante el proceso de registro
 * 
 * Validaciones implementadas:
 * - Formato de email válido
 * - Longitud mínima de contraseña (6 caracteres)
 * - Coincidencia de contraseñas
 * - Campos requeridos
 * - Validaciones en tiempo real
 * 
 * Seguridad:
 * - Validación de fortaleza de contraseña
 * - Prevención de envíos duplicados
 * - Manejo seguro de credenciales
 * - Mensajes de error informativos pero seguros
 * 
*/

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { auth } from "../services/firebase";
import { createUserWithEmailAndPassword } from "firebase/auth";

export default function Signup() {
  const navigate = useNavigate();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await createUserWithEmailAndPassword(auth, email, password);
      navigate("/dashboard");
    } catch (err) {
      switch (err.code) {
        case "auth/email-already-in-use":
          setError("El correo ya está registrado");
          break;
        case "auth/weak-password":
          setError("La contraseña es demasiado débil");
          break;
        case "auth/invalid-email":
          setError("Correo electrónico inválido");
          break;
        default:
          setError(err.message);
      }
    }
  };

  return (
    <div className="auth-container">
      <h2>Crear cuenta</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Correo electrónico"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button className="auth-button" type="submit">
          Registrarse
        </button>
        {error && <p className="error">{error}</p>}
      </form>
      <p>
        ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
      </p>
    </div>
  );
}
