# PyQt App Builder

A simple and intuitive GUI tool that wraps PyInstaller to easily convert Python scripts into standalone executables.
![apphome](https://github.com/user-attachments/assets/826fa51a-d4ad-43da-a820-e7c422b6e6d4)
![progress](https://github.com/user-attachments/assets/24c970ac-8c40-470c-b8a8-58762cb5980d)


## Features

- **User-friendly interface** for PyInstaller configuration
- **Drag & drop support** for selecting script files
- **Custom executable options**:
  - One-file or one-directory output
  - Console/no-console window
  - Custom application name
  - Custom application icon
- **Dependency management** - easily add additional files and folders
- **Command preview** - see and copy the generated PyInstaller command
- **Command injection** - paste existing PyInstaller commands to configure the UI
- **Real-time build output** monitoring
- **Error detection** for common PyInstaller issues

## Installation

### Prerequisites
- Python 3.6+
- PyQt6
- PyInstaller (can be installed through the app)

### Option 1: From Source
1. Clone this repository
```
git clone https://github.com/64one/AppBuilder.git
cd AppBuilder
```

2. Install dependencies
```
pip install -r requirements.txt
```

3. Run the application
```
python main.py
```

### Option 2: Using the Executable
Download the latest release from the [Releases page](https://github.com/yourusername/pyqt-app-builder/releases).

## Usage

1. **Select a Python script** using the "Select Script" button
2. **Configure output options**:
   - Set application name
   - Choose whether to show console
   - Choose one-file or one-directory output
   - Select an icon (optional)
   - Set output directory (optional)
3. **Add dependencies** if needed:
   - Add individual files
   - Add entire folders
4. **Build the executable** by clicking the "Build" button
5. **Monitor the build progress** in the progress tab

## Tips & Tricks

- **Command Injection**: Copy a PyInstaller command from elsewhere and inject it into the app using the "Inject" button to configure all settings at once.
- **Adding Files**: Make sure dependency files are correctly organized relative to your main script.
- **Troubleshooting**: Check the output tab for detailed error messages if your build fails.

## Common Issues

- **File not found errors**: Ensure all dependency paths are correctly specified and relative to the main script.
- **Icon issues**: Make sure your icon is in .ico format.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Powered by [PyInstaller](https://www.pyinstaller.org/)
