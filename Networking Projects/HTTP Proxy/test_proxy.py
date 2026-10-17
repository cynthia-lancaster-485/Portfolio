"""Automated tests for HTTPproxy.py.

Each test talks to a real proxy process over sockets. A small fake origin
server runs in a background thread so the tests can see exactly what the
proxy forwards and control what the origin sends back.

Run with:  python3 -m unittest test_proxy.py
"""

import os
import socket
import subprocess
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LAST_MODIFIED = "Tue, 01 Oct 2024 12:00:00 GMT"
BIG_BODY = bytes(range(256)) * 1200  # about 300 KB of binary data


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class FakeOrigin:
    """A tiny HTTP/1.0 origin server that records every request it receives.

    Paths:
      /simple.html  200 with Last-Modified, or 304 if If-Modified-Since is sent
      /nolm         200 without Last-Modified, or 304 if If-Modified-Since is sent
      /big          200 with a large binary body
      /missing      404 Not Found
    Every 200 response carries a unique X-Response-Id so tests can tell a
    cached copy from a fresh one.
    """

    def __init__(self):
        self.port = free_port()
        self.requests = []
        self.counter = 0
        self.lock = threading.Lock()
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", self.port))
        self.sock.listen(50)
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        with conn:
            data = b""
            conn.settimeout(5)
            try:
                while b"\r\n\r\n" not in data:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
            request = data.decode("latin-1")
            with self.lock:
                self.requests.append(request)
                self.counter += 1
                response_id = self.counter
            path = request.split(" ")[1] if " " in request else ""
            conditional = "if-modified-since:" in request.lower()
            if path.startswith("/missing"):
                body = b"not here"
                head = "HTTP/1.0 404 Not Found\r\nContent-Type: text/plain\r\n"
            elif path.startswith("/big"):
                body = BIG_BODY
                head = f"HTTP/1.0 200 OK\r\nContent-Type: application/octet-stream\r\nX-Response-Id: {response_id}\r\n"
            elif conditional and (path.startswith("/simple.html") or path.startswith("/nolm")):
                body = b""
                head = "HTTP/1.0 304 Not Modified\r\n"
            else:
                body = f"<p>response {response_id}</p>".encode()
                head = f"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nX-Response-Id: {response_id}\r\n"
                if not path.startswith("/nolm"):
                    head += f"Last-Modified: {LAST_MODIFIED}\r\n"
            head += f"Content-Length: {len(body)}\r\n\r\n"
            try:
                conn.sendall(head.encode() + body)
            except OSError:
                pass

    def count(self):
        with self.lock:
            return len(self.requests)

    def last(self):
        with self.lock:
            return self.requests[-1]

    def close(self):
        self.sock.close()


