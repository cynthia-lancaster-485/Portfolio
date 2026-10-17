# Reliable Transport Protocols

Two protocols that deliver data reliably and in order over a network that loses and corrupts packets: **Alternating Bit** (stop and wait, also called rdt3.0) and **Go-Back-N** (a sliding window). These are the same ideas TCP is built on.

Built for CS 4480 Computer Networks at the University of Utah. I wrote the sender (`EntityA`) and receiver (`EntityB`) classes in each file. The network simulator around them was provided by the course (originally by J.F. Kurose, Python version by Eric Eide).

## How they work

Both protocols share the same building blocks:

- **Checksums.** Each packet carries the sum of its sequence number, ACK number, and payload bytes. A packet whose checksum doesn't match was corrupted in transit and is ignored.
- **Sequence numbers and ACKs.** The receiver only accepts the packet it expects next and ACKs it. Anything corrupted or out of order gets the last good ACK again.
- **A retransmission timer.** If the sender doesn't hear back in time, it assumes something was lost and resends.
- **A send buffer.** Messages from the application wait their turn instead of being dropped.

**Alternating Bit** (`abp_rdtsim.py`) keeps one packet in flight at a time, numbered 0 or 1.

**Go-Back-N** (`gbn_rdtsim.py`) keeps up to half the sequence number space in flight at once. ACKs are cumulative, so one ACK confirms a packet and everything before it. A single timer covers the oldest unACKed packet, and on a timeout the sender resends everything still in flight.

## Run it

```bash
python3 gbn_rdtsim.py -n 50 -z 16 -l 0.05 -c 0.05 -v 1
```

`-n` is the number of messages, `-z` the sequence number limit, `-l` and `-c` the loss and corruption probabilities, and `-v` the trace level. For Alternating Bit, run `abp_rdtsim.py` with `-z 2`.

## Tests

```bash
python3 -m unittest test_protocols.py
```

The tests run each protocol across 30 random seeds at 0%, 5%, and 10% loss and corruption (and window sizes 2, 4, and 8 for Go-Back-N). Every run must deliver messages in exactly the order they were sent, without crashing or making invalid calls to the simulator, and deliver nearly every message.

## Changes since the course

The first commit is the version I submitted. Alternating Bit passed every test unchanged. Go-Back-N worked without packet loss but had real bugs once packets were lost:

- The receiver crashed if the very first packet arrived corrupted, because it tried to resend an ACK it hadn't created yet.
- After an ACK, the sender stopped its timer even while other packets were still in flight, so a lost packet could stall the connection.
- The retransmission timeout was too short for a full window in this simulator, so the sender kept resending its whole window and flooded the network. I tested several values and scaled the timeout with the window size.
