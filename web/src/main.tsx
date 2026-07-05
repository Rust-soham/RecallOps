import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { App } from "./App"
import { Landing } from "./Landing"
import "./styles.css"

const page = window.location.pathname === "/dashboard" ? <App /> : <Landing />

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {page}
  </StrictMode>,
)
