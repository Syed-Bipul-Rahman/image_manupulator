# Image Manipulator and Inspector

A command-line tool for performing a variety of image manipulation and inspection tasks. This script provides a simple, interactive interface to handle common image processing needs.

## Features

- **Image Information & Inspector**: Get detailed information about an image, including dimensions, format, size, aspect ratio, and transparency.
- **EXIF Data Extraction**: Extract and display EXIF metadata from images. The output can be in a human-readable format or as a JSON object, which can be saved to a file.
- **Image Compression**: Reduce file size using either lossy or lossless compression. For lossy compression, you can specify the quality level.
- **Format Conversion**: Convert images between various formats, including JPEG, PNG, WEBP, BMP, and GIF. It also supports reading HEIC files.
- **Image Resizing**: Resize images to specific dimensions. You can choose to maintain the aspect ratio or resize to exact dimensions.
- **Image Rotation**: Rotate images by any specified angle.
- **Base64 Conversion**:
    - Convert an image file into a base64 encoded string, which can be saved to a text file.
    - Convert a base64 string (or a file containing it) back into an image file.

## Dependencies

The script requires the following Python libraries:

- `Pillow`
- `pillow-heif`

You can install them using pip:
```bash
pip install Pillow pillow-heif
```

## Usage

To run the tool, execute the script from your terminal:

```bash
python image_manupulator.py
```

The script will present a menu of options. Enter the number corresponding to the action you want to perform and follow the on-screen prompts.
