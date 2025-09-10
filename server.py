#!/usr/bin/env python3
import os
import json
import subprocess
import asyncio
from typing import Optional
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
PORT = int(os.getenv('PORT', 3000))

def run_llm_command(args):
    """Run LLM command via uvx"""
    env = os.environ.copy()
    if OPENAI_API_KEY:
        env['OPENAI_API_KEY'] = OPENAI_API_KEY
    
    cmd = ['uvx', 'llm'] + args
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        raise Exception("Command timed out")
    except Exception as e:
        logger.error(f"Error running command: {e}")
        raise

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/prompt', methods=['POST'])
def prompt():
    data = request.json
    prompt_text = data.get('prompt', '')
    model = data.get('model', 'gpt-5-nano')
    system = data.get('system')
    temperature = data.get('temperature')
    max_tokens = data.get('max_tokens')
    
    args = [prompt_text, '-m', model]
    
    if system:
        args.extend(['-s', system])
    if temperature is not None:
        args.extend(['-t', str(temperature)])
    if max_tokens is not None:
        args.extend(['--max-tokens', str(max_tokens)])
    
    try:
        output = run_llm_command(args)
        return jsonify({'response': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sse/prompt', methods=['POST'])
def sse_prompt():
    data = request.json
    prompt_text = data.get('prompt', '')
    model = data.get('model', 'gpt-5-nano')
    system = data.get('system')
    temperature = data.get('temperature')
    max_tokens = data.get('max_tokens')
    
    def generate():
        args = [prompt_text, '-m', model]
        
        if system:
            args.extend(['-s', system])
        if temperature is not None:
            args.extend(['-t', str(temperature)])
        if max_tokens is not None:
            args.extend(['--max-tokens', str(max_tokens)])
        
        env = os.environ.copy()
        if OPENAI_API_KEY:
            env['OPENAI_API_KEY'] = OPENAI_API_KEY
        
        cmd = ['uvx', 'llm'] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            for line in iter(process.stdout.readline, ''):
                if line:
                    yield f"data: {json.dumps({'text': line})}\n\n"
            
            process.wait()
            yield f"data: {json.dumps({'done': True, 'code': process.returncode})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/models')
def models():
    try:
        output = run_llm_command(['models', 'list'])
        model_list = [line.strip() for line in output.split('\n') if line.strip()]
        return jsonify({'models': model_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mcp/tools/list', methods=['POST'])
def mcp_tools_list():
    return jsonify({
        'tools': [
            {
                'name': 'prompt',
                'description': 'Send a prompt to an LLM model',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt': {'type': 'string'},
                        'model': {'type': 'string', 'default': 'gpt-5-nano'},
                        'system': {'type': 'string'},
                        'temperature': {'type': 'number'},
                        'max_tokens': {'type': 'number'}
                    },
                    'required': ['prompt']
                }
            },
            {
                'name': 'list_models',
                'description': 'List available LLM models'
            }
        ]
    })

@app.route('/mcp/tools/call', methods=['POST'])
def mcp_tools_call():
    data = request.json
    tool_name = data.get('name')
    args = data.get('arguments', {})
    
    if tool_name == 'prompt':
        try:
            output = run_llm_command([
                args.get('prompt', ''),
                '-m', args.get('model', 'gpt-5-nano')
            ])
            return jsonify({'content': [{'type': 'text', 'text': output}]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif tool_name == 'list_models':
        try:
            output = run_llm_command(['models', 'list'])
            return jsonify({'content': [{'type': 'text', 'text': output}]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Unknown tool'}), 400

if __name__ == '__main__':
    logger.info(f"Starting LLM MCP/SSE Server on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)