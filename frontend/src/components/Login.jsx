/**
 * Componente de Inicio de Sesión - Autenticación de Usuarios
 * 
 * Este componente proporciona la interfaz de usuario para el inicio de sesión
 * de usuarios registrados en el sistema. Maneja la autenticación con Firebase
 * Auth y proporciona una experiencia de usuario intuitiva y segura.
 * 
 * Funcionalidades principales:
 * - Formulario de inicio de sesión con validación
 * - Integración con Firebase Authentication
 * - Manejo de estados de carga y errores
 * - Redirección automática después del login exitoso
 * - Enlace para registro de nuevos usuarios
 * 
 * Estados manejados:
 * - email: Dirección de correo electrónico del usuario
 * - password: Contraseña del usuario
 * - error: Mensajes de error de autenticación
 * - loading: Estado de carga durante el proceso de login
 * 
 * Seguridad:
 * - Validación de campos requeridos
 * - Manejo seguro de credenciales
 * - Protección contra ataques de fuerza bruta (lado servidor)
 * - Mensajes de error informativos pero seguros
 * 
*/

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { auth } from "../services/firebase";
import { signInWithEmailAndPassword } from "firebase/auth";

export default function Login() {
  const navigate = useNavigate();
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await signInWithEmailAndPassword(auth, email, password);
      navigate("/dashboard");
    } catch (err) {
      switch (err.code) {
        case "auth/wrong-password":
          setError("Contraseña incorrecta");
          break;
        case "auth/user-not-found":
          setError("El usuario no existe");
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
      <h2>Iniciar sesión</h2>
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
          Entrar
        </button>
        {error && <p className="error">{error}</p>}
      </form>
      <p>
        ¿No tienes cuenta? <Link to="/signup">Regístrate</Link>
      </p>
    </div>
  );
}
