---
title: OpenAPI MCP Server
---

# OpenAPI MCP Server

This server dynamically creates Model Context Protocol (MCP) tools and resources from OpenAPI specifications, allowing LLMs to interact with APIs through the Model Context Protocol.

## Documentation

- [Overview](#overview) (this page)
- [Authentication](openapi-mcp-server/authentication.md) - Authentication methods and configuration
- [Deployment](openapi-mcp-server/deployment.md) - Deployment options and considerations
- [Observability](openapi-mcp-server/observability.md) - Metrics, logging, and monitoring capabilities
- [Configuration](openapi-mcp-server/configuration.md) - Complete reference for all configuration parameters

---

## Overview

{%include "../../src/openapi-mcp-server/README.md"%}

<script>
document.addEventListener('DOMContentLoaded', function() {
  // Map of source markdown files to their corresponding documentation pages
  const linkMap = {
    'AUTHENTICATION.md': 'openapi-mcp-server/authentication/',
    'DEPLOYMENT.md': 'openapi-mcp-server/deployment/',
    'OBSERVABILITY.md': 'openapi-mcp-server/observability/',
    'CONFIGURATION.md': 'openapi-mcp-server/configuration/'
  };

  // Replace links to markdown files with links to the proper pages
  const links = document.querySelectorAll('a');
  links.forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;

    // Check if the href matches any of our markdown files
    for (const [mdFile, docPage] of Object.entries(linkMap)) {
      if (href === mdFile || href.endsWith('/' + mdFile)) {
        link.href = docPage;
        break;
      }
    }
  });
});
</script>
