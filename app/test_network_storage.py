# test_network.py
import os

network_path = r"\\server\share\documente"  # UNC path direct
print(f"Testing access to: {network_path}")

try:
    files = os.listdir(network_path)
    print(f"Success! Found {len(files)} items")
    print(files[:5])  # primele 5
except Exception as e:
    print(f"Error: {e}")