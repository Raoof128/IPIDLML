#!/usr/bin/env python3
"""
IPI-Shield Development Server Launcher

Quick start:
    python run.py

With options:
    python run.py --port 8080 --reload
"""

import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run IPI-Shield server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print("🛡️ Starting IPI-Shield...")
    print(f"   Dashboard: http://{args.host}:{args.port}/dashboard")
    print(f"   API Docs:  http://{args.host}:{args.port}/docs")
    print()

    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
