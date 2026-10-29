"""Windows-compatible FastAPI entry point: MQTT needs a selector event loop."""
import argparse
import asyncio
import sys

import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = uvicorn.Server(uvicorn.Config('app.main:app', host=args.host, port=args.port, loop='none'))
    if sys.platform == 'win32':
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(server.serve())


if __name__ == '__main__':
    main()
