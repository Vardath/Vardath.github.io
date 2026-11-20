"""Command line entrypoint for training, chatting and serving from scratch."""
from __future__ import annotations
import argparse
from pathlib import Path
import torch
from .engine import LocalChatEngine
from .training import train
from .server import serve
from .model import ModelConfig, describe

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WEIGHTS = ROOT / "checkpoints" / "starter.pt"
DEFAULT_DATA = ROOT / "data" / "starter.jsonl"


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m vardath_chat", description="Local transformer trained from random initialization")
    sub = p.add_subparsers(dest="action", required=True)
    t = sub.add_parser("train", help="Train a new model from scratch or continue prior weights")
    t.add_argument("--data", type=Path, default=DEFAULT_DATA)
    t.add_argument("--out", type=Path, default=DEFAULT_WEIGHTS)
    t.add_argument("--steps", type=int, default=800)
    t.add_argument("--batch", type=int, default=12)
    t.add_argument("--context", type=int, default=256)
    t.add_argument("--width", type=int, default=96)
    t.add_argument("--layers", type=int, default=3)
    t.add_argument("--heads", type=int, default=4)
    t.add_argument("--lr", type=float, default=0.0008)
    t.add_argument("--threads", type=int, default=4)
    t.add_argument("--resume", action="store_true")
    t.add_argument("--save-every", type=int, default=100)
    c = sub.add_parser("chat", help="Interactive conversation with local weights")
    c.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    c.add_argument("--temperature", type=float, default=0.35)
    c.add_argument("--max-tokens", type=int, default=96)
    s = sub.add_parser("serve", help="Serve an OpenAI-like local HTTP chat API")
    s.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    s.add_argument("--port", type=int, default=8080)
    d = sub.add_parser("describe", help="Print model architecture and parameter count")
    args = p.parse_args()
    if args.action == "train":
        train(args.data, args.out, steps=args.steps, batch=args.batch,
              context=args.context, width=args.width, layers=args.layers,
              heads=args.heads, lr=args.lr, threads=args.threads,
              save_every=args.save_every, resume=args.resume)
    elif args.action == "serve":
        torch.set_num_threads(4)
        serve(args.weights, port=args.port)
    elif args.action == "describe":
        print(describe(ModelConfig()))
    elif args.action == "chat":
        torch.set_num_threads(4)
        engine = LocalChatEngine(args.weights)
        history: list[dict] = []
        print("Vardath Scratch Chat; model trained locally from scratch. /quit exits, /clear resets history.")
        while True:
            try:
                question = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if question.lower() in {"/quit", "/exit"}:
                break
            if question.lower() == "/clear":
                history.clear()
                print("Cleared.")
                continue
            if not question:
                continue
            history.append({"role": "user", "content": question})
            answer = engine.reply(history, max_tokens=args.max_tokens, temperature=args.temperature)
            print(f"Model> {answer}")
            history.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()
