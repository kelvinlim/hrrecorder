import asyncio
from bleak import BleakScanner
from polar_python import PolarDevice, HRData
import logging

class PolarRecorder:
    def __init__(self):
        self.device = None
        self.device_client: PolarDevice = None
        self.is_connected = False
        self.hr_callback = None

    async def scan_and_connect(self, target_name_partial):
        """Scans for a device containing target_name_partial and connects to the first one found."""
        print(f"Scanning for devices containing '{target_name_partial}'...")
        devices = await BleakScanner.discover()
        target_device = None
        
        for d in devices:
            # print(f"Found: {d.name} ({d.address})")
            if d.name and target_name_partial.lower() in d.name.lower():
                target_device = d
                break
        
        if not target_device:
            raise Exception(f"Device containing '{target_name_partial}' not found.")
            
        print(f"Connecting to {target_device.name} ({target_device.address})...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.device_client = PolarDevice(target_device)
                await self.device_client.connect()
                self.is_connected = True
                print("Connected successfully.")
                break
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    import traceback
                    traceback.print_exc()
                    raise e
                await asyncio.sleep(2.0)
        
        return target_device.name

    async def disconnect(self):
        if self.device_client and self.is_connected:
            await self.device_client.disconnect()
            self.is_connected = False
            print("Disconnected.")

    async def start_hr_stream(self, callback):
        """
        Starts HR streaming.
        callback(hr_value: int, timestamp: float)
        """
        self.hr_callback = callback
        
        def internal_callback(data: HRData):
            # HRData has 'heartrate' and 'rr_intervals'
            
            hr_val = 0
            if hasattr(data, 'heartrate'):
                hr_val = data.heartrate
            elif isinstance(data, dict) and 'heartrate' in data:
                hr_val = data['heartrate']
            
            # Timestamp: We generate it here or use arrival time?
            # Arrival time is easiest for now.
            import time
            if self.hr_callback:
                self.hr_callback(time.time(), hr_val)

        self.device_client.set_callback(heartrate_callback=internal_callback)
        await self.device_client.start_heartrate_stream()

    async def stop_hr_stream(self):
        if self.device_client and self.is_connected:
            await self.device_client.stop_heartrate_stream()
