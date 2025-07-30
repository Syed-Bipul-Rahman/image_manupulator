import base64
from PIL import Image, ImageOps, ImageEnhance
from PIL.ExifTags import TAGS, GPSTAGS
import io
import os
import json
import sys
from pathlib import Path
from datetime import datetime
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

def validate_file_path(file_path, check_exists=True):
    """Validate and normalize file path"""
    try:
        path = Path(file_path.strip().strip('"\''))
        if check_exists and not path.exists():
            return False, f"File '{path}' does not exist"
        return True, str(path)
    except Exception as e:
        return False, f"Invalid file path: {str(e)}"

def ensure_directory_exists(file_path):
    """Ensure the directory for the file path exists"""
    try:
        directory = Path(file_path).parent
        directory.mkdir(parents=True, exist_ok=True)
        return True, ""
    except Exception as e:
        return False, f"Cannot create directory: {str(e)}"

def get_image_info(image_path):
    """Get comprehensive image information"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        
        image_path = result
        file_size = Path(image_path).stat().st_size
        
        with Image.open(image_path) as img:
            info = {
                "file_path": image_path,
                "file_name": Path(image_path).name,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "image_format": img.format,
                "image_mode": img.mode,
                "dimensions": {
                    "width": img.width,
                    "height": img.height,
                    "aspect_ratio": round(img.width / img.height, 2)
                },
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
            
            return info
            
    except Exception as e:
        return f"Error getting image info: {str(e)}"

def extract_exif_data(image_path, output_format="terminal"):
    """Extract EXIF data from image"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        
        image_path = result
        
        with Image.open(image_path) as img:
            exif_data = {}
            
            # Get basic EXIF
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # Handle GPS data specially
                    if tag == "GPSInfo":
                        gps_data = {}
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = str(gps_value)
                        exif_data[tag] = gps_data
                    else:
                        exif_data[tag] = str(value)
            
            # Get additional info
            if img.info:
                for key, value in img.info.items():
                    if key not in exif_data:
                        exif_data[key] = str(value)
            
            if not exif_data:
                return "No EXIF data found in the image"
            
            if output_format.lower() == "json":
                return json.dumps(exif_data, indent=2, ensure_ascii=False)
            else:
                # Terminal format
                output = "EXIF Data:\n" + "="*50 + "\n"
                for key, value in exif_data.items():
                    if isinstance(value, dict):
                        output += f"{key}:\n"
                        for sub_key, sub_value in value.items():
                            output += f"  {sub_key}: {sub_value}\n"
                    else:
                        output += f"{key}: {value}\n"
                return output
                
    except Exception as e:
        return f"Error extracting EXIF data: {str(e)}"

def compress_image(image_path, output_path, compression_type="lossy", quality=85, optimize=True):
    """Compress image with lossy or lossless compression"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        image_path = result
        
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        output_path = result
        
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        original_size = Path(image_path).stat().st_size
        
        with Image.open(image_path) as img:
            # Determine output format
            output_ext = Path(output_path).suffix.lower()
            format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', 
                         '.webp': 'WEBP', '.bmp': 'BMP', '.gif': 'GIF'}
            output_format = format_map.get(output_ext, 'JPEG')
            
            save_kwargs = {'optimize': optimize}
            
            if compression_type.lower() == "lossy":
                if output_format in ['JPEG', 'WEBP']:
                    save_kwargs['quality'] = quality
                    
                    # Convert to RGB if saving as JPEG
                    if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                        
            elif compression_type.lower() == "lossless":
                if output_format == 'PNG':
                    save_kwargs['compress_level'] = 9  # Maximum compression
                elif output_format == 'WEBP':
                    save_kwargs['lossless'] = True
                elif output_format == 'JPEG':
                    save_kwargs['quality'] = 100
            
            img.save(output_path, format=output_format, **save_kwargs)
            
            new_size = Path(output_path).stat().st_size
            compression_ratio = round((1 - new_size/original_size) * 100, 2)
            
            return (f"Image compressed successfully!\n"
                   f"Original size: {original_size:,} bytes ({original_size/1024/1024:.2f} MB)\n"
                   f"New size: {new_size:,} bytes ({new_size/1024/1024:.2f} MB)\n"
                   f"Compression: {compression_ratio}% reduction\n"
                   f"Saved to: {output_path}")
            
    except Exception as e:
        return f"Error compressing image: {str(e)}"

def convert_format(image_path, output_path, maintain_quality=True):
    """Convert image from one format to another"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        image_path = result
        
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        output_path = result
        
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        with Image.open(image_path) as img:
            original_format = img.format
            output_ext = Path(output_path).suffix.lower()
            format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', 
                         '.webp': 'WEBP', '.bmp': 'BMP', '.gif': 'GIF', '.heic': 'HEIF'}
            output_format = format_map.get(output_ext, 'JPEG')
            
            save_kwargs = {}
            
            # Handle format-specific conversions
            if output_format == 'JPEG':
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                if maintain_quality:
                    save_kwargs.update({'quality': 95, 'optimize': True})
                    
            elif output_format == 'PNG':
                if maintain_quality:
                    save_kwargs['compress_level'] = 1  # Fast compression
                    
            elif output_format == 'WEBP':
                if maintain_quality:
                    save_kwargs.update({'quality': 95, 'method': 6})
            
            img.save(output_path, format=output_format, **save_kwargs)
            
            original_size = Path(image_path).stat().st_size
            new_size = Path(output_path).stat().st_size
            
            return (f"Format conversion successful!\n"
                   f"Original: {original_format} ({original_size:,} bytes)\n"
                   f"New: {output_format} ({new_size:,} bytes)\n"
                   f"Saved to: {output_path}")
            
    except Exception as e:
        return f"Error converting format: {str(e)}"

