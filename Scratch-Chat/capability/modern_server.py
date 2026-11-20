"""Local-only OpenAI-compatible chat endpoint for *our* trained modern model.

This does NOT invoke cloud providers or wrap pretrained third-party models.
All generation is from the local model checkpoint.  Default bind is loopback.
"""
from __future__ import annotations
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
from uuid import uuid4

from capability.modern_chat import decode_tokens, encode_dialog, generate_tokens, load_chat

MODEL_ID = 'vardath-scratch-chat'
MAX_BODY = 256 * 1024


def make_handler(model, tok, inference_lock=None):
    lock = inference_lock or threading.Lock()

    class ChatHandler(BaseHTTPRequestHandler):
        def json_response(self, status, data):
            payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == '/health':
                self.json_response(200, {'status': 'running', 'model': MODEL_ID,
                                         'context': model.cfg.context_size,
                                         'trained_general_chat': False})
            elif self.path == '/v1/models':
                self.json_response(200, {'object': 'list', 'data': [{'id': MODEL_ID, 'object': 'model',
                                                                'owned_by': 'local'}]})
            else:
                self.json_response(404, {'error': {'message': 'Unknown path', 'type': 'not_found'}})

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                self.json_response(404, {'error': {'message': 'Unknown path', 'type': 'not_found'}})
                return
            try:
                size = int(self.headers.get('Content-Length', '-1'))
                if not 1 <= size <= MAX_BODY:
                    raise ValueError('Request body missing or too large')
                data = json.loads(self.rfile.read(size).decode('utf-8'))
                if not isinstance(data, dict):
                    raise ValueError('Expected a JSON object')
                if data.get('stream', False):
                    raise ValueError('Streaming is not supported by this experimental endpoint')
                if data.get('model', MODEL_ID) != MODEL_ID:
                    raise ValueError('Unknown model ID')
                messages = data.get('messages')
                max_tokens = data.get('max_tokens', 64)
                temperature = data.get('temperature', 0)
                top_p = data.get('top_p', 1.0)
                top_k = data.get('top_k', 0)
                penalty = data.get('repetition_penalty', 1.0)
                if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 256:
                    raise ValueError('max_tokens must be an integer from 1 to 256')
                if not isinstance(temperature, (int,float)) or isinstance(temperature, bool):
                    raise ValueError('temperature must be numeric')
                if not isinstance(top_p, (int,float)) or isinstance(top_p, bool):
                    raise ValueError('top_p must be numeric')
                if not isinstance(penalty, (int,float)) or isinstance(penalty, bool):
                    raise ValueError('repetition_penalty must be numeric')
                if isinstance(top_k, bool) or not isinstance(top_k, int):
                    raise ValueError('top_k must be integer')
                with lock:
                    tokens, prompt_count = generate_tokens(model, tok, messages,
                        max_new_tokens=max_tokens, temperature=float(temperature), top_p=float(top_p),
                        top_k=top_k, repetition_penalty=float(penalty))
                completion = decode_tokens(tok, tokens)
                self.json_response(200, {'id': 'chatcmpl-'+uuid4().hex, 'object': 'chat.completion',
                    'created': int(time.time()), 'model': MODEL_ID,
                    'choices': [{'index':0, 'message': {'role':'assistant','content':completion},
                                 'finish_reason': 'stop' if len(tokens)<max_tokens else 'length'}],
                    'usage': {'prompt_tokens':prompt_count, 'completion_tokens':len(tokens),
                              'total_tokens':prompt_count+len(tokens)}})
            except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self.json_response(400, {'error': {'message': str(exc), 'type':'invalid_request_error'}})

        def log_message(self, fmt, *args):
            return  # local chat prompts are not logged

    return ChatHandler


def main(argv=None):
    p=argparse.ArgumentParser(description='Standalone Vardath Scratch Chat local API')
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--tokenizer', type=Path, required=True)
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8080)
    args=p.parse_args(argv)
    if args.host not in ('127.0.0.1', 'localhost', '::1'):
        raise SystemExit('Refusing to expose unauthenticated experimental API outside loopback')
    model,tok=load_chat(args.checkpoint, args.tokenizer)
    with ThreadingHTTPServer((args.host, args.port), make_handler(model,tok)) as server:
        print('Vardath Scratch Chat API on http://%s:%d/v1 (EXPERIMENTAL)' % (args.host,args.port), flush=True)
        server.serve_forever(poll_interval=0.2)

if __name__ == '__main__': main()
