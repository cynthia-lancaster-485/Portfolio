#!/usr/bin/env python3
import socket
import sys
import signal
import threading
import urllib.parse
from datetime import datetime, timezone
from email.utils import format_datetime
from optparse import OptionParser

# Methods defined by HTTP that this proxy recognizes but does not implement (501).
# Anything else is not a valid method at all (400).
KNOWN_METHODS = {"HEAD", "POST", "PUT", "DELETE", "LINK", "UNLINK", "OPTIONS", "PATCH", "TRACE", "CONNECT"}

# URL -> (full response bytes, value to send back in If-Modified-Since)
cache = {}
blockList = []
cacheEnabled = False
blockingEnabled = False
state_lock = threading.Lock()


def ctrl_c_pressed(signal, frame):
    sys.exit(0)


def send_response(client_socket, status):
    client_socket.sendall(f"HTTP/1.0 {status}\r\n\r\n".encode())


def headerErrorCheck(headerData, client_socket):
    """Returns True (after sending the error) if the request line is invalid."""
    if len(headerData) != 3:
        send_response(client_socket, "400 Bad Request")
        return True
    method, _, version = headerData
    if method in KNOWN_METHODS:
        send_response(client_socket, "501 Not Implemented")
        return True
    if method != "GET" or version != "HTTP/1.0":
        send_response(client_socket, "400 Bad Request")
        return True
    return False


def parse_headers(lines, client_socket):
    """Returns the client's headers as a list of lines, or None (after sending
    a 400) if any header is not in "Name: value" form."""
    headers = []
    for line in lines:
        if line == "":
            continue
        name, sep, value = line.partition(": ")
        if not sep or not name or " " in name or ":" in name:
            send_response(client_socket, "400 Bad Request")
            return None
        headers.append(line)
    return headers


def handle_proxy_req(client_socket, urlData):
    """Handles the /proxy/... control URLs. Returns True if this was one."""
    global cacheEnabled, blockingEnabled
    path = urlData.path
    if not path.startswith("/proxy/"):
        return False

    with state_lock:
        if path == "/proxy/cache/enable":
            cacheEnabled = True
        elif path == "/proxy/cache/disable":
            cacheEnabled = False
        elif path == "/proxy/cache/flush":
            cache.clear()
        elif path == "/proxy/blocklist/enable":
            blockingEnabled = True
        elif path == "/proxy/blocklist/disable":
            blockingEnabled = False
        elif path == "/proxy/blocklist/flush":
            blockList.clear()
        elif path.startswith("/proxy/blocklist/add/"):
            entry = path[len("/proxy/blocklist/add/"):]
            if entry and entry not in blockList:
                blockList.append(entry)
        elif path.startswith("/proxy/blocklist/remove/"):
            entry = path[len("/proxy/blocklist/remove/"):]
            if entry in blockList:
                blockList.remove(entry)
        else:
            return False

    send_response(client_socket, "200 OK")
    return True


def handle_blocking_req(urlData, client_socket, port):
    """Sends 403 Forbidden and returns True if the host is on the blocklist."""
    with state_lock:
        if not blockingEnabled:
            return False
        entries = list(blockList)

    host_and_port = f"{urlData.hostname}:{port}"
    for block in entries:
        # An entry like "example:80" blocks hosts containing "example" on port 80.
        if ":" in block:
            block_host, _, block_port = block.rpartition(":")
            blocked = block_host in urlData.hostname and block_port == str(port)
        else:
            blocked = block in host_and_port
        if blocked:
            send_response(client_socket, "403 Forbidden")
            return True
    return False


def read_until_closed(sock):
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            return data
        data += chunk


def fetch(host, port, request):
    with socket.create_connection((host, port)) as origin:
        origin.sendall(request.encode())
        return read_until_closed(origin)


def status_code(response):
    parts = response.split(b"\r\n", 1)[0].split(b" ")
    return parts[1].decode() if len(parts) > 1 else ""


def header_value(response, name):
    head = response.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    for line in head.split("\r\n")[1:]:
        key, _, value = line.partition(":")
        if key.strip().lower() == name.lower():
            return value.strip()
    return None


def handle_client(client_socket, client_addr):
    try:
        # Read until the blank line that ends the request headers.
        content = b""
        while b"\r\n\r\n" not in content:
            data = client_socket.recv(1024)
            if not data:
                return
            content += data
        lines = content.decode("latin-1").split("\r\n\r\n", 1)[0].split("\r\n")

        headerData = lines[0].split(" ")
        if headerErrorCheck(headerData, client_socket):
            return

        urlData = urllib.parse.urlparse(headerData[1])
        if urlData.scheme != "http" or not urlData.hostname or urlData.path == "":
            send_response(client_socket, "400 Bad Request")
            return

        clientHeaders = parse_headers(lines[1:], client_socket)
        if clientHeaders is None:
            return

        if handle_proxy_req(client_socket, urlData):
            return

        port = urlData.port or 80
        if handle_blocking_req(urlData, client_socket, port):
            return

        path = urlData.path + (f"?{urlData.query}" if urlData.query else "")
        # Host and Connection are always set by the proxy, so drop the client's copies.
        extraHeader = "".join(h + "\r\n" for h in clientHeaders
                              if h.split(":", 1)[0].lower() not in ("host", "connection"))
        dataR = f"GET {path} HTTP/1.0\r\nHost: {urlData.netloc}\r\n{extraHeader}Connection: close\r\n\r\n"

        url = urllib.parse.urlunparse(("http", urlData.netloc, urlData.path, "", urlData.query, ""))
        with state_lock:
            useCache = cacheEnabled
            cached = cache.get(url) if useCache else None

        servedFromCache = False
        if cached:
            cachedResponse, lastModified = cached
            conditional = dataR[:-2] + f"If-Modified-Since: {lastModified}\r\n\r\n"
            response = fetch(urlData.hostname, port, conditional)
            if status_code(response) == "304":
                response = cachedResponse
                servedFromCache = True
        else:
            response = fetch(urlData.hostname, port, dataR)

        if useCache and not servedFromCache and status_code(response) == "200":
            # Prefer the server's own Last-Modified; otherwise use the time we cached it.
            lastModified = (header_value(response, "Last-Modified")
                            or format_datetime(datetime.now(timezone.utc), usegmt=True))
            with state_lock:
                cache[url] = (response, lastModified)

        client_socket.sendall(response)
    except OSError:
        try:
            send_response(client_socket, "502 Bad Gateway")
        except OSError:
            pass
    finally:
        client_socket.close()


def main():
    parser = OptionParser()
    parser.add_option('-p', type='int', dest='serverPort', default=2100)
    parser.add_option('-a', type='string', dest='serverAddress', default='localhost')
    (options, args) = parser.parse_args()

    signal.signal(signal.SIGINT, ctrl_c_pressed)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        skt.bind((options.serverAddress, options.serverPort))
        skt.listen()
        print(f"Listening on {(options.serverAddress, options.serverPort)}")
        while True:
            clientSocket, addr = skt.accept()
            threading.Thread(target=handle_client, args=(clientSocket, addr), daemon=True).start()


if __name__ == "__main__":
    main()
