import struct
import zlib


def _png_bytes():

    def _chunk(ctype, data):
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw = b""
    for y in range(1):
        raw = b"\x00" + b"\xff\xff\xff"
    idat = zlib.compress(raw)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", idat)
        + _chunk(b"IEND", b"")
    )


async def test_screen_no_file(client):
    resp = await client.post("/screen")
    assert resp.status_code == 400
    assert resp.json() == {"error": "No file provided"}


async def test_screen_wrong_type(client):
    resp = await client.post(
        "/screen",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json() == {"error": "File must be JPEG or PNG"}


async def test_screen_oversized(client):
    huge = b"x" * (11 * 1024 * 1024)
    resp = await client.post(
        "/screen",
        files={"file": ("big.png", huge, "image/png")},
    )
    assert resp.status_code == 413
    assert resp.json() == {"error": "File exceeds 10 MB limit"}


async def test_screen_model_server_unreachable(client):
    resp = await client.post(
        "/screen",
        files={"file": ("test.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 502
    assert resp.json() == {"error": "Model server unavailable"}
