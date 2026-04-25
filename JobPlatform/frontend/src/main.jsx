import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { initializeTheme } from "./services/theme";

/*
  Initialize the saved theme before the app renders.
  To avoid a flash of the wrong theme on page load.
*/
initializeTheme();

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <BrowserRouter>
            <App />
        </BrowserRouter>
    </React.StrictMode>
);
