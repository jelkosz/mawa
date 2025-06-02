from cachetools import LRUCache
import hashlib

cache = LRUCache(maxsize=100)

def store_to_cache(key, value):
    cache[key_to_hash(key)] = value

def is_cached(key):
    return key_to_hash(key) in cache

def get_from_cache(key):
    return cache[key_to_hash(key)]

def clear_from_cache(key):
    if key in cache:
        del cache[key]

def key_to_hash(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()