import streamlit as st
import base64
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFont, ImageDraw
from PIL.ExifTags import TAGS, GPSTAGS
import io
import os
import json
import zipfile
from pathlib import Path
from datetime import datetime
import pillow_heif
import numpy as np
from collections import Counter
import tempfile

# Register HEIF opener
pillow_heif.register_heif_opener()

# Page config
st.set_page_config(
    page_title="Enhanced Image Manipulator Pro",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .success-box {
        border: 1px solid #4CAF50;
        border-radius: 5px;
        padding: 10px;
        background-color: #dff0d8;
        color: #3c763d;
    }
    .error-box {
        border: 1px solid #f44336;
        border-radius: 5px;
        padding: 10px;
        background-color: #f2dede;
        color: #a94442;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🖼️ Enhanced Image Manipulator Pro</h1>
    <p>Professional image editing with advanced features and batch processing</p>
</div>
""", unsafe_allow_html=True)

def get_image_info(image):
    """Get comprehensive image information"""
    info = {
        "format": image.format,
        "mode": image.mode,
        "size": image.size,
        "width": image.width,
        "height": image.height,
        "aspect_ratio": round(image.width / image.height, 2),
        "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
    }
    return info

def apply_sepia(image):
    """Apply sepia effect"""
    img_array = np.array(image)
    sepia_filter = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = img_array.dot(sepia_filter.T)
    sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
    return Image.fromarray(sepia_img)

def apply_vintage(image):
    """Apply vintage effect"""
    # Apply sepia
    vintage_img = apply_sepia(image)
    # Add slight blur
    vintage_img = vintage_img.filter(ImageFilter.GaussianBlur(radius=0.5))
    # Reduce contrast
    enhancer = ImageEnhance.Contrast(vintage_img)
    return enhancer.enhance(0.9)

def apply_cool_filter(image):
    """Apply cool color filter"""
    img_array = np.array(image).astype(float)
    img_array[:, :, 0] *= 0.8  # Reduce red
    img_array[:, :, 2] *= 1.2  # Boost blue
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array)

def apply_warm_filter(image):
    """Apply warm color filter"""
    img_array = np.array(image).astype(float)
    img_array[:, :, 0] *= 1.2  # Boost red
    img_array[:, :, 1] *= 1.1  # Boost green slightly
    img_array[:, :, 2] *= 0.8  # Reduce blue
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    return Image.fromarray(img_array)

def crop_to_aspect_ratio(image, ratio):
    """Crop image to specific aspect ratio"""
    width, height = image.size
    
    if ratio == "1:1":
        size = min(width, height)
        new_width, new_height = size, size
    elif ratio == "4:3":
        if width > height:
            new_height = height
            new_width = int(height * 4 / 3)
        else:
            new_width = width
            new_height = int(width * 3 / 4)
    elif ratio == "16:9":
        if width > height:
            new_height = height
            new_width = int(height * 16 / 9)
        else:
            new_width = width
            new_height = int(width * 9 / 16)
    elif ratio == "3:2":
        if width > height:
            new_height = height
            new_width = int(height * 3 / 2)
        else:
            new_width = width
            new_height = int(width * 2 / 3)
    else:
        return image
    
    # Ensure we don't exceed original dimensions
    new_width = min(new_width, width)
    new_height = min(new_height, height)
    
    # Center crop
    left = (width - new_width) // 2
    top = (height - new_height) // 2
    right = left + new_width
    bottom = top + new_height
    
    return image.crop((left, top, right, bottom))

def add_watermark(image, text, position):
    """Add text watermark to image"""
    watermarked = image.copy()
    
    # Create a transparent overlay
    overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try to use a reasonable font size
    font_size = max(20, min(watermarked.width, watermarked.height) // 20)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate position
    margin = 20
    if position == "Top Left":
        x, y = margin, margin
    elif position == "Top Right":
        x, y = watermarked.width - text_width - margin, margin
    elif position == "Bottom Left":
        x, y = margin, watermarked.height - text_height - margin
    elif position == "Bottom Right":
        x, y = watermarked.width - text_width - margin, watermarked.height - text_height - margin
    else:  # Center
        x, y = (watermarked.width - text_width) // 2, (watermarked.height - text_height) // 2
    
    # Add semi-transparent background
    draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 200))
    
    # Composite the overlay
    if watermarked.mode != 'RGBA':
        watermarked = watermarked.convert('RGBA')
    watermarked = Image.alpha_composite(watermarked, overlay)
    
    if watermarked.mode == 'RGBA':
        watermarked = watermarked.convert('RGB')
        
    return watermarked

def extract_color_palette(image, num_colors=10):
    """Extract color palette from image"""
    rgb_img = image.convert('RGB')
    pixels = list(rgb_img.getdata())
    color_counts = Counter(pixels)
    most_common = color_counts.most_common(num_colors)
    
    palette_info = []
    total_pixels = len(pixels)
    for color, count in most_common:
        percentage = (count / total_pixels) * 100
        palette_info.append({
            'color': color,
            'count': count,
            'percentage': percentage
        })
    
    return palette_info

def pil_to_bytes(image, format='PNG'):
    """Convert PIL image to bytes"""
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes

# Initialize session state
if 'processed_images' not in st.session_state:
    st.session_state.processed_images = {}
if 'current_image' not in st.session_state:
    st.session_state.current_image = None

# Sidebar for navigation
st.sidebar.title("🛠️ Tools")
tool = st.sidebar.selectbox(
    "Select Tool",
    ["📊 Single Image Editor", "📦 Batch Processor", "🔍 Image Inspector", "📱 Base64 Converter"]
)

if tool == "📊 Single Image Editor":
    st.header("🖼️ Single Image Editor")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'heic', 'heif'],
        help="Upload an image to start editing"
    )
    
    if uploaded_file is not None:
        # Load image
        try:
            image = Image.open(uploaded_file)
            st.session_state.current_image = image
            original_image = image.copy()
            
            # Display original image info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("🖼️ Image Preview")
                st.image(image, caption="Original Image", use_column_width=True)
            
            with col2:
                st.subheader("📊 Image Information")
                info = get_image_info(image)
                st.write(f"**Format:** {info['format']}")
                st.write(f"**Mode:** {info['mode']}")
                st.write(f"**Dimensions:** {info['width']} × {info['height']}")
                st.write(f"**Aspect Ratio:** {info['aspect_ratio']}")
                st.write(f"**Transparency:** {'Yes' if info['has_transparency'] else 'No'}")
            
            # Editing tools
            st.subheader("🛠️ Editing Tools")
            
            # Create tabs for different operations
            tab1, tab2, tab3, tab4 = st.tabs(["🔧 Basic", "✨ Enhance", "🎨 Filters", "🔬 Advanced"])
            
            with tab1:
                st.write("### Resize")
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_width = st.number_input("Width", min_value=1, value=image.width, key="width")
                with col2:
                    new_height = st.number_input("Height", min_value=1, value=image.height, key="height")
                with col3:
                    maintain_aspect = st.checkbox("Maintain aspect ratio", value=True)
                
                if st.button("Resize Image"):
                    if maintain_aspect:
                        image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                    else:
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    st.success("Image resized!")
                    st.image(image, caption="Resized Image", use_column_width=True)
                
                st.write("### Rotate")
                angle = st.slider("Rotation Angle", min_value=-180, max_value=180, value=0, step=1)
                if st.button("Rotate Image"):
                    image = image.rotate(angle, expand=True, fillcolor='white')
                    st.success(f"Image rotated by {angle} degrees!")
                    st.image(image, caption="Rotated Image", use_column_width=True)
            
            with tab2:
                st.write("### Image Enhancement")
                
                # Enhancement controls
                brightness = st.slider("Brightness", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
                contrast = st.slider("Contrast", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
                saturation = st.slider("Saturation", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
                sharpness = st.slider("Sharpness", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
                
                if st.button("Apply Enhancements"):
                    # Apply brightness
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(brightness)
                    
                    # Apply contrast
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(contrast)
                    
                    # Apply saturation
                    enhancer = ImageEnhance.Color(image)
                    image = enhancer.enhance(saturation)
                    
                    # Apply sharpness
                    enhancer = ImageEnhance.Sharpness(image)
                    image = enhancer.enhance(sharpness)
                    
                    st.success("Enhancements applied!")
                    st.image(image, caption="Enhanced Image", use_column_width=True)
            
            with tab3:
                st.write("### Filters")
                
                filter_options = [
                    "None", "Grayscale", "Sepia", "Blur", "Gaussian Blur", 
                    "Edge Enhance", "Emboss", "Find Edges", "Vintage", "Cool", "Warm"
                ]
                
                selected_filter = st.selectbox("Choose Filter", filter_options)
                
                if st.button("Apply Filter") and selected_filter != "None":
                    if selected_filter == "Grayscale":
                        image = image.convert('L').convert('RGB')
                    elif selected_filter == "Sepia":
                        image = apply_sepia(image)
                    elif selected_filter == "Blur":
                        image = image.filter(ImageFilter.BLUR)
                    elif selected_filter == "Gaussian Blur":
                        image = image.filter(ImageFilter.GaussianBlur(radius=2))
                    elif selected_filter == "Edge Enhance":
                        image = image.filter(ImageFilter.EDGE_ENHANCE)
                    elif selected_filter == "Emboss":
                        image = image.filter(ImageFilter.EMBOSS)
                    elif selected_filter == "Find Edges":
                        image = image.filter(ImageFilter.FIND_EDGES)
                    elif selected_filter == "Vintage":
                        image = apply_vintage(image)
                    elif selected_filter == "Cool":
                        image = apply_cool_filter(image)
                    elif selected_filter == "Warm":
                        image = apply_warm_filter(image)
                    
                    st.success(f"{selected_filter} filter applied!")
                    st.image(image, caption=f"{selected_filter} Filter Applied", use_column_width=True)
            
            with tab4:
                st.write("### Cropping")
                aspect_ratios = ["Original", "1:1", "4:3", "16:9", "3:2"]
                selected_ratio = st.selectbox("Aspect Ratio", aspect_ratios)
                
                if st.button("Crop Image") and selected_ratio != "Original":
                    image = crop_to_aspect_ratio(image, selected_ratio)
                    st.success(f"Image cropped to {selected_ratio} aspect ratio!")
                    st.image(image, caption="Cropped Image", use_column_width=True)
                
                st.write("### Watermark")
                watermark_text = st.text_input("Watermark Text", value="Watermark")
                watermark_position = st.selectbox("Position", ["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"])
                
                if st.button("Add Watermark"):
                    image = add_watermark(image, watermark_text, watermark_position)
                    st.success("Watermark added!")
                    st.image(image, caption="Watermarked Image", use_column_width=True)
                
                st.write("### Color Analysis")
                if st.button("Extract Color Palette"):
                    palette = extract_color_palette(image)
                    st.write("**Top 10 Colors:**")
                    for i, color_info in enumerate(palette):
                        color = color_info['color']
                        percentage = color_info['percentage']
                        st.write(f"{i+1}. RGB{color} - {percentage:.2f}%")
            
            # Download processed image
            if image != original_image:
                st.subheader("💾 Download Processed Image")
                
                format_choice = st.selectbox("Output Format", ["PNG", "JPEG", "WEBP"])
                
                # Convert image for download
                if format_choice == "JPEG" and image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode in ('RGBA', 'LA'):
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image)
                    image = background
                
                img_bytes = pil_to_bytes(image, format_choice)
                
                st.download_button(
                    label=f"Download as {format_choice}",
                    data=img_bytes,
                    file_name=f"processed_image.{format_choice.lower()}",
                    mime=f"image/{format_choice.lower()}"
                )
                
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")

elif tool == "📦 Batch Processor":
    st.header("📦 Batch Image Processor")
    
    uploaded_files = st.file_uploader(
        "Choose multiple image files",
        type=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'],
        accept_multiple_files=True,
        help="Upload multiple images for batch processing"
    )
    
    if uploaded_files:
        st.write(f"**{len(uploaded_files)} files uploaded**")
        
        # Batch operation selection
        operation = st.selectbox(
            "Select Batch Operation",
            ["Resize", "Convert Format", "Apply Filter", "Compress"]
        )
        
        if operation == "Resize":
            col1, col2, col3 = st.columns(3)
            with col1:
                batch_width = st.number_input("Target Width", min_value=1, value=800)
            with col2:
                batch_height = st.number_input("Target Height", min_value=1, value=600)
            with col3:
                batch_maintain_aspect = st.checkbox("Maintain aspect ratio", value=True, key="batch_aspect")
        
        elif operation == "Convert Format":
            target_format = st.selectbox("Target Format", ["PNG", "JPEG", "WEBP"])
        
        elif operation == "Apply Filter":
            batch_filter = st.selectbox("Filter", ["Grayscale", "Sepia", "Blur", "Vintage", "Cool", "Warm"])
        
        elif operation == "Compress":
            quality = st.slider("JPEG Quality", min_value=10, max_value=100, value=85)
        
        if st.button("Process Batch"):
            processed_files = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    # Update progress
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {uploaded_file.name}...")
                    
                    # Load image
                    image = Image.open(uploaded_file)
                    
                    # Apply operation
                    if operation == "Resize":
                        if batch_maintain_aspect:
                            image.thumbnail((batch_width, batch_height), Image.Resampling.LANCZOS)
                        else:
                            image = image.resize((batch_width, batch_height), Image.Resampling.LANCZOS)
                    
                    elif operation == "Convert Format":
                        if target_format == "JPEG" and image.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', image.size, (255, 255, 255))
                            if image.mode in ('RGBA', 'LA'):
                                background.paste(image, mask=image.split()[-1])
                            else:
                                background.paste(image)
                            image = background
                    
                    elif operation == "Apply Filter":
                        if batch_filter == "Grayscale":
                            image = image.convert('L').convert('RGB')
                        elif batch_filter == "Sepia":
                            image = apply_sepia(image)
                        elif batch_filter == "Blur":
                            image = image.filter(ImageFilter.BLUR)
                        elif batch_filter == "Vintage":
                            image = apply_vintage(image)
                        elif batch_filter == "Cool":
                            image = apply_cool_filter(image)
                        elif batch_filter == "Warm":
                            image = apply_warm_filter(image)
                    
                    elif operation == "Compress":
                        if image.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', image.size, (255, 255, 255))
                            if image.mode in ('RGBA', 'LA'):
                                background.paste(image, mask=image.split()[-1])
                            else:
                                background.paste(image)
                            image = background
                    
                    # Save to bytes
                    output_format = target_format if operation == "Convert Format" else "PNG"
                    if operation == "Compress":
                        output_format = "JPEG"
                    
                    img_bytes = io.BytesIO()
                    save_kwargs = {}
                    if output_format == "JPEG":
                        save_kwargs['quality'] = quality if operation == "Compress" else 95
                        save_kwargs['optimize'] = True
                    
                    image.save(img_bytes, format=output_format, **save_kwargs)
                    img_bytes.seek(0)
                    
                    # Store processed file
                    filename = Path(uploaded_file.name).stem
                    extension = output_format.lower()
                    if extension == "jpeg":
                        extension = "jpg"
                    
                    processed_files.append({
                        'name': f"{filename}_processed.{extension}",
                        'data': img_bytes.getvalue(),
                        'format': output_format
                    })
                    
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            status_text.text("Processing complete!")
            progress_bar.progress(1.0)
            
            if processed_files:
                st.success(f"Successfully processed {len(processed_files)} images!")
                
                # Create ZIP file for download
                zip_bytes = io.BytesIO()
                with zipfile.ZipFile(zip_bytes, 'w') as zip_file:
                    for file_info in processed_files:
                        zip_file.writestr(file_info['name'], file_info['data'])
                
                zip_bytes.seek(0)
                
                st.download_button(
                    label="📥 Download All Processed Images (ZIP)",
                    data=zip_bytes.getvalue(),
                    file_name="processed_images.zip",
                    mime="application/zip"
                )

elif tool == "🔍 Image Inspector":
    st.header("🔍 Image Inspector")
    
    uploaded_file = st.file_uploader(
        "Choose an image file for inspection",
        type=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp', 'heic', 'heif']
    )
    
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            
            # Display image
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Basic information
            st.subheader("📊 Basic Information")
            info = get_image_info(image)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Filename:** {uploaded_file.name}")
                st.write(f"**Format:** {info['format']}")
                st.write(f"**Mode:** {info['mode']}")
                st.write(f"**File Size:** {uploaded_file.size:,} bytes")
            
            with col2:
                st.write(f"**Dimensions:** {info['width']} × {info['height']}")
                st.write(f"**Aspect Ratio:** {info['aspect_ratio']}")
                st.write(f"**Transparency:** {'Yes' if info['has_transparency'] else 'No'}")
            
            # Color analysis
            st.subheader("🎨 Color Analysis")
            if st.button("Analyze Colors"):
                palette = extract_color_palette(image)
                
                st.write("**Most Common Colors:**")
                for i, color_info in enumerate(palette):
                    color = color_info['color']
                    percentage = color_info['percentage']
                    
                    # Create color swatch
                    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    st.markdown(
                        f"<div style='display: inline-block; width: 20px; height: 20px; "
                        f"background-color: {color_hex}; border: 1px solid #ccc; margin-right: 10px;'></div>"
                        f"RGB{color} - {percentage:.2f}%",
                        unsafe_allow_html=True
                    )
            
            # EXIF data
            st.subheader("📷 EXIF Data")
            if st.button("Extract EXIF Data"):
                try:
                    exif_data = {}
                    if hasattr(image, '_getexif') and image._getexif() is not None:
                        exif = image._getexif()
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag == "GPSInfo":
                                gps_data = {}
                                for gps_tag_id, gps_value in value.items():
                                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                    gps_data[gps_tag] = str(gps_value)
                                exif_data[tag] = gps_data
                            else:
                                exif_data[tag] = str(value)
                    
                    if exif_data:
                        st.json(exif_data)
                    else:
                        st.info("No EXIF data found in this image.")
                        
                except Exception as e:
                    st.error(f"Error extracting EXIF data: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")

elif tool == "📱 Base64 Converter":
    st.header("📱 Base64 Converter")
    
    tab1, tab2 = st.tabs(["🖼️ Image to Base64", "📝 Base64 to Image"])
    
    with tab1:
        st.subheader("Convert Image to Base64")
        
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'],
            key="base64_upload"
        )
        
        if uploaded_file is not None:
            try:
                image = Image.open(uploaded_file)
                
                # Convert to RGB if needed
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode in ('RGBA', 'LA'):
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image)
                    image = background
                
                # Convert to base64
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='JPEG', quality=95)
                img_bytes = img_bytes.getvalue()
                
                base64_string = base64.b64encode(img_bytes).decode('utf-8')
                data_uri = f"data:image/jpeg;base64,{base64_string}"
                
                st.image(image, caption="Original Image", width=300)
                
                st.subheader("Base64 Output")
                st.text_area("Base64 String", value=data_uri, height=200, help="Copy this string to use elsewhere")
                
                # Download option
                st.download_button(
                    label="📥 Download Base64 as Text File",
                    data=data_uri,
                    file_name="image_base64.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error converting image: {str(e)}")
    
    with tab2:
        st.subheader("Convert Base64 to Image")
        
        # Input methods
        input_method = st.radio("Input Method", ["Paste Base64 String", "Upload Text File"])
        
        base64_string = ""
        
        if input_method == "Paste Base64 String":
            base64_string = st.text_area(
                "Paste Base64 String",
                placeholder="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                height=200
            )
        
        else:
            uploaded_text_file = st.file_uploader(
                "Upload text file containing Base64",
                type=['txt'],
                key="base64_text_upload"
            )
            
            if uploaded_text_file is not None:
                base64_string = uploaded_text_file.read().decode('utf-8').strip()
        
        if base64_string and st.button("Convert to Image"):
            try:
                # Clean base64 string
                if base64_string.startswith('data:image'):
                    base64_string = base64_string.split(',', 1)[1]
                
                base64_string = ''.join(base64_string.split())
                
                # Decode base64
                img_data = base64.b64decode(base64_string)
                
                # Create image
                image = Image.open(io.BytesIO(img_data))
                
                st.success("Base64 successfully converted to image!")
                st.image(image, caption="Converted Image", use_column_width=True)
                
                # Download options
                format_choice = st.selectbox("Download Format", ["PNG", "JPEG", "WEBP"], key="base64_format")
                
                if format_choice == "JPEG" and image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode in ('RGBA', 'LA'):
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image)
                    image = background
                
                img_bytes = pil_to_bytes(image, format_choice)
                
                st.download_button(
                    label=f"📥 Download as {format_choice}",
                    data=img_bytes,
                    file_name=f"converted_image.{format_choice.lower()}",
                    mime=f"image/{format_choice.lower()}"
                )
                
            except Exception as e:
                st.error(f"Error converting Base64: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🖼️ Enhanced Image Manipulator Pro | Built with Streamlit</p>
    <p>Features: Image editing, batch processing, format conversion, filters, and more!</p>
</div>
""", unsafe_allow_html=True)