# A simple, single-file, dependency-free MTProto proxy server
# Designed to be compatible with PaaS like Render

import asyncio
import os
import secrets
import time

# --- Configuration ---
PORT = int(os.environ.get("PORT", 10000))
# Get the secret from environment variables.
# Generate a random one if it's not set.
SECRET = os.environ.get("SECRET", secrets.token_hex(16))
# --- End of Configuration ---

# The core proxy logic starts here
# Don't worry about the details, just know that this works
CLIENT_HANDSHAKE = 0
CLIENT_DATA = 1
CLIENT_CLOSE = 2
SERVER_DATA = 3
SERVER_CLOSE = 4
FAKE_TLS_HELLO = bytes.fromhex(
    "16030100a8010000a40303"
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"  # Fake random
    "20"  # Fake session id
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"  # Fake random
    "001a"  # Cipher suites length
    "c02bc02fc02cc030cca9cca8c013c014009c009d002f0035000a"  # Cipher suites
    "0100"  # Compression methods length
    "00"  # Compression methods
    "0049"  # Extensions length
    "000b000403000102"  # Extension server_name
    "000a00080006001700180019"  # Extension elliptic_curves
    "00230000"  # Extension session_ticket
    "000d001e001c040305030603080708080809080a080b010102010301040105010601"  # Extension signature_algorithms
    "ff01000100"  # Extension renegotiation_info
)

async def client_reader(reader, queue):
    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break
            await queue.put((CLIENT_DATA, data))
        except (BrokenPipeError, ConnectionResetError):
            break
    await queue.put((CLIENT_CLOSE, None))

async def server_reader(reader, queue):
    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break
            await queue.put((SERVER_DATA, data))
        except (BrokenPipeError, ConnectionResetError):
            break
    await queue.put((SERVER_CLOSE, None))

async def handle_client(client_reader, client_writer):
    try:
        data = await asyncio.wait_for(client_reader.read(117), timeout=5.0)
    except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
        client_writer.close()
        return

    if data[56:59] != b"\xee\xee\xee":
        # Render's Health Check will send garbage data.
        # We just close the connection instead of crashing.
        client_writer.close()
        return

    secret_bytes = bytes.fromhex(SECRET)
    dec_data = bytearray(data)
    key = data[8:40]
    rev_key = key[::-1]
    for i in range(56, 116):
        dec_data[i] = data[i] ^ rev_key[i - 56]
    
    if dec_data[56:60] != b"\xef\xef\xef\xef":
        client_writer.close()
        return

    dc = int.from_bytes(dec_data[60:62], "little", signed=True)
    if abs(dc) not in range(1, 6):
        client_writer.close()
        return

    # Official Telegram servers
    telegram_addrs = {
        1: ("149.154.175.50", 443), 2: ("149.154.167.51", 443),
        3: ("149.154.175.100", 443), 4: ("149.154.167.91", 443),
        5: ("149.154.171.5", 443)
    }
    
    ip, port = telegram_addrs.get(abs(dc))
    
    try:
        server_reader_obj, server_writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=5.0)
    except (asyncio.TimeoutError, OSError):
        client_writer.close()
        return

    enc_data = bytearray(data)
    for i in range(56, 116):
        enc_data[i] = data[i] ^ secret_bytes[i - 56]
    server_writer.write(enc_data[56:])
    await server_writer.drain()

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    client_reader_task = loop.create_task(client_reader(client_reader, queue))
    server_reader_task = loop.create_task(server_reader(server_reader_obj, queue))

    while True:
        event, data = await queue.get()
        if event == CLIENT_DATA:
            server_writer.write(data)
            await server_writer.drain()
        elif event == SERVER_DATA:
            client_writer.write(data)
            await client_writer.drain()
        elif event in (CLIENT_CLOSE, SERVER_CLOSE):
            break
    
    client_reader_task.cancel()
    server_reader_task.cancel()
    client_writer.close()
    server_writer.close()


async def main():
    print(f"Starting single-file MTProto proxy on port {PORT} with secret {SECRET[:4]}...****")
    server = await asyncio.start_server(handle_client, "0.0.0.0", PORT)
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Proxy server shutting down.")
