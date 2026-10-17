# HTTP Proxy

A caching, filtering HTTP/1.0 proxy server written in Python using only the `socket` and `threading` modules. No HTTP libraries: parsing requests, building requests to the origin server, caching, and filtering are all done by hand.

Built for CS 4480 Computer Networks at the University of Utah.

## What it does

- **Forwards requests.** A browser or tool sends the proxy a full URL (`GET http://example.com/page HTTP/1.0`). The proxy connects to that server, sends the request in the form servers expect (`GET /page` plus a `Host` header, always with `Connection: close`), and relays the response back byte for byte, including large binary files.
- **Validates input.** Malformed request lines, headers, URLs, or HTTP versions get `400 Bad Request`. Real HTTP methods other than GET get `501 Not Implemented`. Rejected requests never reach the origin server.
- **Handles many clients at once.** Each connection gets its own thread, so a slow or idle client never blocks anyone else.
- **Caches responses.** When caching is on, the proxy keeps successful responses in memory. Before reusing one, it asks the server whether the object changed (a conditional GET with `If-Modified-Since`). If the server answers `304 Not Modified`, the proxy serves its cached copy.
- **Blocks sites.** When the blocklist is on, any request whose host contains a blocked string gets `403 Forbidden`. Entries like `example:8080` block a host on a specific port.
- **Can be controlled while running** through special URLs:

| URL path | Effect |
| --- | --- |
| `/proxy/cache/enable`, `/proxy/cache/disable` | Turn caching on or off (the cache is kept) |
| `/proxy/cache/flush` | Empty the cache |
| `/proxy/blocklist/enable`, `/proxy/blocklist/disable` | Turn blocking on or off |
| `/proxy/blocklist/add/<string>`, `/proxy/blocklist/remove/<string>` | Change the blocklist |
| `/proxy/blocklist/flush` | Empty the blocklist |

## Run it

```bash
python3 HTTPproxy.py -a localhost -p 2100
```

Then, in another terminal:

```bash
curl --proxy1.0 localhost:2100 http://example.com/
curl --proxy1.0 localhost:2100 http://localhost/proxy/cache/enable
```

## Tests

```bash
python3 -m unittest test_proxy.py
```

31 tests start the real proxy and talk to it over sockets, with a small fake origin server in the background so the tests can check exactly what the proxy forwards and control what comes back. They cover request validation, the forwarded request format, large and error responses, concurrent clients, conditional GET caching, and the blocklist.

## Changes since the course

The first commit is the version I submitted. Writing the tests turned up 9 failures, which I fixed:

- After sending an error, the proxy kept going and forwarded the bad request anyway.
- The forwarded request joined the `Host` header to the next header on one line, and a stray blank line pushed `Connection: close` out of the headers.
- Control URLs answered `400 Bad Request` instead of `200 OK`.
- Error responses were missing the blank line that tells the client the response is complete.
- The cache could hit an undefined variable when a response had no `Last-Modified` header, query strings were dropped, and the server could loop forever if a client disconnected early.
