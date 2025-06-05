// frontend/src/main.jsx
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// 👇 montamos la app sin StrictMode
createRoot(document.getElementById("root")).render(<App />);
