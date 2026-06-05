# Variantes de configuración MCP (Google Search Console)

> Preservadas el 2026-06-05 antes de consolidar el repo en `main` y borrar las
> ramas `claude/*`. Son tres enfoques distintos para conectar el MCP de Search
> Console. Se conservan aquí para no perder el trabajo de configuración.

## A) `main` — paquete oficial Anthropic (npx)

```json
{
  "mcpServers": {
    "google-search-console": {
      "command": "npx",
      "args": ["-y", "@anthropics/mcp-google-search-console"]
    }
  }
}
```

## B) `claude/get-click-data-lsQg6` — módulo Python `gsc_mcp_server` (con site URL real)

Esta es la más completa: lleva la URL del sitio y la ruta de credenciales ya configuradas.

```json
{
  "mcpServers": {
    "google-search-console": {
      "command": "python3",
      "args": ["-m", "gsc_mcp_server"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/adrihosan/.config/gsc/credentials.json",
        "GSC_SITE_URL": "https://www.adrihosan.com/"
      }
    }
  }
}
```

## C) `claude/top-pages-last-month-RY2i9` — paquete `mcp-server-gsc` (npx)

⚠️ Ojo: la ruta de credenciales tenía un typo (`/Users/adrhosan/` sin la "i"). Corregido abajo.

```json
{
  "mcpServers": {
    "gsc": {
      "command": "npx",
      "args": ["-y", "mcp-server-gsc"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/adrihosan/.config/gsc/credentials.json"
      }
    }
  }
}
```
