import hashlib

def hash(text: str) -> str:
    h = hashlib.new("sha256")
    h.update(text.encode())
    return h.hexdigest()