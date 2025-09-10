# LLM MCP Server

MCP (Model Context Protocol) server wrapper for Simon Willison's LLM CLI tool.

## Features

- Send prompts to LLM models
- Chat with LLM models
- List available models
- Install new models/providers
- OpenAI API key integration

## Setup

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key
```

3. Run the server:
```bash
npm start
```

### Deploy to Render

1. Fork/push this repository to GitHub
2. Connect your GitHub repo to Render
3. Add your `OPENAI_API_KEY` in Render's environment variables
4. Deploy using the included `render.yaml` configuration

## MCP Client Configuration

Add to your Claude Desktop or other MCP client configuration:

```json
{
  "mcpServers": {
    "llm-cli": {
      "command": "node",
      "args": ["/path/to/llm-mcp/index.js"],
      "env": {
        "OPENAI_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

- `prompt`: Send a single prompt to an LLM
- `chat`: Interactive chat with an LLM
- `list_models`: List available models
- `install_model`: Install new models or providers

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for GPT models