class ProxyTestCase(unittest.TestCase):
    proxy_script = os.path.join(HERE, "HTTPproxy.py")

    @classmethod
    def setUpClass(cls):
        cls.origin = FakeOrigin()
        cls.port = free_port()
        cls.proc = subprocess.Popen(
            [sys.executable, "-u", cls.proxy_script, "-a", "127.0.0.1", "-p", str(cls.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                socket.create_connection(("127.0.0.1", cls.port), timeout=0.5).close()
                return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("proxy did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()
        cls.proc.wait()
        cls.origin.close()

    def setUp(self):
        for path in ("/proxy/cache/disable", "/proxy/cache/flush",
                     "/proxy/blocklist/disable", "/proxy/blocklist/flush"):
            self.control(path)

    # Helpers

    def send(self, raw, timeout=5):
        """Send raw bytes to the proxy and return everything it sends back."""
        with socket.create_connection(("127.0.0.1", self.port), timeout=timeout) as s:
            s.sendall(raw.encode() if isinstance(raw, str) else raw)
            data = b""
            try:
                while True:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
        return data

    def url(self, path):
        return f"http://localhost:{self.origin.port}{path}"

    def get(self, path, headers=""):
        return self.send(f"GET {self.url(path)} HTTP/1.0\r\n{headers}\r\n")

    def control(self, path):
        return self.send(f"GET http://localhost:{self.origin.port}{path} HTTP/1.0\r\n\r\n")

    def status(self, response):
        return response.split(b"\r\n", 1)[0].decode("latin-1")

    def response_id(self, response):
        for line in response.split(b"\r\n"):
            if line.lower().startswith(b"x-response-id:"):
                return line.split(b":", 1)[1].strip().decode()
        return None

    def assertStatus(self, response, code):
        self.assertTrue(self.status(response).startswith(f"HTTP/1.0 {code}"),
                        f"expected {code}, got {self.status(response)!r}")


class RequestValidationTests(ProxyTestCase):
    def test_other_methods_get_501(self):
        for method in ("POST", "HEAD"):
            self.assertStatus(self.send(f"{method} {self.url('/simple.html')} HTTP/1.0\r\n\r\n"), 501)

    def test_unknown_method_gets_400(self):
        self.assertStatus(self.send(f"GIBBERISH {self.url('/simple.html')} HTTP/1.0\r\n\r\n"), 400)

    def test_malformed_request_lines_get_400(self):
        for line in ("GET something with spaces HTTP/1.0", "This should definitely not work"):
            self.assertStatus(self.send(f"{line}\r\n\r\n"), 400)

    def test_malformed_headers_get_400(self):
        for header in ("this is not a header", "Connection : close", "Connection:close"):
            self.assertStatus(self.send(f"GET {self.url('/simple.html')} HTTP/1.0\r\n{header}\r\n\r\n"), 400)

    def test_malformed_uris_get_400(self):
        for uri in (f"localhost:{self.origin.port}/simple.html", f"http://localhost:{self.origin.port}",
                    "/simple.html", "gibberish"):
            self.assertStatus(self.send(f"GET {uri} HTTP/1.0\r\n\r\n"), 400)

    def test_wrong_http_versions_get_400(self):
        for version in (" HTTP/1.1", "", " 1.0", " gibberish"):
            self.assertStatus(self.send(f"GET {self.url('/simple.html')}{version}\r\n\r\n"), 400)

    def test_error_responses_are_complete(self):
        response = self.send(f"POST {self.url('/simple.html')} HTTP/1.0\r\n\r\n")
        self.assertIn(b"\r\n\r\n", response)

    def test_rejected_requests_are_not_forwarded(self):
        before = self.origin.count()
        self.send(f"POST {self.url('/simple.html')} HTTP/1.0\r\n\r\n")
        self.send(f"GET {self.url('/simple.html')} HTTP/1.1\r\n\r\n")
        self.send(f"GET {self.url('/simple.html')} HTTP/1.0\r\nnot a header\r\n\r\n")
        time.sleep(0.3)
        self.assertEqual(self.origin.count(), before)


class ForwardingTests(ProxyTestCase):
    def test_request_uses_relative_url_and_host_header(self):
        self.get("/simple.html")
        request = self.origin.last()
        lines = request.split("\r\n")
        self.assertEqual(lines[0], "GET /simple.html HTTP/1.0")
        self.assertIn(f"Host: localhost:{self.origin.port}", lines)

    def test_connection_close_always_sent_once(self):
        for headers in ("", "Connection: close\r\n", "Connection: keep-alive\r\n"):
            self.get("/simple.html", headers)
            lines = self.origin.last().split("\r\n")
            self.assertEqual([l for l in lines if l.lower().startswith("connection:")], ["Connection: close"])

    def test_client_headers_are_kept(self):
        self.get("/simple.html", "User-Agent: TestAgent/1.0\r\nX-Custom: abc\r\n")
        lines = self.origin.last().split("\r\n")
        self.assertIn("User-Agent: TestAgent/1.0", lines)
        self.assertIn("X-Custom: abc", lines)

    def test_headers_are_well_formed(self):
        self.get("/simple.html", "User-Agent: TestAgent/1.0\r\n")
        head, _, body = self.origin.last().partition("\r\n\r\n")
        self.assertEqual(body, "")
        for line in head.split("\r\n")[1:]:
            self.assertRegex(line, r"^[^:\s]+: .+$")

    def test_query_string_is_kept(self):
        self.get("/simple.html?page=2")
        self.assertTrue(self.origin.last().startswith("GET /simple.html?page=2 HTTP/1.0"))

    def test_response_is_relayed_unchanged(self):
        response = self.get("/simple.html")
        self.assertStatus(response, 200)
        self.assertIn(b"<p>response", response)

    def test_large_binary_response(self):
        response = self.get("/big")
        self.assertTrue(response.endswith(BIG_BODY))

    def test_errors_from_origin_are_relayed(self):
        self.assertStatus(self.get("/missing"), 404)


class ConcurrencyTests(ProxyTestCase):
    def test_hanging_client_does_not_block_others(self):
        hanging = socket.create_connection(("127.0.0.1", self.port))
        try:
            start = time.time()
            response = self.get("/simple.html")
            self.assertStatus(response, 200)
            self.assertLess(time.time() - start, 3)
        finally:
            hanging.close()

    def test_many_requests_at_once(self):
        results = []
        threads = [threading.Thread(target=lambda: results.append(self.get("/simple.html"))) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(len([r for r in results if self.status(r).startswith("HTTP/1.0 200")]), 10)


class CacheTests(ProxyTestCase):
    def test_control_urls_return_200_and_are_not_forwarded(self):
        before = self.origin.count()
        for path in ("/proxy/cache/enable", "/proxy/cache/disable", "/proxy/cache/flush"):
            self.assertStatus(self.control(path), 200)
        self.assertEqual(self.origin.count(), before)

    def test_cache_disabled_by_default(self):
        first, second = self.get("/simple.html"), self.get("/simple.html")
        self.assertNotIn("if-modified-since", self.origin.last().lower())
        self.assertNotEqual(self.response_id(first), self.response_id(second))

    def test_cached_object_is_revalidated_with_conditional_get(self):
        self.control("/proxy/cache/enable")
        first = self.get("/simple.html")
        self.assertNotIn("if-modified-since", self.origin.last().lower())
        second = self.get("/simple.html")
        self.assertIn(f"If-Modified-Since: {LAST_MODIFIED}", self.origin.last())
        self.assertStatus(second, 200)
        self.assertEqual(self.response_id(first), self.response_id(second))

    def test_conditional_get_without_last_modified(self):
        self.control("/proxy/cache/enable")
        first = self.get("/nolm")
        second = self.get("/nolm")
        self.assertIn("if-modified-since:", self.origin.last().lower())
        self.assertEqual(self.response_id(first), self.response_id(second))

    def test_disable_then_reenable_keeps_cached_objects(self):
        self.control("/proxy/cache/enable")
        cached = self.get("/simple.html")
        self.control("/proxy/cache/disable")
        fresh = self.get("/simple.html")
        self.assertNotEqual(self.response_id(cached), self.response_id(fresh))
        self.control("/proxy/cache/enable")
        again = self.get("/simple.html")
        self.assertEqual(self.response_id(cached), self.response_id(again))

    def test_flush_empties_the_cache(self):
        self.control("/proxy/cache/enable")
        self.get("/simple.html")
        self.control("/proxy/cache/flush")
        self.get("/simple.html")
        self.assertNotIn("if-modified-since", self.origin.last().lower())

    def test_errors_are_not_cached(self):
        self.control("/proxy/cache/enable")
        self.get("/missing")
        self.get("/missing")
        self.assertNotIn("if-modified-since", self.origin.last().lower())


class BlocklistTests(ProxyTestCase):
    def test_control_urls_return_200(self):
        for path in ("/proxy/blocklist/enable", "/proxy/blocklist/add/example",
                     "/proxy/blocklist/remove/example", "/proxy/blocklist/disable",
                     "/proxy/blocklist/flush"):
            self.assertStatus(self.control(path), 200)

    def test_blocked_host_gets_403_and_is_not_contacted(self):
        self.control("/proxy/blocklist/enable")
        self.control("/proxy/blocklist/add/localhost")
        before = self.origin.count()
        self.assertStatus(self.get("/simple.html"), 403)
        self.assertEqual(self.origin.count(), before)

    def test_host_and_port_entry(self):
        self.control("/proxy/blocklist/enable")
        self.control(f"/proxy/blocklist/add/local:{self.origin.port}")
        self.assertStatus(self.get("/simple.html"), 403)

    def test_removed_entry_is_allowed(self):
        self.control("/proxy/blocklist/enable")
        self.control("/proxy/blocklist/add/localhost")
        self.control("/proxy/blocklist/remove/localhost")
        self.assertStatus(self.get("/simple.html"), 200)

    def test_disabled_blocklist_allows_everything(self):
        self.control("/proxy/blocklist/add/localhost")
        self.assertStatus(self.get("/simple.html"), 200)
        self.control("/proxy/blocklist/enable")
        self.assertStatus(self.get("/simple.html"), 403)
        self.control("/proxy/blocklist/disable")
        self.assertStatus(self.get("/simple.html"), 200)

    def test_flush_empties_the_blocklist(self):
        self.control("/proxy/blocklist/enable")
        self.control("/proxy/blocklist/add/localhost")
        self.control("/proxy/blocklist/flush")
        self.assertStatus(self.get("/simple.html"), 200)


if __name__ == "__main__":
    unittest.main()
