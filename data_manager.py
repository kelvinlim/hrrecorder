import json
import os
from datetime import datetime

class DataManager:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.current_filename = None
        self.data_buffer = []

        # Metadata fields
        self.subject_id = "unknown"
        self.sampling_interval = 10
        self.start_datetime = datetime.now()

    def set_metadata(self, subject_id, sampling_interval, device_name=None, device_address=None):
        self.subject_id = subject_id
        self.sampling_interval = sampling_interval
        self.start_datetime = datetime.now()
        self.device_name = device_name
        self.device_address = device_address

    def create_filename(self, subject_id):
        # We use the time from set_metadata if available, or now
        now = self.start_datetime
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")
        
        # Sanitize subject_id
        safe_subject_id = "".join([c for c in subject_id if c.isalnum() or c in ('-', '_')])
        if not safe_subject_id:
            safe_subject_id = "unknown"
            
        filename = f"sub-{safe_subject_id}_date-{date_str}_time-{time_str}.json"
        self.current_filename = os.path.join(self.output_dir, filename)
        return self.current_filename

    def add_data_point(self, timestamp, hr):
        """Adds a data point to the buffer."""
        iso_time = datetime.fromtimestamp(timestamp).isoformat()
        self.data_buffer.append({
            "timestamp": timestamp,
            "datetime": iso_time,
            "hr": hr
        })

    def save_buffer(self):
        if not self.current_filename:
            return

        date_str = self.start_datetime.strftime("%Y-%m-%d")
        time_str = self.start_datetime.strftime("%H:%M:%S")

        data_structure = {
            "subject": self.subject_id,
            "date": date_str,
            "time": time_str,
            "sampling_interval_sec": self.sampling_interval,
            "device_name": getattr(self, "device_name", None),
            "device_address": getattr(self, "device_address", None),
            "data": []
        }

        if os.path.exists(self.current_filename):
            try:
                with open(self.current_filename, 'r') as f:
                    if os.path.getsize(self.current_filename) > 0:
                        data_structure = json.load(f)
            except json.JSONDecodeError:
                pass 
        
        data_structure["data"].extend(self.data_buffer)
        
        with open(self.current_filename, 'w') as f:
            json.dump(data_structure, f, indent=2)
            
        self.data_buffer = [] # Clear buffer after save
