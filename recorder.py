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
        self.connected_name = None
        self.connected_address = None

    async def scan_devices(self):
        """Return list of devices with name and address."""
        devices = await BleakScanner.discover()
        results = []
        for d in devices:
            name = d.name or "Unknown"
            addr = d.address
            if addr:
                results.append({"name": name, "address": addr, "device": d})
        return results

    async def connect_to_address(self, address):
        """Find and connect to a device by exact address."""
        if not address:
            raise Exception("No device address provided")

        print(f"Connecting to address {address}...")
        max_retries = 3
        target_device = None

        # Try find by address quickly
        target_device = await BleakScanner.find_device_by_address(address, timeout=8.0)
        if not target_device:
            # Fallback to full scan
            devices = await BleakScanner.discover()
            for d in devices:
                if d.address == address:
                    target_device = d
                    break

        if not target_device:
            raise Exception(f"Device with address {address} not found.")

        for attempt in range(max_retries):
            try:
                self.device_client = PolarDevice(target_device)
                await self.device_client.connect()
                self.is_connected = True
                self.connected_name = target_device.name or "Unknown"
                self.connected_address = target_device.address
                print(f"Connected successfully to {self.connected_name} ({self.connected_address}).")
                break
            except Exception as e:
                print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    import traceback
                    traceback.print_exc()
                    raise e
                await asyncio.sleep(2.0)

        return self.connected_name

    async def disconnect(self):
        if self.device_client and self.is_connected:
            await self.device_client.disconnect()
            self.is_connected = False
            self.connected_name = None
            self.connected_address = None
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
            try:
                await self.device_client.stop_heartrate_stream()
            except Exception as e:
                print(f"Warning: Failed to stop HR stream gracefully: {e}")

    async def get_battery_level(self):
        """Fetch battery level from the device using standard Battery Service (0x180F)."""
        if not self.is_connected or not self.device_client:
            return None
        
        try:
            # Battery Level Characteristic UUID: 2A19
            # The client property in PolarDevice is usually the BleakClient
            client = self.device_client.client
            if client and client.is_connected:
                battery_data = await client.read_gatt_char("00002a19-0000-1000-8000-00805f9b34fb")
                if battery_data:
                    return int(battery_data[0])
        except Exception as e:
            print(f"Error fetching battery level: {e}")
        return None