def resize_image(image_path, output_path, dimensions, maintain_aspect=True, resample_filter="LANCZOS"):
    """Resize image with various options"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        image_path = result
        
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        output_path = result
        
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        # Parse dimensions
        if isinstance(dimensions, str):
            if 'x' in dimensions.lower():
                width, height = map(int, dimensions.lower().split('x'))
            else:
                # Single dimension, make it square
                width = height = int(dimensions)
        else:
            width, height = dimensions
        
        with Image.open(image_path) as img:
            original_size = img.size
            
            if maintain_aspect:
                img.thumbnail((width, height), getattr(Image.Resampling, resample_filter))
                new_size = img.size
            else:
                img = img.resize((width, height), getattr(Image.Resampling, resample_filter))
                new_size = (width, height)
            
            # Determine output format and save
            output_ext = Path(output_path).suffix.lower()
            format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', 
                         '.webp': 'WEBP', '.bmp': 'BMP'}
            output_format = format_map.get(output_ext, img.format)
            
            save_kwargs = {}
            if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
                save_kwargs['quality'] = 95
            
            img.save(output_path, format=output_format, **save_kwargs)
            
            return (f"Image resized successfully!\n"
                   f"Original size: {original_size[0]}x{original_size[1]}\n"
                   f"New size: {new_size[0]}x{new_size[1]}\n"
                   f"Saved to: {output_path}")
            
    except Exception as e:
        return f"Error resizing image: {str(e)}"

def rotate_image(image_path, output_path, angle, expand=True):
    """Rotate image by specified angle"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        image_path = result
        
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        output_path = result
        
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        with Image.open(image_path) as img:
            rotated = img.rotate(angle, expand=expand, fillcolor='white')
            
            # Determine output format
            output_ext = Path(output_path).suffix.lower()
            format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', 
                         '.webp': 'WEBP', '.bmp': 'BMP'}
            output_format = format_map.get(output_ext, img.format)
            
            save_kwargs = {}
            if output_format == 'JPEG' and rotated.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', rotated.size, (255, 255, 255))
                if rotated.mode in ('RGBA', 'LA'):
                    background.paste(rotated, mask=rotated.split()[-1])
                else:
                    background.paste(rotated)
                rotated = background
                save_kwargs['quality'] = 95
            
            rotated.save(output_path, format=output_format, **save_kwargs)
            
            return f"Image rotated by {angle}° and saved to: {output_path}"
            
    except Exception as e:
        return f"Error rotating image: {str(e)}"

def image_to_base64(image_path, output_text_file=None):
    """Convert image to base64 string with comprehensive error handling"""
    try:
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        
        image_path = result
        
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA' or img.mode == 'LA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            original_format = img.format or 'JPEG'
            img_byte_arr = io.BytesIO()
            save_format = original_format if original_format in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP'] else 'JPEG'
            img.save(img_byte_arr, format=save_format, quality=95 if save_format == 'JPEG' else None)
            img_byte_arr = img_byte_arr.getvalue()
            
            base64_string = base64.b64encode(img_byte_arr).decode('utf-8')
            full_data_uri = f"data:image/{save_format.lower()};base64,{base64_string}"
            
            if output_text_file:
                valid, result = validate_file_path(output_text_file, check_exists=False)
                if not valid:
                    return f"Error with output path: {result}"
                
                output_text_file = result
                success, error = ensure_directory_exists(output_text_file)
                if not success:
                    return f"Error: {error}"
                
                with open(output_text_file, 'w', encoding='utf-8') as f:
                    f.write(full_data_uri)
                return f"Base64 string saved to '{output_text_file}'"
            else:
                return full_data_uri
                    
    except Exception as e:
        return f"Error converting to base64: {str(e)}"

