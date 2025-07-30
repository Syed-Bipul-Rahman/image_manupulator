import base64
from PIL import Image
import io
import os
import sys
from pathlib import Path

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

def get_image_format(image_path):
    """Get image format, handle edge cases"""
    try:
        with Image.open(image_path) as img:
            format_name = img.format
            if format_name is None:
                # Try to determine format from file extension
                ext = Path(image_path).suffix.lower()
                format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', 
                            '.gif': 'GIF', '.bmp': 'BMP', '.webp': 'WEBP'}
                format_name = format_map.get(ext, 'JPEG')
            return format_name
    except Exception:
        return 'JPEG'  # Default fallback

def image_to_base64(image_path, output_text_file=None):
    """Convert image to base64 string with comprehensive error handling"""
    try:
        # Validate input path
        valid, result = validate_file_path(image_path, check_exists=True)
        if not valid:
            return f"Error: {result}"
        
        image_path = result
        
        # Check if file is actually an image
        try:
            with Image.open(image_path) as img:
                # Handle different image modes
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG compatibility
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA' or img.mode == 'LA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                # Get original format
                original_format = get_image_format(image_path)
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                save_format = original_format if original_format in ['JPEG', 'PNG', 'GIF', 'BMP', 'WEBP'] else 'JPEG'
                img.save(img_byte_arr, format=save_format, quality=95 if save_format == 'JPEG' else None)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode to base64
                base64_string = base64.b64encode(img_byte_arr).decode('utf-8')
                full_data_uri = f"data:image/{save_format.lower()};base64,{base64_string}"
                
                # Save to text file if specified
                if output_text_file:
                    valid, result = validate_file_path(output_text_file, check_exists=False)
                    if not valid:
                        return f"Error with output path: {result}"
                    
                    output_text_file = result
                    success, error = ensure_directory_exists(output_text_file)
                    if not success:
                        return f"Error: {error}"
                    
                    try:
                        with open(output_text_file, 'w', encoding='utf-8') as f:
                            f.write(full_data_uri)
                        return f"Base64 string saved to '{output_text_file}'"
                    except Exception as e:
                        return f"Error writing to file: {str(e)}"
                else:
                    # Return the base64 string (might be very long)
                    return full_data_uri
                    
        except Exception as e:
            return f"Error processing image: {str(e)}"
            
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def read_base64_from_file(file_path):
    """Read base64 string from file with error handling"""
    try:
        valid, result = validate_file_path(file_path, check_exists=True)
        if not valid:
            return False, result
        
        file_path = result
        
        # Check file size (warn if very large)
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
        # Handle file input vs direct string input
        if os.path.exists(base64_input.strip().strip('"\'')):
            # It's a file path
            success, base64_string = read_base64_from_file(base64_input)
            if not success:
                return f"Error reading base64 file: {base64_string}"
        else:
            # It's a direct base64 string
            base64_string = base64_input.strip()
        
        # Validate output path
        valid, result = validate_file_path(output_path, check_exists=False)
        if not valid:
            return f"Error with output path: {result}"
        
        output_path = result
        
        # Ensure output directory exists
        success, error = ensure_directory_exists(output_path)
        if not success:
            return f"Error: {error}"
        
        # Handle and validate output extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        output_path_obj = Path(output_path)
        output_ext = output_path_obj.suffix.lower()
        
        # If user just entered an extension (like ".jpg"), create a proper filename
        if output_path.startswith('.') and len(output_path_obj.parts) == 1:
            output_path = f"output{output_path}"
            output_path_obj = Path(output_path)
            output_ext = output_path_obj.suffix.lower()
        
        # If user entered just an extension without dot (like "jpg"), add dot and filename
        elif output_path.lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            output_path = f"output.{output_path.lower()}"
            output_path_obj = Path(output_path)
            output_ext = output_path_obj.suffix.lower()
        
        if output_ext not in valid_extensions:
            return f"Error: Output file must have a valid image extension {valid_extensions}\nExample: output.jpg or just type 'jpg' for default name"
        
        # Clean base64 string
        if base64_string.startswith('data:image'):
            if ',' not in base64_string:
                return "Error: Invalid data URI format"
            base64_string = base64_string.split(',', 1)[1]
        
        # Remove any whitespace/newlines
        base64_string = ''.join(base64_string.split())
        
        # Validate base64 string
        if not base64_string:
            return "Error: Empty base64 string"
        
        # Check if string contains only valid base64 characters
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if not set(base64_string).issubset(valid_chars):
            return "Error: Invalid base64 characters found"
        
        # Decode base64
        try:
            img_data = base64.b64decode(base64_string, validate=True)
        except Exception as e:
            return f"Error decoding base64: {str(e)}"
        
        if len(img_data) == 0:
            return "Error: Decoded data is empty"
        
        # Create image from data
        try:
            img = Image.open(io.BytesIO(img_data))
            
            # Handle different output formats
            output_format = output_ext.replace('.', '').upper()
            if output_format == 'JPG':
                output_format = 'JPEG'
            
            # Convert image mode if necessary
            if output_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            # Save image
            save_kwargs = {}
            if output_format == 'JPEG':
                save_kwargs['quality'] = 95
                save_kwargs['optimize'] = True
            
            img.save(output_path, format=output_format, **save_kwargs)
            
            # Get image info for confirmation
            width, height = img.size
            return f"Image saved to '{output_path}' (Size: {width}x{height}, Format: {output_format})"
            
        except Exception as e:
            return f"Error creating/saving image: {str(e)}"
            
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def get_default_output_name(input_path, suffix="_base64", extension=".txt"):
    """Generate default output filename"""
    input_path = Path(input_path)
    return str(input_path.parent / f"{input_path.stem}{suffix}{extension}")

def main():
    print("Image <-> Base64 Converter with File Support")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. Convert image to base64 string (save to text file)")
        print("2. Convert image to base64 string (display in terminal)")
        print("3. Convert base64 string/file to image")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ").strip()

        if choice == '1':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
                
            # Generate default output name or ask for custom
            default_output = get_default_output_name(image_path)
            output_file = input(f"Enter output text file path (press Enter for '{default_output}'): ").strip()
            
            if not output_file:
                output_file = default_output
                
            print("Converting image to base64...")
            result = image_to_base64(image_path, output_file)
            print(result)
            
        elif choice == '2':
            image_path = input("Enter image file path: ").strip()
            if not image_path:
                print("Error: Please provide an image file path")
                continue
                
            print("Converting image to base64...")
            result = image_to_base64(image_path)
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
                    
        elif choice == '3':
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
            
        elif choice == '4':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()