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

    def create_filename(self, subject_id):
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        # Sanitize subject_id to be safe for filenames
        safe_subject_id = "".join([c for c in subject_id if c.isalnum() or c in ('-', '_')])
        if not safe_subject_id:
            safe_subject_id = "unknown"
            
        filename = f"sub-{safe_subject_id}_date-{date_str}_time-{time_str}.json"
        self.current_filename = os.path.join(self.output_dir, filename)
        return self.current_filename

    def add_data_point(self, timestamp, hr):
        """Adds a data point to the buffer."""
        self.data_buffer.append({
            "timestamp": timestamp,
            "hr": hr
        })

    def save_buffer(self):
        """Saves current buffer to disk and clears it (or appends).
        For simplicity, we might read-modify-write or just append if we structured it correctly.
        Here we will write the whole list for now, or append to a list in a file.
        Efficient approach: Read existing, append, write back? Or just write chunk?
        Request asked for periodic save to prevent data loss.
        """
        if not self.current_filename:
            return

        # Simple approach: Load existing data if file exists, append, save.
        # Warning: This gets slow if data grows large.
        # Better approach for logging: Write per line or append to a JSON array structure carefully.
        # Given the requirements, we'll try to keep it robust.
        
        all_data = []
        if os.path.exists(self.current_filename):
            try:
                with open(self.current_filename, 'r') as f:
                   if os.path.getsize(self.current_filename) > 0:
                       all_data = json.load(f)
            except json.JSONDecodeError:
                pass # file corrupted or empty
        
        all_data.extend(self.data_buffer)
        
        with open(self.current_filename, 'w') as f:
            json.dump(all_data, f, indent=2)
            
        self.data_buffer = [] # Clear buffer after save
