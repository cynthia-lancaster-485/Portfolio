# Networking Projects

Three projects from CS 4480 Computer Networks at the University of Utah, all written in Python with no networking libraries beyond raw sockets.

| Project | What it is |
| --- | --- |
| [HTTP Proxy](HTTP%20Proxy/) | A multithreaded HTTP/1.0 proxy with request validation, a cache that revalidates with conditional GET, and a domain blocklist, all controllable at runtime |
| [Reliable Transport](Reliable%20Transport/) | Two reliable data transfer protocols, Alternating Bit (stop and wait) and Go-Back-N (sliding window), running over a simulated network that loses and corrupts packets |

The first commit in this folder is the code exactly as I submitted it for the class. When I revisited it later, I wrote automated tests, found real bugs (the proxy forwarded requests it had already rejected, and Go-Back-N could crash or stall under packet loss), and fixed each one in its own commit. You can see the before and after in the commit history.

Run all the tests with:

```bash
cd "HTTP Proxy" && python3 -m unittest test_proxy.py
cd "../Reliable Transport" && python3 -m unittest test_protocols.py
```

Both need only Python 3.10 or newer.
