import dearpygui.dearpygui as dpg
import threading
import time
import asyncio
from data_manager import DataManager
from recorder import PolarRecorder
import queue

class HRRecorderApp:
    def __init__(self):
        self.data_manager = DataManager()
        self.recorder = PolarRecorder()
        
        self.is_recording = False
        self.subject_id = "test"
        self.sampling_interval = 10
        self.last_sample_time = 0
        self.selected_device_type = "Polar Verity Sense"
        
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
        dpg.create_viewport(title='HR Recorder', width=800, height=600)
        
        with dpg.window(tag="Primary Window"):
            dpg.add_text("Polar Device Connection")
            
            dpg.add_input_text(label="Subject ID", default_value="test", callback=self.update_subject_id)
            
            dpg.add_combo(label="Device Type", items=["Polar Verity Sense", "Polar H10"], 
                          default_value="Polar Verity Sense", callback=self.update_device_type)
            
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

    def connect_device(self):
        dpg.set_value("status_text", f"Scanning for {self.selected_device_type}...")
        # Schedule the coroutine on the existing loop
        self.loop.create_task(self.async_connect())

    async def async_connect(self):
        try:
            device_name = await self.recorder.scan_and_connect(self.selected_device_type)
            dpg.set_value("status_text", f"Connected to: {device_name}")
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
            
            self.data_manager.set_metadata(self.subject_id, self.sampling_interval)
            filename = self.data_manager.create_filename(self.subject_id)
            dpg.set_value("status_text", f"Recording to: {filename}")
            
            self.start_time = time.time()
            self.last_sample_time = 0
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
                    if len(self.data_manager.data_buffer) >= 60:
                        self.data_manager.save_buffer() 
                
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
