import dearpygui.dearpygui as dpg
import threading
import time
import asyncio
from data_manager import DataManager
from recorder import PolarRecorder
from version import __version__
import queue

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
            dpg.add_text("Polar Device Connection")
            
            dpg.add_input_text(label="Subject ID", default_value="test", callback=self.update_subject_id)
            
            dpg.add_combo(label="Device Type", items=["Polar Sense", "Polar H10"], 
                          default_value="Polar Sense", callback=self.update_device_type)
            
            dpg.add_button(label="Scan Devices", callback=self.scan_devices)
            dpg.add_listbox(items=[], label="Devices", tag="device_list", num_items=6, callback=self.select_device)
            dpg.add_button(label="Connect", callback=self.connect_device)
            dpg.add_text("Status: Disconnected", tag="status_text")
            
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
        try:
            device_name = await self.recorder.connect_to_address(self.selected_device_address)
            self.selected_device_name = device_name
            self.busy_devices.add(self.selected_device_address)
            dpg.set_value("status_text", f"Connected to: {device_name} ({self.selected_device_address})")
        except Exception as e:
            dpg.set_value("status_text", f"Error: {e}")

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
            self.plot_data_x = []
            self.plot_data_y = []
            self.data_manager.data_buffer = [] # Reset buffer
            
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
            
            self.loop.create_task(self.recorder.stop_hr_stream())
            
            self.data_manager.save_buffer()
            dpg.set_value("status_text", f"Saved: {self.data_manager.current_filename}")

    def handle_hr_data(self, timestamp, hr_val):
        # We can now write directly or still use queue if we want to be safe, 
        # but since we are single threaded, we can just push to a list or queue.
        # Queue is still fine to decouple data reception from plot update timing.
        self.data_queue.put((timestamp, hr_val))

    def update_plot(self):
        # Process queue
        while not self.data_queue.empty():
            ts, hr = self.data_queue.get()
            
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
                        dpg.set_value("status_text", f"Auto-saved to {filename} at {time.strftime('%H:%M:%S')}")
                
                if self.start_time:
                    rel_time = ts - self.start_time
                    self.plot_data_x.append(rel_time)
                    self.plot_data_y.append(hr)
                    
                    if len(self.plot_data_x) > 300:
                        dpg.set_value("hr_series", [self.plot_data_x[-300:], self.plot_data_y[-300:]])
                    else:
                        dpg.set_value("hr_series", [self.plot_data_x, self.plot_data_y])
                        
                    # Auto-fit occasionally or always? Always is fine for small N
                    dpg.fit_axis_data("x_axis")
                    dpg.fit_axis_data("y_axis")

    async def main_loop(self):
        while dpg.is_dearpygui_running():
            self.update_plot()
            dpg.render_dearpygui_frame()
            await asyncio.sleep(0.001) # Yield to allow BLE events to process

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
