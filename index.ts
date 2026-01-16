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
    
    app.use(
      "/api",
      createProxyMiddleware({
        target: target,
        changeOrigin: true,
        // IMPORTANT: We do NOT want to strip /api because the backend expects /api/homepage/v1
        // However, http-proxy-middleware mounted on /api might strip it depending on version/config.
        // We explicitly rewrite it to ensure it matches what FastAPI expects.
        pathRewrite: (path, req) => {
          // If path is /homepage/v1 (stripped), add /api back
          // If path is /api/homepage/v1 (preserved), keep it
          // The safest way is to ensure the target path starts with /api
          
          // Actually, when using app.use('/api', ...), the 'path' argument here is relative to the mount point.
          // So if request is /api/foo, path is /foo.
          // We want to send /api/foo to the backend.
          return `/api${path}`; 
        },
        on: {
          proxyReq: (proxyReq, req, res) => {
            console.log(`[Proxy] ${req.method} ${req.url} -> ${target}${proxyReq.path}`);
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