def read_base64_from_file(file_path):
    """Read base64 string from file with error handling"""
    try:
        valid, result = validate_file_path(file_path, check_exists=True)
        if not valid:
            return False, result
        
        file_path = result
        file_size = Path(file_path).stat().st_size
        if file_size > 100 * 1024 * 1024:  # 100MB
            return False, f"File is too large ({file_size / 1024 / 1024:.1f}MB). Maximum recommended size is 100MB."
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return False, "File is empty"
            
        return True, content
        
    except UnicodeDecodeError:
        return False, "File contains invalid characters. Please ensure it's a text file with base64 data."
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def base64_to_image(base64_input, output_path):
    """Convert base64 string to image with comprehensive error handling"""
    try:
        if os.path.exists(base64_input.strip().strip('"\'')):
            success, base64_string = read_base64_from_file(base64_input)
            if not success:
                return f"Error reading base64 file: {base64_string}"
        else:
            base64_string = base64_input.strip()
        
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        
        output_path = result
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        # Handle and validate output extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        output_path_obj = Path(output_path)
        output_ext = output_path_obj.suffix.lower()
        
        if output_path.startswith('.') and len(output_path_obj.parts) == 1:
            output_path = f"output{output_path}"
            output_path_obj = Path(output_path)
            output_ext = output_path_obj.suffix.lower()
        elif output_path.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            output_path = f"output.{output_path.lower()}"
            output_path_obj = Path(output_path)
            output_ext = output_path_obj.suffix.lower()
        
        if output_ext not in valid_extensions:
            return f"Error: Output file must have a valid image extension {valid_extensions}\nExample: output.jpg or just type 'jpg' for default name"
        
        if base64_string.startswith('data:image'):
            if ',' not in base64_string:
                return "Error: Invalid data URI format"
            base64_string = base64_string.split(',', 1)[1]
        
        base64_string = ''.join(base64_string.split())
        
        if not base64_string:
            return "Error: Empty base64 string"
        
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if not set(base64_string).issubset(valid_chars):
            return "Error: Invalid base64 characters found"
        
        try:
            img_data = base64.b64decode(base64_string, validate=True)
        except Exception as e:
            return f"Error decoding base64: {str(e)}"
        
        if len(img_data) == 0:
            return "Error: Decoded data is empty"
        
        try:
            img = Image.open(io.BytesIO(img_data))
            
            output_format = output_ext.replace('.', '').upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            save_kwargs = {}
            if output_format == 'JPEG':
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            
            img.save(output_path, format=output_format, **save_kwargs)
            
            width, height = img.size
            return f"Image saved to '{output_path}' (Size: {width}x{height}, Format: {output_format})"
            
        except Exception as e:
            return f"Error creating/saving image: {str(e)}"
            
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def get_default_output_name(input_path, suffix="_processed", extension=None):
    """Generate default output filename"""
    input_path = Path(input_path)
    if extension is None:
        extension = input_path.suffix
    return str(input_path.parent / f"{input_path.stem}{suffix}{extension}")

