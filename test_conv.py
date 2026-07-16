import requests
import time

url = "http://127.0.0.1:8000"

print("Logging in...")
try:
    # We don't know the exact username/pass, let's just test by bypassing or checking auth
    pass
except Exception as e:
    print(e)
