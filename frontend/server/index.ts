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
  const backendHost = process.env.BACKEND_URL;
  
  if (backendHost) {
    const target = backendHost.startsWith("http") ? backendHost : `http://${backendHost}`;
    console.log(`Setting up API proxy to: ${target}`);
    
    // Use context matching instead of mounting on /api
    // This prevents Express from stripping the /api prefix
    app.use(
      createProxyMiddleware(["/api"], {
        target: target,
        changeOrigin: true,
        // No pathRewrite needed because we want to pass /api/... exactly as is
        on: {
          proxyReq: (proxyReq, req, res) => {
            console.log(`[Proxy] ${req.method} ${req.url} -> ${target}${req.url}`);
          },
          proxyRes: (proxyRes, req, res) => {
            console.log(`[Proxy] Response: ${proxyRes.statusCode} ${req.url}`);
          },
          error: (err, req, res) => {
            console.error(`[Proxy] Error: ${err.message}`);
          }
        }
      })
    );
  } else {
    console.warn("BACKEND_URL not set. API proxy will not work.");
  }

  // Serve static files from dist/public in production
  const staticPath = path.resolve(__dirname, "public");
  console.log(`Serving static files from: ${staticPath}`);

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
