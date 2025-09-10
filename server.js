#!/usr/bin/env node
import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import { config } from 'dotenv';

config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// SSE endpoint for streaming LLM responses
app.post('/sse/prompt', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  });

  const { prompt, model = 'gpt-4o-mini', system, temperature, max_tokens } = req.body;
  
  const args = ['llm', prompt, '-m', model];
  
  if (system) args.push('-s', system);
  if (temperature) args.push('-t', temperature.toString());
  if (max_tokens) args.push('--max-tokens', max_tokens.toString());

  const env = { ...process.env };
  if (process.env.OPENAI_API_KEY) {
    env.OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  }

  const child = spawn('uvx', args, { env });

  child.stdout.on('data', (data) => {
    res.write(`data: ${JSON.stringify({ text: data.toString() })}\n\n`);
  });

  child.stderr.on('data', (data) => {
    res.write(`data: ${JSON.stringify({ error: data.toString() })}\n\n`);
  });

  child.on('close', (code) => {
    res.write(`data: ${JSON.stringify({ done: true, code })}\n\n`);
    res.end();
  });

  req.on('close', () => {
    child.kill();
  });
});

// Regular REST endpoints
app.post('/prompt', async (req, res) => {
  const { prompt, model = 'gpt-4o-mini', system, temperature, max_tokens } = req.body;
  
  const args = ['llm', prompt, '-m', model];
  
  if (system) args.push('-s', system);
  if (temperature) args.push('-t', temperature.toString());
  if (max_tokens) args.push('--max-tokens', max_tokens.toString());

  const env = { ...process.env };
  if (process.env.OPENAI_API_KEY) {
    env.OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  }

  const child = spawn('uvx', args, { env });
  
  let output = '';
  let error = '';

  child.stdout.on('data', (data) => {
    output += data.toString();
  });

  child.stderr.on('data', (data) => {
    error += data.toString();
  });

  child.on('close', (code) => {
    if (code !== 0) {
      res.status(500).json({ error: error || 'Command failed' });
    } else {
      res.json({ response: output });
    }
  });
});

app.get('/models', async (req, res) => {
  const child = spawn('uvx', ['llm', 'models', 'list']);
  
  let output = '';
  let error = '';

  child.stdout.on('data', (data) => {
    output += data.toString();
  });

  child.stderr.on('data', (data) => {
    error += data.toString();
  });

  child.on('close', (code) => {
    if (code !== 0) {
      res.status(500).json({ error: error || 'Command failed' });
    } else {
      res.json({ models: output.split('\n').filter(Boolean) });
    }
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// MCP protocol endpoints
app.post('/mcp/tools/list', (req, res) => {
  res.json({
    tools: [
      {
        name: 'prompt',
        description: 'Send a prompt to an LLM model',
        inputSchema: {
          type: 'object',
          properties: {
            prompt: { type: 'string' },
            model: { type: 'string', default: 'gpt-4o-mini' },
            system: { type: 'string' },
            temperature: { type: 'number' },
            max_tokens: { type: 'number' }
          },
          required: ['prompt']
        }
      },
      {
        name: 'list_models',
        description: 'List available LLM models'
      }
    ]
  });
});

app.post('/mcp/tools/call', async (req, res) => {
  const { name, arguments: args } = req.body;
  
  if (name === 'prompt') {
    const response = await fetch(`http://localhost:${PORT}/prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(args)
    });
    const data = await response.json();
    res.json({ content: [{ type: 'text', text: data.response || data.error }] });
  } else if (name === 'list_models') {
    const response = await fetch(`http://localhost:${PORT}/models`);
    const data = await response.json();
    res.json({ content: [{ type: 'text', text: data.models.join('\n') }] });
  } else {
    res.status(400).json({ error: 'Unknown tool' });
  }
});

app.listen(PORT, () => {
  console.log(`LLM SSE/MCP Server running on port ${PORT}`);
});