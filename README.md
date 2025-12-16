# HR Recorder

A GUI application for recording heart rate data from Polar devices (Verity Sense or H10 chest strap) with real-time visualization and persistent data storage.

## Overview

HR Recorder connects to Polar heart rate monitors via Bluetooth Low Energy (BLE), displays live heart rate data in a plotting interface, and saves the data to JSON files at configurable intervals. The application is built with Python using DearPyGUI for the interface and integrates asyncio for BLE operations.

## Features

- **Device Support**: Connect to Polar Verity Sense or Polar H10 chest strap
- **Device Picker with Addresses**: Scan and select exact devices by name + MAC address
- **Busy Indicator (Local Soft Lock)**: Marks devices already selected in this app window to avoid double-pick
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
2. **Select Device Type**: Choose "Polar Sense" or "Polar H10" from dropdown (this filters scan results)
3. **Scan Devices**: Click "Scan Devices" to list nearby devices matching the selected type as `Name (Address)`; entries marked `[busy]` are already selected in this app window
4. **Select Device**: Pick the exact device you want; selection stores its address
5. **Connect**: Click "Connect" to pair to that specific address (prevents accidental cross-pairing)
6. **Set Sampling**: Adjust sampling interval in seconds (default: 10)
7. **Start Recording**: Click "Start Recording" to begin data collection
8. **Monitor**: Watch real-time heart rate plot
9. **Stop Recording**: Click "Stop Recording" to end and save data

**Note**: The version number is displayed in the lower right corner of the app window.

### Multi-user / multi-device tips
- Run one app window per sensor; each window soft-locks the device it selects (shows `[busy]` in the list)
- Label devices physically with the last 4 chars of their address to pick the right one
- If a device is in use elsewhere, disconnect it there before connecting from this app

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
   "device_name": "Polar Sense",
   "device_address": "AA:BB:CC:DD:EE:FF",
  "data": [
    {
      "timestamp": 1702654200.123,
      "hr": 72
    }
  ]
}
```

## Installation from Pre-built Releases

### Download

Download the latest release from the [Releases page](https://github.com/kelvinlim/hrrecorder/releases).
HRRecorder-Installer
**Windows 10/11 (x64)**
- `hrrecorder-setup.exe` - Windows Installer (Recommended)
- `hrrecorder.exe` - Standalone executable

**macOS (Apple Silicon / M1/M2/M3)**
- `hrrecorder.dmg` - macOS Disk Image

### Installing

**Windows:**
1. Download `hrrecorder-setup.exe`
2. Run the installer and follow prompts
3. Launch from Start Menu or Desktop shortcut

**macOS:**
1. Download `hrrecorder.dmg`
2. Open the DMG file
3. Drag HR Recorder to your Applications folder
4. Launch from Applications

### Verifying Downloads

Each release includes SHA256 checksums (`.sha256` files). To verify:

**Windows (PowerShell):**
```powershell
Get-FileHash HRRecorder-Installer.exe -Algorithm SHA256
# Compare with contents of HRRecorder-Installer.exe.sha256
```

**macOS/Linux:**
```bash
shasum -a 256 hrrecorder.dmg
# Compare with contents of hrrecorder.dmg.sha256
```

## Building from Source

### Local Build

**Windows:**
```bash
# Build executable
pyinstaller hrrecorder.spec

# Create installer (requires Inno Setup)
iscc hrrecorder.iss
```

Outputs:
- `dist/hrrecorder.exe` - Standalone executable
- `dist/HRRecorder-Installer.exe` - Windows installer

**macOS:**
```bash
# Build app bundle
pyinstaller hrrecorder.spec

# Create DMG
chmod +x create_dmg.sh
./create_dmg.sh
```

Outputs:
- `dist/hrrecorder.app` - macOS application bundle
- `dist/hrrecorder.dmg` - Disk image installer

### Build Configuration

The `hrrecorder.spec` file configures PyInstaller with:
- Platform-specific icons and metadata
- Console disabled (windowed mode)
- UPX compression enabled
- macOS app bundle with proper Info.plist
- Bluetooth permissions for macOS

## Releases and CI/CD

### Automated Builds

This project uses GitHub Actions to automatically build releases for Windows and macOS when version tags are pushed.

### Creating a New Release

1. **Update version number** in the following files:
   - `version.py` (`__version__` - displays in app and used by macOS bundle)
   - `hrrecorder.iss` (MyAppVersion for Windows installer)

2. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Bump version to v1.0.1"
   ```

3. **Create and push a version tag:**
   ```bash
   # Create annotated tag (recommended)
   git tag -a v1.0.1 -m "Release version 1.0.1"
   
   # Or create lightweight tag
   git tag v1.0.1
   
   # Push commits and tags
   git push origin main
   git push origin v1.0.1
   ```

4. **Monitor the build:**
   - Go to the "Actions" tab in your GitHub repository
   - Watch the "Build and Release" workflow execute
   - Builds typically take 5-10 minutes

5. **Release published automatically:**
   - Once builds complete, a new release is created
   - Release includes Windows installer, Windows executable, and macOS DMG
   - SHA256 checksums generated for all files

### Version Tag Format

Use semantic versioning with a `v` prefix:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)
- `v1.0.0-beta` - Pre-release
- `v1.0.0-rc1` - Release candidate

### Viewing Releases

```bash
# List all tags
git tag -l

# View tag details
git show v1.0.0

# Delete local tag (if needed)
git tag -d v1.0.0

# Delete remote tag (if needed)
git push origin --delete v1.0.0
```

### Manual Release Process

If you need to create a release manually (without CI/CD):

1. Build for each platform locally
2. Create release on GitHub:
   ```bash
   # Using GitHub CLI
   gh release create v1.0.0 \
     dist/hrrecorder-setup.exe \
     dist/hrrecorder.exe \
     dist/hrrecorder.dmg \
     --title "HR Recorder v1.0.0" \
     --notes "Release notes here"
   ```

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

