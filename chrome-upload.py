import subprocess
import time
from collections import deque

WINDOW = 20   # seconds

def get_bytes_out():
    # Only sum obytes for the main network interface (e.g., en0)
    interface = "en0"  # Change this to your active interface if needed
    output = subprocess.check_output(["netstat", "-ib"], text=True)

    total = 0
    seen = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 10:
            continue
        if parts[0] != interface:
            continue
        # Only count the first occurrence per interface/address
        key = (parts[0], parts[1])
        if key in seen:
            continue
        seen.add(key)
        try:
            total += int(parts[9])  # obytes column
        except ValueError:
            pass
    return total


def human(bps):
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    i = 0

    while bps >= 1024 and i < 3:
        bps /= 1024
        i += 1

    return f"{bps:.2f} {units[i]}"


samples = deque(maxlen=WINDOW)

prev = get_bytes_out()

while True:

    time.sleep(1)
    now = get_bytes_out()
    delta = now - prev
    samples.append(delta)
    avg = sum(samples) / len(samples)
    rate = avg  # because each delta is 1 second
    print(f"\rUpload ({len(samples)}s avg): {human(rate)}", end="", flush=True)

    prev = now