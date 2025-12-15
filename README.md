# HR Recorder

A GUI application for recording heart rate data from Polar devices (Verity Sense or H10 chest strap) with real-time visualization and persistent data storage.

## Overview

HR Recorder connects to Polar heart rate monitors via Bluetooth Low Energy (BLE), displays live heart rate data in a plotting interface, and saves the data to JSON files at configurable intervals. The application is built with Python using DearPyGUI for the interface and integrates asyncio for BLE operations.

## Features

- **Device Support**: Connect to Polar Verity Sense or Polar H10 chest strap
- **Live Visualization**: Real-time heart rate plotting (displays last 300 data points)
- **Configurable Sampling**: Set sampling interval (default: 10 seconds)
- **Data Persistence**: Automatic periodic saves to prevent data loss
- **Subject Management**: Assign subject IDs for organized data collection
- **JSON Export**: Structured data files with metadata and timestamps

## Architecture

### Core Components

**main.py** - Main application class (`HRRecorderApp`)
- Integrates DearPyGUI interface with asyncio event loop
- Manages UI state and user interactions
- Coordinates between recorder and data manager
- Handles real-time plot updates via data queue

**recorder.py** - BLE interface (`PolarRecorder`)
- Scans for and connects to Polar devices
- Manages heart rate data streaming using `polar-python` library
- Handles connection retries and error recovery
- Provides async callbacks for HR data

**data_manager.py** - Data persistence (`DataManager`)
- Buffers incoming heart rate data
- Creates timestamped JSON files with naming convention: `sub-{id}_date-{YYYYMMDD}_time-{HHMMSS}.json`
- Auto-saves every 60 data points
- Stores metadata (subject ID, date, time, sampling interval)

### Data Flow

1. User connects to Polar device via BLE
2. Device streams heart rate data asynchronously
3. Data queued for UI processing
4. Real-time plot updated on each frame
5. Data sampled at configured interval and buffered
6. Buffer auto-saved periodically and on recording stop

## Installation

### Prerequisites

- Python 3.8 or higher
- Bluetooth adapter (built-in or USB)
- Windows 10/11 or macOS

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kelvinlim/hrrecorder.git
cd hrrecorder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
- `dearpygui` - GUI framework
- `bleak` - Cross-platform BLE library
- `polar-python` - Polar device SDK
- `pyinstaller` - For building executables

## Usage

### Running from Source

```bash
python main.py
```

### Using the Application

1. **Enter Subject ID**: Type an identifier for the recording session
2. **Select Device Type**: Choose "Polar Sense" or "Polar H10" from dropdown
3. **Connect**: Click "Connect" button to scan and pair with device
4. **Set Sampling**: Adjust sampling interval in seconds (default: 10)
5. **Start Recording**: Click "Start Recording" to begin data collection
6. **Monitor**: Watch real-time heart rate plot
7. **Stop Recording**: Click "Stop Recording" to end and save data

### Output Files

Data files are saved in the `data/` directory with the format:

```
sub-{subject_id}_date-{YYYYMMDD}_time-{HHMMSS}.json
```

JSON structure:
```json
{
  "subject": "subject_id",
  "date": "2025-12-15",
  "time": "14:30:00",
  "sampling_interval_sec": 10,
  "data": [
    {
      "timestamp": 1702654200.123,
      "hr": 72
    }
  ]
}
```

## Building Executables

### Windows

```bash
pyinstaller hrrecorder.spec
```

The executable will be created in `dist/hrrecorder.exe`

### macOS

```bash
pyinstaller hrrecorder.spec
```

The application bundle will be created in `dist/hrrecorder.app`

### Build Configuration

The `hrrecorder.spec` file configures PyInstaller with:
- Single-file executable
- Console disabled (windowed mode)
- UPX compression enabled
- macOS app bundle support

## Development

### Debug Scripts

- **debug_bleak.py**: Test direct BLE connectivity with Bleak
- **debug_connect.py**: Test Polar device connection using polar-python

Run these to troubleshoot connection issues:
```bash
python debug_bleak.py
python debug_connect.py
```

### Project Structure

```
hrrecorder/
├── main.py                  # Main application
├── recorder.py              # BLE/Polar interface
├── data_manager.py          # Data persistence
├── requirements.txt         # Python dependencies
├── hrrecorder.spec         # PyInstaller config
├── debug_bleak.py          # BLE debug script
├── debug_connect.py        # Polar debug script
├── README.md               # This file
├── ApplicationDescription.md  # Original requirements
└── data/                   # Output directory (created on first run)
```

## Troubleshooting

**Connection Issues**
- Ensure Bluetooth is enabled
- Device must be in pairing mode
- Try the debug scripts to isolate issues
- Check device battery level

**Data Loss**
- Data auto-saves every 60 points
- Manual save on "Stop Recording"
- Check `data/` directory for files

**Performance**
- Plot displays last 300 points for performance
- Reduce sampling interval for more frequent saves
- Close other Bluetooth applications

## License

MIT License - See repository for details

## Contributing

Contributions welcome! Please open issues or pull requests on GitHub.

