# Enhanced Image Manipulator Pro

A comprehensive image manipulation tool with both command-line and GUI interfaces. The enhanced version provides advanced features, batch processing, and an intuitive graphical user interface for easy image editing.

## Features

### Basic Features (CLI & GUI)
- **Image Information & Inspector**: Get detailed information about an image, including dimensions, format, size, aspect ratio, and transparency.
- **EXIF Data Extraction**: Extract and display EXIF metadata from images. The output can be in a human-readable format or as a JSON object, which can be saved to a file.
- **Image Compression**: Reduce file size using either lossy or lossless compression. For lossy compression, you can specify the quality level.
- **Format Conversion**: Convert images between various formats, including JPEG, PNG, WEBP, BMP, and GIF. It also supports reading HEIC files.
- **Image Resizing**: Resize images to specific dimensions. You can choose to maintain the aspect ratio or resize to exact dimensions.
- **Image Rotation**: Rotate images by any specified angle.
- **Base64 Conversion**:
    - Convert an image file into a base64 encoded string, which can be saved to a text file.
    - Convert a base64 string (or a file containing it) back into an image file.

### Enhanced Features (GUI Only)
- **Real-time Image Enhancement**:
  - Brightness adjustment with live preview
  - Contrast control with sliders
  - Saturation enhancement
  - Sharpness adjustment
  
- **Advanced Filters**:
  - Grayscale conversion
  - Sepia tone effect
  - Blur effects (standard and Gaussian)
  - Edge enhancement and detection
  - Emboss effect
  - Vintage filter
  - Cool and warm color filters

- **Smart Cropping**:
  - Aspect ratio presets (1:1, 4:3, 16:9, 3:2)
  - Center crop functionality
  - Custom cropping ratios

- **Watermarking**:
  - Add text watermarks to images
  - Customizable position (corners, center)
  - Semi-transparent overlay

- **Advanced Analysis**:
  - Color palette extraction (top 10 colors)
  - RGB histogram display
  - Face detection with automatic blur

- **Batch Processing**:
  - Process multiple images at once
  - Batch resize with progress tracking
  - Batch format conversion
  - Batch compression
  - Batch filter application

- **User-Friendly Interface**:
  - File selection dialogs (no manual typing)
  - Real-time image preview
  - Tabbed organization of features
  - Progress bars for batch operations
  - Comprehensive image information display

## Dependencies

### For CLI version (image_manupulator.py):
```bash
pip install Pillow pillow-heif
```

### For Enhanced GUI version (enhanced_image_manipulator.py):
```bash
pip install -r requirements.txt
```

The enhanced version requires the following Python libraries:
- `Pillow` (>=10.0.0) - Core image processing
- `pillow-heif` (>=0.10.0) - HEIC/HEIF format support
- `opencv-python` (>=4.8.0) - Face detection and advanced image processing
- `numpy` (>=1.24.0) - Array operations for filters
- `matplotlib` (>=3.7.0) - Histogram display

## Usage

### 1. Command Line Interface (Original)
```bash
pip install Pillow pillow-heif
python image_manupulator.py
```

### 2. Enhanced GUI Interface (Desktop)
```bash
# Install tkinter first (macOS)
./install_tkinter.sh
# OR manually: brew install python-tk

# Install other dependencies
pip install opencv-python numpy matplotlib Pillow pillow-heif

# Run the GUI
python enhanced_image_manipulator.py
```

### 3. Web-Based GUI Interface (Recommended - No tkinter needed!)
```bash
# Install Streamlit and basic dependencies
pip install streamlit Pillow pillow-heif numpy

# Run the web interface
streamlit run web_image_manipulator.py
```

## Troubleshooting

### tkinter Issues on macOS
If you get `ModuleNotFoundError: No module named '_tkinter'`, try:

1. **Automated fix:**
   ```bash
   ./install_tkinter.sh
   ```

2. **Manual fix:**
   ```bash
   brew install python-tk
   ```

3. **Alternative - Use the web version:**
   ```bash
   pip install streamlit
   streamlit run web_image_manipulator.py
   ```

The web version has all the same features and works in your browser!

## Interface Overview

The enhanced GUI is organized into tabs:

1. **Basic**: Resize, rotate, and format conversion
2. **Enhance**: Brightness, contrast, saturation, and sharpness controls
3. **Filters**: Various artistic and enhancement filters
4. **Advanced**: Cropping, watermarking, and analysis tools
5. **Batch**: Multi-file processing capabilities

## Key Improvements

- ✅ **No Manual Typing**: Use file selection dialogs instead of typing paths
- ✅ **Real-time Preview**: See changes immediately
- ✅ **Batch Processing**: Handle multiple images efficiently
- ✅ **Advanced Filters**: Professional-grade image effects
- ✅ **Face Detection**: Automatic face blur for privacy
- ✅ **Color Analysis**: Extract palettes and view histograms
- ✅ **Progress Tracking**: Visual feedback for long operations
- ✅ **Modern UI**: Intuitive tabbed interface
