import os

from diskcache import Cache
import hashlib

cache_dir = os.getenv("CACHE_DIR")

cache = None
if cache_dir:
    cache = Cache(cache_dir)

def store_to_cache(key, value):
    """
    Stores a value in the file-based cache.
    """
    if cache:
        cache.set(key_to_hash(key), value)

def is_cached(key):
    """
    Checks if a key is present in the file-based cache.
    """
    if cache:
        return key_to_hash(key) in cache
    else:
        return False

def get_from_cache(key):
    """
    Retrieves a value from the file-based cache.
    """
    if cache:
        return cache.get(key_to_hash(key))
    else:
        return ""

def clear_from_cache(key):
    """
    Removes a key-value pair from the file-based cache.
    """
    if cache:
        cache.delete(key_to_hash(key))

def key_to_hash(key):
    """
    Hashes the key to create a unique filename.
    """
    return hashlib.sha256(key.encode('utf-8')).hexdigest()
