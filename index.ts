import express from "express";
import { createServer } from "http";
import path from "path";
import { fileURLToPath } from "url";
import { createProxyMiddleware } from "http-proxy-middleware";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);

  // Proxy API requests to the backend
  // In Render, BACKEND_URL will be provided as "host:port"
  // We need to prepend http:// if it's missing
  const backendHost = process.env.BACKEND_URL;
  
  if (backendHost) {
    const target = backendHost.startsWith("http") ? backendHost : `http://${backendHost}`;
    console.log(`Setting up API proxy to: ${target}`);
    
    app.use(
      "/api",
      createProxyMiddleware({
        target: target,
        changeOrigin: true,
        pathRewrite: {
          // Keep the /api prefix or remove it depending on backend. 
          // Our backend expects /api/homepage/v1, so we keep it.
        },
      })
    );
  } else {
    console.warn("BACKEND_URL not set. API proxy will not work.");
  }

  // Serve static files from dist/public in production
  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.static(staticPath));

  // Handle client-side routing - serve index.html for all routes
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

startServer().catch(console.error);