def main():
    print("🖼️  Complete Image Manipulator and Inspector Tool")
    print("=" * 60)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. 📊  Image Information & Inspector")
        print("2. 📋  Extract EXIF Data (Terminal/JSON)")
        print("3. 🗜️   Compress Image (Lossy/Lossless)")
        print("4. 🔄  Convert Image Format")
        print("5. 📐  Resize Image")
        print("6. 🔃  Rotate Image")
        print("7. 📱  Convert Image to Base64")
        print("8. 🖼️   Convert Base64 to Image")
        print("9. ❌  Exit")
        
        choice = input("Enter choice (1-9): ").strip()

        if choice == '1':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            print("Analyzing image...")
            result = get_image_info(image_path)
            if isinstance(result, dict):
                print("\n📊 Image Information:")
                print("=" * 40)
                print(f"📁 File: {result['file_name']}")
                print(f"📍 Path: {result['file_path']}")
                print(f"💾 Size: {result['file_size_mb']} MB ({result['file_size_bytes']:,} bytes)")
                print(f"🖼️  Format: {result['image_format']}")
                print(f"🎨 Mode: {result['image_mode']}")
                print(f"📐 Dimensions: {result['dimensions']['width']}x{result['dimensions']['height']}")
                print(f"📏 Aspect Ratio: {result['dimensions']['aspect_ratio']}")
                print(f"👁️  Transparency: {'Yes' if result['has_transparency'] else 'No'}")
            else:
                print(result)
                
        elif choice == '2':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            format_choice = input("Output format (terminal/json) [default: terminal]: ").strip().lower()
            if not format_choice:
                format_choice = "terminal"
                
            print("Extracting EXIF data...")
            result = extract_exif_data(image_path, format_choice)
            print(result)
            
            # Option to save JSON to file
            if format_choice == "json":
                save_choice = input("\nSave to file? (y/n): ").strip().lower()
                if save_choice == 'y':
                    output_file = input("Enter output JSON file path (or press Enter for default): ").strip()
                    if not output_file:
                        output_file = get_default_output_name(image_path, "_exif", ".json")
                    
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result)
                        print(f"EXIF data saved to: {output_file}")
                    except Exception as e:
                        print(f"Error saving file: {str(e)}")
                        
        elif choice == '3':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            output_path = input("Enter output file path (or press Enter for default): ").strip()
            if not output_path:
                output_path = get_default_output_name(image_path, "_compressed")
            
            compression_type = input("Compression type (lossy/lossless) [default: lossy]: ").strip().lower()
            if not compression_type:
                compression_type = "lossy"
            
            if compression_type == "lossy":
                quality = input("Quality (1-100) [default: 85]: ").strip()
                quality = int(quality) if quality.isdigit() else 85
            else:
                quality = 100
            
            print("Compressing image...")
            result = compress_image(image_path, output_path, compression_type, quality)
            print(result)
            
        elif choice == '4':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            print("Supported formats: jpg, png, webp, bmp, gif")
            target_format = input("Enter target format (e.g., jpg, png): ").strip().lower()
            if not target_format:
                print("Error: Please specify target format")
                continue
            
            if not target_format.startswith('.'):
                target_format = f".{target_format}"
            
            output_path = input("Enter output file path (or press Enter for default): ").strip()
            if not output_path:
                input_path_obj = Path(image_path)
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_converted{target_format}")
            
            maintain_quality = input("Maintain high quality? (y/n) [default: y]: ").strip().lower()
            maintain_quality = maintain_quality != 'n'
            
            print("Converting format...")
            result = convert_format(image_path, output_path, maintain_quality)
            print(result)
            
        elif choice == '5':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            dimensions = input("Enter dimensions (e.g., 800x600 or 800 for square): ").strip()
            if not dimensions:
                print("Error: Please specify dimensions")
                continue
            
            output_path = input("Enter output file path (or press Enter for default): ").strip()
            if not output_path:
                output_path = get_default_output_name(image_path, "_resized")
            
            maintain_aspect = input("Maintain aspect ratio? (y/n) [default: y]: ").strip().lower()
            maintain_aspect = maintain_aspect != 'n'
            
            print("Resizing image...")
            result = resize_image(image_path, output_path, dimensions, maintain_aspect)
            print(result)
            
        elif choice == '6':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
            
            angle = input("Enter rotation angle in degrees (e.g., 90, -45): ").strip()
            try:
                angle = float(angle)
            except ValueError:
                print("Error: Please enter a valid number for angle")
                continue
            
            output_path = input("Enter output file path (or press Enter for default): ").strip()
            if not output_path:
                output_path = get_default_output_name(image_path, f"_rotated_{int(angle)}")
            
            expand = input("Expand canvas to fit rotated image? (y/n) [default: y]: ").strip().lower()
            expand = expand != 'n'
            
            print("Rotating image...")
            result = rotate_image(image_path, output_path, angle, expand)
            print(result)
            
        elif choice == '7':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
                
            save_to_file = input("Save to text file? (y/n) [default: y]: ").strip().lower()
            output_file = None
            if save_to_file != 'n':
                output_file = input("Enter output text file path (or press Enter for default): ").strip()
                if not output_file:
                    output_file = get_default_output_name(image_path, "_base64", ".txt")
                
            print("Converting image to base64...")
            result = image_to_base64(image_path, output_file)
            if result.startswith("Error"):
                print(result)
            else:
                print(f"Base64 string (length: {len(result)} characters):")
                print("-" * 50)
                if len(result) > 1000:
                    print(f"{result[:500]}...{result[-500:]}")
                    print(f"\n[Truncated for display - full string is {len(result)} characters]")
                else:
                    print(result)
                        
        elif choice == '8':
            base64_input = input("Enter base64 string OR path to text file containing base64: ").strip()
            if not base64_input:
                print("Error: Please provide base64 string or file path")
                continue
                
            output_path = input("Enter output image file path (e.g., output.jpg, or just 'jpg' for default): ").strip()
            if not output_path:
                print("Error: Please provide output file path or extension")
                continue
                
            print("Converting base64 to image...")
            result = base64_to_image(base64_input, output_path)
            print(result)
            
        elif choice == '9':
            print("👋 Thanks for using Image Manipulator Tool!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-9.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("Please report this issue if it persists.")