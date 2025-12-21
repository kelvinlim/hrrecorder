import dearpygui.dearpygui as dpg
import threading
import time
import asyncio
import os
from data_manager import DataManager
from recorder import PolarRecorder
from version import __version__
import queue
import logging

# Configure logging to file
logging.basicConfig(
    filename='hrrecorder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HRRecorderApp:
    def __init__(self):
        self.data_manager = DataManager()
        self.recorder = PolarRecorder()
        
        self.is_recording = False
        self.subject_id = "test"
        self.sampling_interval = 10
        self.last_sample_time = 0
        self.selected_device_type = "Polar Sense"
        self.selected_device_name = None
        self.selected_device_address = None
        self.discovered_devices = []
        self.busy_devices = set()  # local soft-locks to avoid double pick in same app
        self.battery_level = None
        self.last_battery_check = 0
        self.last_data_time = 0
        self.is_reconnecting = False
        self.watchdog_interval = 20 # seconds to wait before assuming connection lost during recording
        


        
        # Asyncio Loop Thread - Removed for single thread approach
        # self.loop = asyncio.new_event_loop()
        # self.loop_thread = threading.Thread(target=self.start_loop, args=(self.loop,), daemon=True)
        # self.loop_thread.start()
        
        # Data Queue for UI
        self.data_queue = queue.Queue()
        self.plot_data_x = []
        self.plot_data_y = []
        self.start_time = None

        dpg.create_context()
        dpg.create_viewport(title='HR Recorder', width=800, height=750)
        
        with dpg.window(tag="Primary Window"):
            with dpg.group(horizontal=True):
                dpg.add_text("Polar Device Connection")
                dpg.add_spacer(width=200)
                dpg.add_text("Battery: --%", tag="battery_text", color=(0, 255, 0))
            
            dpg.add_input_text(label="Subject ID", default_value="test", callback=self.update_subject_id)

            
            dpg.add_combo(label="Device Type", items=["Polar Sense", "Polar H10"], 
                          default_value="Polar Sense", callback=self.update_device_type)
            
            dpg.add_button(label="Scan Devices", callback=self.scan_devices)
            dpg.add_listbox(items=[], label="Devices", tag="device_list", num_items=6, callback=self.select_device)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Connect", callback=self.connect_device, tag="connect_btn")
                dpg.add_button(label="Reconnect", callback=self.manual_reconnect, tag="reconnect_btn", show=False)
            dpg.add_text("Status: Disconnected", tag="status_text")
            dpg.add_text("Last Data: --:--:--", tag="last_data_text")
            dpg.add_text("Total Time: 00:00:00", tag="total_time_text")
            
            dpg.add_separator()
            
            dpg.add_input_int(label="Sampling (sec)", default_value=10, 
                              callback=self.update_sampling, tag="sampling_input", min_value=1)

            dpg.add_text("Heart Rate Monitor")
            with dpg.plot(label="Live Heart Rate", height=300, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="HR (bpm)", tag="y_axis")
                dpg.add_line_series([], [], label="HR", parent="y_axis", tag="hr_series")

            dpg.add_button(label="Start Recording", callback=self.toggle_recording, tag="record_btn", show=True)
            dpg.add_spacer(height=10)
            dpg.add_button(label="Exit", callback=self.exit_app)
            
            # Add bottom padding so version label stays visible
            dpg.add_spacer(height=40)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=-1)
                dpg.add_text(f"v{__version__}", color=(128, 128, 128))

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)

    # Removed start_loop thread method

    def update_subject_id(self, sender, app_data):
        self.subject_id = app_data

    def update_sampling(self, sender, app_data):
        self.sampling_interval = app_data

    def update_device_type(self, sender, app_data):
        self.selected_device_type = app_data
        print(f"Selected: {app_data}")

    def scan_devices(self):
        dpg.set_value("status_text", "Scanning for devices...")
        self.loop.create_task(self.async_scan_devices())

    async def async_scan_devices(self):
        try:
            devices = await self.recorder.scan_devices()
            # Filter devices by selected device type
            filtered_devices = []
            for d in devices:
                if self.selected_device_type and d['name']:
                    if self.selected_device_type.lower() in d['name'].lower():
                        filtered_devices.append(d)
                        
            self.discovered_devices = filtered_devices
            display_items = []
            for d in filtered_devices:
                label = f"{d['name']} ({d['address']})"
                if d['address'] in self.busy_devices:
                    label += " [busy]"
                display_items.append(label)
            dpg.configure_item("device_list", items=display_items)
            dpg.set_value("status_text", f"Found {len(filtered_devices)} devices matching '{self.selected_device_type}'")
        except Exception as e:
            dpg.set_value("status_text", f"Scan error: {e}")

    def select_device(self, sender, app_data):
        # app_data is the selected label
        if not self.discovered_devices:
            return
        label = app_data
        for d in self.discovered_devices:
            if d['address'] in label:
                self.selected_device_name = d['name']
                self.selected_device_address = d['address']
                break
        if self.selected_device_address:
            busy_flag = " (busy locally)" if self.selected_device_address in self.busy_devices else ""
            dpg.set_value("status_text", f"Selected {self.selected_device_name} ({self.selected_device_address}){busy_flag}")

    def connect_device(self):
        if not self.selected_device_address:
            dpg.set_value("status_text", "Select a device from the list first")
            return
        if self.selected_device_address in self.busy_devices:
            dpg.set_value("status_text", "Device already in use in this app (busy)")
            return
        dpg.set_value("status_text", f"Connecting to {self.selected_device_name} ({self.selected_device_address})...")
        self.loop.create_task(self.async_connect())

    async def async_connect(self):
        dpg.configure_item("connect_btn", enabled=False)
        try:
            device_name = await self.recorder.connect_to_address(self.selected_device_address)
            self.selected_device_name = device_name
            self.busy_devices.add(self.selected_device_address)
            dpg.set_value("status_text", f"Connected to: {device_name} ({self.selected_device_address})")
            dpg.hide_item("reconnect_btn")
            dpg.configure_item("connect_btn", enabled=False)
            logger.info(f"Connected to {device_name} ({self.selected_device_address})")
            
            if self.is_recording:
                dpg.set_value("status_text", "Reconnected! Resuming stream...")
                await self.recorder.start_hr_stream(self.handle_hr_data)
                self.last_data_time = time.time()
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            dpg.set_value("status_text", f"Error: {e}")
            dpg.configure_item("connect_btn", enabled=True)
            dpg.show_item("reconnect_btn")

    def manual_reconnect(self):
        if self.selected_device_address:
            logger.info("Manual reconnect requested")
            self.loop.create_task(self.async_connect())

    def check_watchdog(self):
        """Checks if data has stopped during recording and attempts recovery."""
        if self.is_recording and not self.is_reconnecting:
            current_time = time.time()
            if self.last_data_time > 0 and (current_time - self.last_data_time > self.watchdog_interval):
                self.is_reconnecting = True
                self.loop.create_task(self.async_check_watchdog())

    async def async_check_watchdog(self):
        current_gap = time.time() - self.last_data_time
        logger.warning(f"Watchdog trigger: No data for {current_gap:.1f}s")
        dpg.set_value("status_text", "Connection stalled. Reconnecting...")
        
        # Attempt to disconnect and reconnect
        try:
            await self.recorder.disconnect()
            await asyncio.sleep(1)
            await self.async_connect()
        except Exception as e:
            logger.error(f"Watchdog recovery failed: {e}")
        finally:
            self.is_reconnecting = False



    def toggle_recording(self):
        if not self.is_recording:
            # Start
            if not self.recorder.is_connected:
                dpg.set_value("status_text", "Error: Not connected to device.")
                return

            self.is_recording = True
            dpg.set_item_label("record_btn", "Stop Recording")
            
            dpg.configure_item("sampling_input", enabled=False)
            
            self.data_manager.set_metadata(
                self.subject_id,
                self.sampling_interval,
                device_name=self.selected_device_name,
                device_address=self.selected_device_address,
            )
            filename = self.data_manager.create_filename(self.subject_id)
            dpg.set_value("status_text", f"Recording to: {filename}")
            
            self.start_time = time.time()
            self.last_sample_time = time.time()
            self.last_save_time = time.time()
            self.last_data_time = time.time()
            self.plot_data_x = []
            self.plot_data_y = []
            self.data_manager.data_buffer = [] # Reset buffer
            logger.info(f"Started recording for subject {self.subject_id}")
            
            # Start Stream
            self.loop.create_task(
                self.recorder.start_hr_stream(self.handle_hr_data)
            )
        else:
            # Stop
            self.is_recording = False
            dpg.set_item_label("record_btn", "Start Recording")
            dpg.configure_item("sampling_input", enabled=True)
            dpg.set_value("status_text", "Recording Stopped. Saving...")
            logger.info("Stopped recording")
            
            self.loop.create_task(self.recorder.stop_hr_stream())
            
            self.data_manager.save_buffer()
            dpg.set_value("status_text", f"Saved: {self.data_manager.current_filename}")
            
            # Show reconnect if disconnected
            if not self.recorder.is_connected:
                dpg.show_item("reconnect_btn")
                dpg.configure_item("connect_btn", enabled=True)

    def handle_hr_data(self, timestamp, hr_val):
        self.data_queue.put((timestamp, hr_val))
        self.last_data_time = timestamp

    def update_plot(self):
        # Update last data text
        if self.last_data_time > 0:
            time_str = time.strftime('%H:%M:%S', time.localtime(self.last_data_time))
            dpg.set_value("last_data_text", f"Last Data: {time_str}")
            
        # Update total time
        if self.is_recording and self.start_time:
            total_seconds = int(time.time() - self.start_time)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            dpg.set_value("total_time_text", f"Total Time: {hours:02}:{minutes:02}:{seconds:02}")
        
        # Connection status button management (ensure consistency)
        if not self.recorder.is_connected and not self.is_reconnecting:
            if dpg.is_item_shown("reconnect_btn") is False:
                 dpg.show_item("reconnect_btn")
                 dpg.configure_item("connect_btn", enabled=True)
        elif self.recorder.is_connected:
            if dpg.is_item_shown("reconnect_btn") is True:
                 dpg.hide_item("reconnect_btn")
                 dpg.configure_item("connect_btn", enabled=False)

        # Process queue
        while not self.data_queue.empty():
            try:
                ts, hr = self.data_queue.get_nowait()
            except queue.Empty:
                break
            
            if self.is_recording:
                # Sampling logic: only save if enough time has passed
                if ts - self.last_sample_time >= self.sampling_interval:
                    self.data_manager.add_data_point(ts, hr)
                    self.last_sample_time = ts
                    # Periodic save every 30 seconds
                    if time.time() - self.last_save_time >= 30:
                        self.data_manager.save_buffer()
                        self.last_save_time = time.time()
                        filename = os.path.basename(self.data_manager.current_filename) if self.data_manager.current_filename else "unknown"
                        msg = f"Auto-saved to {filename} at {time.strftime('%H:%M:%S')}"
                        dpg.set_value("status_text", msg)
                        logger.info(msg)
                
                if self.start_time:
                    rel_time = ts - self.start_time
                    self.plot_data_x.append(rel_time)
                    self.plot_data_y.append(hr)
                    
                    if len(self.plot_data_x) > 300:
                        dpg.set_value("hr_series", [self.plot_data_x[-300:], self.plot_data_y[-300:]])
                    else:
                        dpg.set_value("hr_series", [self.plot_data_x, self.plot_data_y])
                        
                    dpg.fit_axis_data("x_axis")
                    dpg.fit_axis_data("y_axis")

    async def main_loop(self):
        while dpg.is_dearpygui_running():
            self.update_plot()
            self.check_battery() 
            self.check_watchdog() # Non-blocking now
            dpg.render_dearpygui_frame()
            await asyncio.sleep(0.01) # Yield to allow BLE events to process, ~100 FPS

    def check_battery(self):
        if self.recorder.is_connected:
            current_time = time.time()
            # Check battery every 60 seconds
            if current_time - self.last_battery_check >= 60:
                self.last_battery_check = current_time # Update immediately to avoid multiple tasks
                self.loop.create_task(self.async_check_battery())
        else:
            if self.battery_level is not None:
                self.battery_level = None
                dpg.set_value("battery_text", "Battery: --%")

    async def async_check_battery(self):
        try:
            level = await self.recorder.get_battery_level()
            if level is not None:
                self.battery_level = level
                dpg.set_value("battery_text", f"Battery: {self.battery_level}%")
        except Exception as e:
            print(f"Background battery check failed: {e}")

    def exit_app(self, sender=None, app_data=None):
        dpg.stop_dearpygui()

    def run(self):
        # Setup AsyncIO Loop (Main Thread)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.main_loop())
        except KeyboardInterrupt:
            pass
        finally:
            # Cleanup
            if self.recorder.is_connected:
                 self.loop.run_until_complete(self.recorder.disconnect())
            dpg.destroy_context()
            self.loop.close()

if __name__ == "__main__":
    app = HRRecorderApp()
    app.run()
