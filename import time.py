import time
import re
import subprocess
from scapy.all import ARP, Ether, srp

def get_gateway():
    result = subprocess.run(["ip", "route"], capture_output=True, text=True)
    match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", result.stdout)
    return match.group(1) if match else None

def get_mac(ip):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    answered = srp(pkt, timeout=2, verbose=False)[0]
    for _, recv in answered:
        return recv.hwsrc.lower()
    return None

gateway = get_gateway()
if not gateway:
    print("Could not find default gateway.")
    raise SystemExit(1)

original_mac = get_mac(gateway)
if not original_mac:
    print("Could not resolve gateway MAC.")
    raise SystemExit(1)

print(f"Monitoring gateway {gateway} [{original_mac}]")

while True:
    current_mac = get_mac(gateway)
    if current_mac and current_mac != original_mac:
        print(f"[ALERT] Possible ARP spoofing! {gateway}: {original_mac} -> {current_mac}")
    time.sleep(5)