"""Exercise the browser-to-Modal proxy handshake without loading a model."""
import base64
import unittest
import aiohttp
from aiohttp import web
from aiohttp.test_utils import TestServer
from protected_haru import protect_app

PASSWORD = "test-only-password-" * 3
AUTH = "Basic " + base64.b64encode(("haru:" + PASSWORD).encode()).decode()

class ProxyHandshakeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        app = web.Application()
        async def chat(request):
            socket = web.WebSocketResponse()
            await socket.prepare(request)
            await socket.send_bytes(b"\x00")
            await socket.send_bytes(b"\x02Japanese speech handshake")
            await socket.receive(timeout=2)
            return socket
        app.router.add_get("/api/chat", chat)
        self.server = TestServer(protect_app(app, PASSWORD))
        await self.server.start_server()

    async def asyncTearDown(self):
        await self.server.close()

    async def receive_handshake(self, offer):
        headers = {"Authorization": AUTH}
        if offer:
            # Modal forwards Chrome's offer but its upstream ws_connect has
            # compress=0. Reproduce that exact mismatch, then require plain frames.
            headers["Sec-WebSocket-Extensions"] = "permessage-deflate; client_max_window_bits"
        async with aiohttp.ClientSession() as client:
            async with client.ws_connect(self.server.make_url("/api/chat"),
                                         headers=headers, compress=0) as socket:
                message = await socket.receive(timeout=2)
                self.assertEqual(message.type, aiohttp.WSMsgType.BINARY, str(socket.exception()))
                self.assertEqual(message.data, b"\x00")
                text = await socket.receive(timeout=2)
                self.assertEqual(text.data, b"\x02Japanese speech handshake")
                await socket.send_bytes(b"\x06")

    async def test_browser_offer_through_noncompressing_proxy(self):
        await self.receive_handshake(True)

    async def test_plain_client_remains_supported(self):
        await self.receive_handshake(False)

    async def test_unauthenticated_websocket_is_rejected(self):
        async with aiohttp.ClientSession() as client:
            with self.assertRaises(aiohttp.WSServerHandshakeError) as raised:
                await client.ws_connect(self.server.make_url("/api/chat"))
            self.assertEqual(raised.exception.status, 401)
