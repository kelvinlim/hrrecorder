import asyncio
from bleak import BleakScanner, BleakClient

async def debug_bleak():
    print("Scanning with BleakScanner...")
    devices = await BleakScanner.discover()
    target = None
    for d in devices:
        if "Polar" in (d.name or ""):
            print(f"Found: {d.name} ({d.address})")
            target = d
            break
            
    if not target:
        print("No Polar device found.")
        return

    print(f"Connecting to {target.name} with 30s timeout...")
    # Trying with a much longer timeout
    async with BleakClient(target, timeout=30.0) as client:
        print(f"Connected: {client.is_connected}")
        print("Reading Services...")
        for service in client.services:
            print(f"[Service] {service}")
            
        print("Disconnecting...")

if __name__ == "__main__":
    asyncio.run(debug_bleak())
