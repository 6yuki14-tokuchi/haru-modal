"""Haru's official Japanese demo, protected by HTTP Basic authentication."""
import base64
import hmac
import os

def accepts_authorization(value, password):
    if not password or len(password) < 32 or not isinstance(value, str):
        return False
    expected = "Basic " + base64.b64encode(("haru:" + password).encode()).decode()
    return hmac.compare_digest(value.encode(), expected.encode())

def protect_app(application, password):
    from aiohttp import web
    @web.middleware
    async def authenticate(request, handler):
        if not accepts_authorization(request.headers.get("Authorization"), password):
            return web.Response(
                status=401, text="Authentication required",
                headers={"WWW-Authenticate": 'Basic realm="Haru Japanese conversation"'},
            )
        return await handler(request)
    application.middlewares.insert(0, authenticate)
    return application

def main():
    from aiohttp import web
    from huggingface_hub import snapshot_download
    from haru.backends import LocalBackend
    from haru.server import DemoServer, ServerOptions

    password = os.environ.get("HARU_PASSWORD", "")
    if len(password) < 32:
        raise RuntimeError("Refusing to run an unprotected GPU endpoint.")
    revision = os.environ["HARU_MODEL_REVISION"]
    model_dir = snapshot_download(
        "higurashi-ai/Haru-4B",
        revision=revision,
        allow_patterns=["config.json", "tokenizer.json", "model.safetensors"],
    )
    server = DemoServer(
        LocalBackend(model_dir, device="cuda", warmup_frames=4, codec_backend="auto"),
        ServerOptions(
            default_language="ja", max_sessions=1,
            time_limit_seconds=180, webrtc="off",
        ),
    )
    application = protect_app(server.build_app(), password)
    web.run_app(application, host="0.0.0.0", port=8000, print=None, access_log=None)

if __name__ == "__main__":
    main()
