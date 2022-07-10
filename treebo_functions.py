import base64
import os

from Crypto.Cipher import ChaCha20


async def before_media_send(ctx, _, filename):
    try:
        observation_id = filename.split("/")[-1].split(".")[0].split("_")[1]
    except:
        observation_id = None
    if observation_id:
        encrypted = encrypt_chacha(
            int(observation_id).to_bytes(8, "big").strip(b"\x00")
        )
        await ctx.send("**Observation Code**: `" + encrypted + "`")


def encrypt_chacha(plaintext: bytes) -> str:
    """Encrypts a string using ChaCha20."""
    hex_key = os.getenv("SOURCE_ENCRYPTION_KEY")
    if not hex_key:
        raise ValueError("No encryption key set")
    key = int(hex_key, 16).to_bytes(32, "big")
    cipher = ChaCha20.new(key=key)
    ciphertext = (
        base64.b64encode(cipher.encrypt(plaintext), altchars=b"-_").decode().strip("=")
    )
    nonce = base64.b64encode(cipher.nonce, altchars=b"-_").decode().strip("=")
    return f"{ciphertext}.{nonce}"


def decrypt_chacha(encrypted: str) -> bytes:
    """Decrypts a string using ChaCha20."""
    hex_key = os.getenv("SOURCE_ENCRYPTION_KEY")
    if not hex_key:
        raise ValueError("No encryption key set")
    key = int(hex_key, 16).to_bytes(32, "big")

    parsed = encrypted.split(".")
    if len(parsed) != 2:
        raise ValueError("Invalid ciphertext")

    # apparently it's ok if you have extra padding
    ciphertext = base64.b64decode(parsed[0] + "==", altchars=b"-_")
    nonce = base64.b64decode(parsed[1] + "==", altchars=b"-_")

    cipher = ChaCha20.new(key=key, nonce=nonce)
    return cipher.decrypt(ciphertext)
