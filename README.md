# GPU Intelligence MCP Chatbot

MCP (Model Context Protocol) **chatbot** that queries the database created in the `gpu-bd` POC and answers questions using the OpenAI API. It includes an agent server with SQLite access and an optional web UI via OpenWebUI.

POC database repository: https://github.com/edunavata/gpu-bd.git

## Demo
<video src="media/demo-gpu-mcp.mp4" controls width="600">
  Tu navegador no admite el elemento de video.
</video>


## What this project is

- **MCP server** that exposes the POC database so the model can answer with real context.
- **OpenAI-compatible API** to integrate the chatbot with clients like OpenWebUI.
- **Docker-based stack** for fast, reproducible setup.

## Requirements

- Docker and Docker Compose
- Make
- Git
- An **OpenAI API key**

## Configuration

1) Copy or create the `.env` file with your API key:

```bash
OPENAI_API_KEY=sk-...
```

## Getting started

1) Clone this repo.
2) Run the setup to **clone the POC and create the database**:

```bash
make setup
```

3) Start the services:

```bash
docker compose up --build -d
```

Done. The stack is available at:

- **API MCP / OpenAI-compatible**: `http://localhost:8000/v1`
- **OpenWebUI**: `http://localhost:3005`

## How it works

- `make setup` clones `gpu-bd` and runs its initialization to create `gpu-bd/db/pcbuilder.db`.
- The `gpu-agent` container mounts the database as **read-only** and exposes an OpenAI-style API.
- `openwebui` connects to `gpu-agent` to interact with the chatbot in a web UI.

## Structure

- `server/`: MCP API and database query logic
- `gpu-bd/`: POC repo checkout with the DB
- `docker-compose.yml`: services and container network
- `Makefile`: automates POC clone and init

## Basic usage

- Open OpenWebUI and ask about GPUs, builds, and components stored in the database.
- You can also consume the API from any OpenAI-compatible client.

## Quick troubleshooting

- If the DB does not exist, run `make setup` again.
- If you change the DB, restart containers: `docker compose down && docker compose up --build`.
