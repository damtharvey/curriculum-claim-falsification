#!/usr/bin/env node
/**
 * Local API for `npm run dev` in the frontend. Serves the bundled handler on
 * :3001, reading data from the repo checkout instead of S3.
 *   node dev-server.mjs   (after `npm run build`)
 */
import { createServer } from "node:http";
import { resolve } from "node:path";

process.env.LOCAL_DATA_ROOT ??= resolve(import.meta.dirname, "../..");
const { handler } = await import("./dist/handler.mjs");
const port = Number(process.env.PORT) || 3001;

createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  let body = "";
  for await (const chunk of req) body += chunk;
  const event = {
    rawPath: url.pathname,
    queryStringParameters: Object.fromEntries(url.searchParams),
    requestContext: { http: { method: req.method } },
    body: body || undefined,
  };
  const out = await handler(event);
  res.writeHead(out.statusCode ?? 200, out.headers ?? {});
  res.end(out.body ?? "");
}).listen(port, () => console.log(`API on http://localhost:${port} (data: ${process.env.LOCAL_DATA_ROOT})`));
