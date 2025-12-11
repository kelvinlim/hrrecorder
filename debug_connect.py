import asyncio
from bleak import BleakScanner
from polar_python import PolarDevice

async def debug_main():
    print("Starting Scan...")
    devices = await BleakScanner.discover()
    target_device = None
    
    for d in devices:
        if d.name and "Polar" in d.name:
            print(f"Found: {d.name} - {d.address}")
            target_device = d
            # Break on first match for testing
            break
            
    if not target_device:
        print("No Polar device found.")
        return

    print(f"Attempting to connect to {target_device.name}...")
    
    client = PolarDevice(target_device)
    try:
        await client.connect()
        print("SUCCESS: Connected!")
        print("Waiting 5 seconds...")
        await asyncio.sleep(5)
        print("Disconnecting...")
        await client.disconnect()
        print("Disconnected.")
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_main())
