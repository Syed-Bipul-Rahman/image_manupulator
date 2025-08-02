import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import base64
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFont, ImageDraw
from PIL.ExifTags import TAGS, GPSTAGS
import io
import os
import json
import threading
from pathlib import Path
from datetime import datetime
import pillow_heif
import cv2
import numpy as np
from collections import Counter

pillow_heif.register_heif_opener()

class EnhancedImageManipulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Image Manipulator Pro")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        self.current_image_path = None
        self.processed_image = None
        self.preview_image = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_panel = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # File selection
        file_frame = ttk.Frame(left_panel)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="📁 Select Image", 
                  command=self.select_image).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="📁 Select Multiple Images", 
                  command=self.select_multiple_images).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="💾 Save Current Image", 
                  command=self.save_image).pack(fill=tk.X, pady=2)
        
        # Tabs for different operations
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Basic Operations Tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")
        self.setup_basic_tab(basic_tab)
        
        # Enhancement Tab
        enhance_tab = ttk.Frame(notebook)
        notebook.add(enhance_tab, text="Enhance")
        self.setup_enhance_tab(enhance_tab)
        
        # Filters Tab
        filters_tab = ttk.Frame(notebook)
        notebook.add(filters_tab, text="Filters")
        self.setup_filters_tab(filters_tab)
        
        # Advanced Tab
        advanced_tab = ttk.Frame(notebook)
        notebook.add(advanced_tab, text="Advanced")
        self.setup_advanced_tab(advanced_tab)
        
        # Batch Tab
        batch_tab = ttk.Frame(notebook)
        notebook.add(batch_tab, text="Batch")
        self.setup_batch_tab(batch_tab)
        
        # Right panel - Preview and Info
        right_panel = ttk.LabelFrame(main_frame, text="Preview & Info", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Image preview
        self.preview_frame = ttk.Frame(right_panel)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_frame, text="No image selected", 
                                      font=("Arial", 14), background="white")
        self.preview_label.pack(expand=True)
        
        # Info panel
        info_frame = ttk.LabelFrame(right_panel, text="Image Information")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.info_text.pack(fill=tk.X, expand=True)
        
    def setup_basic_tab(self, parent):
        # Resize section
        resize_frame = ttk.LabelFrame(parent, text="Resize")
        resize_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(resize_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value="800")
        ttk.Entry(resize_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(resize_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.StringVar(value="600")
        ttk.Entry(resize_frame, textvariable=self.height_var, width=10).grid(row=1, column=1, padx=5)
        
        self.maintain_aspect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(resize_frame, text="Maintain aspect ratio", 
                       variable=self.maintain_aspect_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Button(resize_frame, text="Resize", 
                  command=self.resize_image).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Rotate section
        rotate_frame = ttk.LabelFrame(parent, text="Rotate")
        rotate_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rotate_frame, text="Angle:").grid(row=0, column=0, sticky=tk.W)
        self.angle_var = tk.StringVar(value="90")
        ttk.Entry(rotate_frame, textvariable=self.angle_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(rotate_frame, text="Rotate", 
                  command=self.rotate_image).grid(row=1, column=0, columnspan=2, pady=5)
        
        # Format conversion
        format_frame = ttk.LabelFrame(parent, text="Convert Format")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.format_var = tk.StringVar(value="JPEG")
        formats = ["JPEG", "PNG", "WEBP", "BMP", "GIF"]
        ttk.Combobox(format_frame, textvariable=self.format_var, 
                    values=formats, state="readonly").pack(fill=tk.X, pady=5)
        
        ttk.Button(format_frame, text="Convert", 
                  command=self.convert_format).pack(fill=tk.X, pady=5)
        
    def setup_enhance_tab(self, parent):
        # Brightness
        brightness_frame = ttk.LabelFrame(parent, text="Brightness")
        brightness_frame.pack(fill=tk.X, pady=5)
        
        self.brightness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(brightness_frame, from_=0.1, to=3.0, variable=self.brightness_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(brightness_frame, textvariable=self.brightness_var).pack()
        ttk.Button(brightness_frame, text="Apply Brightness", 
                  command=self.apply_brightness).pack(pady=5)
        
        # Contrast
        contrast_frame = ttk.LabelFrame(parent, text="Contrast")
        contrast_frame.pack(fill=tk.X, pady=5)
        
        self.contrast_var = tk.DoubleVar(value=1.0)
        ttk.Scale(contrast_frame, from_=0.1, to=3.0, variable=self.contrast_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(contrast_frame, textvariable=self.contrast_var).pack()
        ttk.Button(contrast_frame, text="Apply Contrast", 
                  command=self.apply_contrast).pack(pady=5)
        
        # Saturation
        saturation_frame = ttk.LabelFrame(parent, text="Saturation")
        saturation_frame.pack(fill=tk.X, pady=5)
        
        self.saturation_var = tk.DoubleVar(value=1.0)
        ttk.Scale(saturation_frame, from_=0.0, to=3.0, variable=self.saturation_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(saturation_frame, textvariable=self.saturation_var).pack()
        ttk.Button(saturation_frame, text="Apply Saturation", 
                  command=self.apply_saturation).pack(pady=5)
        
        # Sharpness
        sharpness_frame = ttk.LabelFrame(parent, text="Sharpness")
        sharpness_frame.pack(fill=tk.X, pady=5)
        
        self.sharpness_var = tk.DoubleVar(value=1.0)
        ttk.Scale(sharpness_frame, from_=0.0, to=3.0, variable=self.sharpness_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(sharpness_frame, textvariable=self.sharpness_var).pack()
        ttk.Button(sharpness_frame, text="Apply Sharpness", 
                  command=self.apply_sharpness).pack(pady=5)
        
    def setup_filters_tab(self, parent):
        filter_buttons = [
            ("Grayscale", self.apply_grayscale),
            ("Sepia", self.apply_sepia),
            ("Blur", self.apply_blur),
            ("Gaussian Blur", self.apply_gaussian_blur),
            ("Edge Enhance", self.apply_edge_enhance),
            ("Emboss", self.apply_emboss),
            ("Find Edges", self.apply_find_edges),
            ("Vintage", self.apply_vintage),
            ("Cool", self.apply_cool_filter),
            ("Warm", self.apply_warm_filter)
        ]
        
        for i, (text, command) in enumerate(filter_buttons):
            ttk.Button(parent, text=text, command=command).grid(
                row=i//2, column=i%2, sticky=tk.EW, padx=2, pady=2)
        
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        
    def setup_advanced_tab(self, parent):
        # Cropping
        crop_frame = ttk.LabelFrame(parent, text="Crop")
        crop_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(crop_frame, text="Aspect Ratio:").pack(anchor=tk.W)
        self.crop_ratio_var = tk.StringVar(value="Original")
        ratios = ["Original", "1:1", "4:3", "16:9", "3:2", "Custom"]
        ttk.Combobox(crop_frame, textvariable=self.crop_ratio_var, 
                    values=ratios, state="readonly").pack(fill=tk.X, pady=2)
        
        ttk.Button(crop_frame, text="Crop Center", 
                  command=self.crop_center).pack(fill=tk.X, pady=2)
        
        # Watermark
        watermark_frame = ttk.LabelFrame(parent, text="Watermark")
        watermark_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(watermark_frame, text="Text:").pack(anchor=tk.W)
        self.watermark_text_var = tk.StringVar(value="Watermark")
        ttk.Entry(watermark_frame, textvariable=self.watermark_text_var).pack(fill=tk.X, pady=2)
        
        ttk.Label(watermark_frame, text="Position:").pack(anchor=tk.W)
        self.watermark_pos_var = tk.StringVar(value="Bottom Right")
        positions = ["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"]
        ttk.Combobox(watermark_frame, textvariable=self.watermark_pos_var, 
                    values=positions, state="readonly").pack(fill=tk.X, pady=2)
        
        ttk.Button(watermark_frame, text="Add Watermark", 
                  command=self.add_watermark).pack(fill=tk.X, pady=2)
        
        # Color analysis
        analysis_frame = ttk.LabelFrame(parent, text="Analysis")
        analysis_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(analysis_frame, text="Extract Color Palette", 
                  command=self.extract_color_palette).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="Show Histogram", 
                  command=self.show_histogram).pack(fill=tk.X, pady=2)
        ttk.Button(analysis_frame, text="Detect Faces & Blur", 
                  command=self.detect_and_blur_faces).pack(fill=tk.X, pady=2)
        
    def setup_batch_tab(self, parent):
        self.batch_files = []
        
        ttk.Label(parent, text="Batch Processing").pack(pady=5)
        
        batch_buttons_frame = ttk.Frame(parent)
        batch_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(batch_buttons_frame, text="Add Files", 
                  command=self.add_batch_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(batch_buttons_frame, text="Clear List", 
                  command=self.clear_batch_files).pack(side=tk.LEFT, padx=2)
        
        # Batch operations
        operations_frame = ttk.LabelFrame(parent, text="Batch Operations")
        operations_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(operations_frame, text="Batch Resize", 
                  command=self.batch_resize).pack(fill=tk.X, pady=2)
        ttk.Button(operations_frame, text="Batch Convert Format", 
                  command=self.batch_convert_format).pack(fill=tk.X, pady=2)
        ttk.Button(operations_frame, text="Batch Compress", 
                  command=self.batch_compress).pack(fill=tk.X, pady=2)
        ttk.Button(operations_frame, text="Batch Apply Filter", 
                  command=self.batch_apply_filter).pack(fill=tk.X, pady=2)
        
        # Files list
        self.batch_listbox = tk.Listbox(parent, height=8)
        self.batch_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.heic *.heif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.load_and_display_image(file_path)
            self.update_image_info()
            
    def select_multiple_images(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Multiple Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.heic *.heif"),
                ("All files", "*.*")
            ]
        )
        
        if file_paths:
            self.batch_files.extend(file_paths)
            self.update_batch_list()
            messagebox.showinfo("Success", f"Added {len(file_paths)} files to batch list")
            
    def load_and_display_image(self, file_path):
        try:
            with Image.open(file_path) as img:
                self.processed_image = img.copy()
                self.display_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            
    def display_preview(self):
        if self.processed_image:
            # Calculate display size
            display_size = (400, 300)
            img_copy = self.processed_image.copy()
            img_copy.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for display
            import tkinter.image_names
            photo = tk.PhotoImage(data=self.pil_to_base64(img_copy))
            
            self.preview_label.configure(image=photo, text="")
            self.preview_label.image = photo
            
    def pil_to_base64(self, img):
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        return img_str
        
    def update_image_info(self):
        if not self.current_image_path:
            return
            
        try:
            with Image.open(self.current_image_path) as img:
                file_size = Path(self.current_image_path).stat().st_size
                
                info = f"File: {Path(self.current_image_path).name}\n"
                info += f"Path: {self.current_image_path}\n"
                info += f"Size: {file_size / 1024 / 1024:.2f} MB ({file_size:,} bytes)\n"
                info += f"Format: {img.format}\n"
                info += f"Mode: {img.mode}\n"
                info += f"Dimensions: {img.width}x{img.height}\n"
                info += f"Aspect Ratio: {img.width / img.height:.2f}\n"
                info += f"Transparency: {'Yes' if img.mode in ('RGBA', 'LA') else 'No'}\n"
                
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, info)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get image info: {str(e)}")
            
    def save_image(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No processed image to save")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".jpg",
            filetypes=[
                ("JPEG files", "*.jpg"),
                ("PNG files", "*.png"),
                ("WEBP files", "*.webp"),
                ("BMP files", "*.bmp"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Handle format conversion for saving
                save_image = self.processed_image.copy()
                format_ext = Path(file_path).suffix.lower()
                
                if format_ext in ['.jpg', '.jpeg']:
                    if save_image.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', save_image.size, (255, 255, 255))
                        if save_image.mode in ('RGBA', 'LA'):
                            background.paste(save_image, mask=save_image.split()[-1])
                        else:
                            background.paste(save_image)
                        save_image = background
                    save_image.save(file_path, quality=95, optimize=True)
                else:
                    save_image.save(file_path)
                    
                messagebox.showinfo("Success", f"Image saved to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
                
    # Basic operations
    def resize_image(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            if self.maintain_aspect_var.get():
                self.processed_image.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                self.processed_image = self.processed_image.resize((width, height), Image.Resampling.LANCZOS)
                
            self.display_preview()
            messagebox.showinfo("Success", "Image resized successfully")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid width and height values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to resize image: {str(e)}")
            
    def rotate_image(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            angle = float(self.angle_var.get())
            self.processed_image = self.processed_image.rotate(angle, expand=True, fillcolor='white')
            self.display_preview()
            messagebox.showinfo("Success", f"Image rotated by {angle} degrees")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid angle value")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rotate image: {str(e)}")
            
    def convert_format(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        format_name = self.format_var.get()
        messagebox.showinfo("Info", f"Format will be changed to {format_name} when you save the image")
        
    # Enhancement operations
    def apply_brightness(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            enhancer = ImageEnhance.Brightness(self.processed_image)
            self.processed_image = enhancer.enhance(self.brightness_var.get())
            self.display_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust brightness: {str(e)}")
            
    def apply_contrast(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            enhancer = ImageEnhance.Contrast(self.processed_image)
            self.processed_image = enhancer.enhance(self.contrast_var.get())
            self.display_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust contrast: {str(e)}")
            
    def apply_saturation(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            enhancer = ImageEnhance.Color(self.processed_image)
            self.processed_image = enhancer.enhance(self.saturation_var.get())
            self.display_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust saturation: {str(e)}")
            
    def apply_sharpness(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            enhancer = ImageEnhance.Sharpness(self.processed_image)
            self.processed_image = enhancer.enhance(self.sharpness_var.get())
            self.display_preview()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust sharpness: {str(e)}")
            
    # Filter operations
    def apply_grayscale(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.convert('L').convert('RGB')
        self.display_preview()
        
    def apply_sepia(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        # Convert to numpy array for sepia effect
        img_array = np.array(self.processed_image)
        sepia_filter = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        sepia_img = img_array.dot(sepia_filter.T)
        sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
        self.processed_image = Image.fromarray(sepia_img)
        self.display_preview()
        
    def apply_blur(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.filter(ImageFilter.BLUR)
        self.display_preview()
        
    def apply_gaussian_blur(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.filter(ImageFilter.GaussianBlur(radius=2))
        self.display_preview()
        
    def apply_edge_enhance(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.filter(ImageFilter.EDGE_ENHANCE)
        self.display_preview()
        
    def apply_emboss(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.filter(ImageFilter.EMBOSS)
        self.display_preview()
        
    def apply_find_edges(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        self.processed_image = self.processed_image.filter(ImageFilter.FIND_EDGES)
        self.display_preview()
        
    def apply_vintage(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        # Apply vintage effect (sepia + vignette + noise)
        self.apply_sepia()
        
        # Add slight blur for vintage feel
        self.processed_image = self.processed_image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Reduce contrast slightly
        enhancer = ImageEnhance.Contrast(self.processed_image)
        self.processed_image = enhancer.enhance(0.9)
        
        self.display_preview()
        
    def apply_cool_filter(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        # Cool filter (boost blues, reduce reds)
        img_array = np.array(self.processed_image).astype(float)
        img_array[:, :, 0] *= 0.8  # Reduce red
        img_array[:, :, 2] *= 1.2  # Boost blue
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        self.processed_image = Image.fromarray(img_array)
        self.display_preview()
        
    def apply_warm_filter(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        # Warm filter (boost reds/yellows, reduce blues)
        img_array = np.array(self.processed_image).astype(float)
        img_array[:, :, 0] *= 1.2  # Boost red
        img_array[:, :, 1] *= 1.1  # Boost green slightly
        img_array[:, :, 2] *= 0.8  # Reduce blue
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        self.processed_image = Image.fromarray(img_array)
        self.display_preview()
        
    # Advanced operations
    def crop_center(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        ratio = self.crop_ratio_var.get()
        width, height = self.processed_image.size
        
        if ratio == "Original":
            return
        elif ratio == "1:1":
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
            return
            
        # Center crop
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        
        self.processed_image = self.processed_image.crop((left, top, right, bottom))
        self.display_preview()
        messagebox.showinfo("Success", f"Image cropped to {ratio} aspect ratio")
        
    def add_watermark(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Create a copy for watermarking
            watermarked = self.processed_image.copy()
            draw = ImageDraw.Draw(watermarked)
            
            text = self.watermark_text_var.get()
            position = self.watermark_pos_var.get()
            
            # Try to load a font, fallback to default if not available
            try:
                font_size = max(20, min(watermarked.width, watermarked.height) // 20)
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
            overlay = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], 
                                 fill=(0, 0, 0, 128))
            overlay_draw.text((x, y), text, font=font, fill=(255, 255, 255, 200))
            
            # Composite the overlay
            if watermarked.mode != 'RGBA':
                watermarked = watermarked.convert('RGBA')
            watermarked = Image.alpha_composite(watermarked, overlay)
            
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
                
            self.processed_image = watermarked
            self.display_preview()
            messagebox.showinfo("Success", "Watermark added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add watermark: {str(e)}")
            
    def extract_color_palette(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Convert image to RGB and get pixels
            rgb_img = self.processed_image.convert('RGB')
            pixels = list(rgb_img.getdata())
            
            # Get most common colors
            color_counts = Counter(pixels)
            most_common = color_counts.most_common(10)
            
            # Create palette display
            palette_window = tk.Toplevel(self.root)
            palette_window.title("Color Palette")
            palette_window.geometry("600x400")
            
            info_text = "Top 10 Most Common Colors:\n\n"
            for i, (color, count) in enumerate(most_common):
                percentage = (count / len(pixels)) * 100
                info_text += f"{i+1}. RGB{color} - {percentage:.2f}% ({count} pixels)\n"
            
            text_widget = scrolledtext.ScrolledText(palette_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, info_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract color palette: {str(e)}")
            
    def show_histogram(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            import matplotlib.pyplot as plt
            
            # Calculate histogram
            rgb_img = self.processed_image.convert('RGB')
            r, g, b = rgb_img.split()
            
            plt.figure(figsize=(10, 6))
            plt.hist(np.array(r).flatten(), bins=256, alpha=0.7, color='red', label='Red')
            plt.hist(np.array(g).flatten(), bins=256, alpha=0.7, color='green', label='Green')
            plt.hist(np.array(b).flatten(), bins=256, alpha=0.7, color='blue', label='Blue')
            
            plt.xlabel('Pixel Value')
            plt.ylabel('Frequency')
            plt.title('RGB Histogram')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()
            
        except ImportError:
            messagebox.showerror("Error", "Matplotlib is required for histogram display. Install with: pip install matplotlib")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show histogram: {str(e)}")
            
    def detect_and_blur_faces(self):
        if not self.processed_image:
            messagebox.showwarning("Warning", "No image loaded")
            return
            
        try:
            # Convert PIL image to OpenCV format
            cv_img = cv2.cvtColor(np.array(self.processed_image), cv2.COLOR_RGB2BGR)
            
            # Load face cascade classifier
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                messagebox.showinfo("Info", "No faces detected in the image")
                return
            
            # Blur detected faces
            for (x, y, w, h) in faces:
                # Extract face region
                face_region = cv_img[y:y+h, x:x+w]
                
                # Apply Gaussian blur
                blurred_face = cv2.GaussianBlur(face_region, (99, 99), 30)
                
                # Replace face region with blurred version
                cv_img[y:y+h, x:x+w] = blurred_face
            
            # Convert back to PIL
            self.processed_image = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            self.display_preview()
            
            messagebox.showinfo("Success", f"Detected and blurred {len(faces)} face(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to detect faces: {str(e)}")
            
    # Batch operations
    def add_batch_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Add Files to Batch",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.heic *.heif"),
                ("All files", "*.*")
            ]
        )
        
        if file_paths:
            self.batch_files.extend(file_paths)
            self.update_batch_list()
            
    def clear_batch_files(self):
        self.batch_files.clear()
        self.update_batch_list()
        
    def update_batch_list(self):
        self.batch_listbox.delete(0, tk.END)
        for file_path in self.batch_files:
            self.batch_listbox.insert(tk.END, Path(file_path).name)
            
    def batch_resize(self):
        if not self.batch_files:
            messagebox.showwarning("Warning", "No files in batch list")
            return
            
        # Get target directory
        target_dir = filedialog.askdirectory(title="Select Output Directory")
        if not target_dir:
            return
            
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            maintain_aspect = self.maintain_aspect_var.get()
            
            progress_window = self.create_progress_window("Batch Resize", len(self.batch_files))
            
            for i, file_path in enumerate(self.batch_files):
                try:
                    with Image.open(file_path) as img:
                        if maintain_aspect:
                            img.thumbnail((width, height), Image.Resampling.LANCZOS)
                        else:
                            img = img.resize((width, height), Image.Resampling.LANCZOS)
                        
                        output_path = Path(target_dir) / f"resized_{Path(file_path).name}"
                        
                        # Handle format conversion for saving
                        if img.mode in ('RGBA', 'LA', 'P') and output_path.suffix.lower() in ['.jpg', '.jpeg']:
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode in ('RGBA', 'LA'):
                                background.paste(img, mask=img.split()[-1])
                            else:
                                background.paste(img)
                            img = background
                        
                        img.save(output_path, quality=95 if output_path.suffix.lower() in ['.jpg', '.jpeg'] else None)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
                
                self.update_progress(progress_window, i + 1)
                
            progress_window.destroy()
            messagebox.showinfo("Success", f"Batch resize completed. Files saved to {target_dir}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid width and height values")
        except Exception as e:
            messagebox.showerror("Error", f"Batch resize failed: {str(e)}")
            
    def batch_convert_format(self):
        if not self.batch_files:
            messagebox.showwarning("Warning", "No files in batch list")
            return
            
        target_dir = filedialog.askdirectory(title="Select Output Directory")
        if not target_dir:
            return
            
        target_format = self.format_var.get().lower()
        if target_format == 'jpeg':
            target_format = 'jpg'
            
        progress_window = self.create_progress_window("Batch Convert", len(self.batch_files))
        
        for i, file_path in enumerate(self.batch_files):
            try:
                with Image.open(file_path) as img:
                    output_path = Path(target_dir) / f"{Path(file_path).stem}.{target_format}"
                    
                    # Handle format conversion
                    if target_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    
                    save_kwargs = {}
                    if target_format in ['jpg', 'jpeg']:
                        save_kwargs['quality'] = 95
                        save_kwargs['optimize'] = True
                    
                    img.save(output_path, **save_kwargs)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
            
            self.update_progress(progress_window, i + 1)
            
        progress_window.destroy()
        messagebox.showinfo("Success", f"Batch conversion completed. Files saved to {target_dir}")
        
    def batch_compress(self):
        if not self.batch_files:
            messagebox.showwarning("Warning", "No files in batch list")
            return
            
        target_dir = filedialog.askdirectory(title="Select Output Directory")
        if not target_dir:
            return
            
        quality = 85  # Default compression quality
        
        progress_window = self.create_progress_window("Batch Compress", len(self.batch_files))
        
        for i, file_path in enumerate(self.batch_files):
            try:
                with Image.open(file_path) as img:
                    output_path = Path(target_dir) / f"compressed_{Path(file_path).name}"
                    
                    # Convert to RGB if needed for JPEG compression
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    
                    img.save(output_path, quality=quality, optimize=True)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
            
            self.update_progress(progress_window, i + 1)
            
        progress_window.destroy()
        messagebox.showinfo("Success", f"Batch compression completed. Files saved to {target_dir}")
        
    def batch_apply_filter(self):
        if not self.batch_files:
            messagebox.showwarning("Warning", "No files in batch list")
            return
            
        # Create filter selection dialog
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Select Filter")
        filter_window.geometry("300x400")
        
        ttk.Label(filter_window, text="Select filter to apply:").pack(pady=10)
        
        filter_var = tk.StringVar(value="Grayscale")
        filters = ["Grayscale", "Sepia", "Blur", "Gaussian Blur", "Edge Enhance", 
                  "Emboss", "Find Edges", "Vintage", "Cool", "Warm"]
        
        for filter_name in filters:
            ttk.Radiobutton(filter_window, text=filter_name, variable=filter_var, 
                           value=filter_name).pack(anchor=tk.W, padx=20)
        
        def apply_batch_filter():
            target_dir = filedialog.askdirectory(title="Select Output Directory")
            if not target_dir:
                return
                
            filter_window.destroy()
            
            progress_window = self.create_progress_window("Batch Filter", len(self.batch_files))
            
            for i, file_path in enumerate(self.batch_files):
                try:
                    with Image.open(file_path) as img:
                        # Apply selected filter
                        filtered_img = self.apply_filter_to_image(img.copy(), filter_var.get())
                        
                        output_path = Path(target_dir) / f"filtered_{Path(file_path).name}"
                        
                        # Save with appropriate format handling
                        if filtered_img.mode in ('RGBA', 'LA', 'P') and output_path.suffix.lower() in ['.jpg', '.jpeg']:
                            background = Image.new('RGB', filtered_img.size, (255, 255, 255))
                            if filtered_img.mode in ('RGBA', 'LA'):
                                background.paste(filtered_img, mask=filtered_img.split()[-1])
                            else:
                                background.paste(filtered_img)
                            filtered_img = background
                        
                        filtered_img.save(output_path, quality=95 if output_path.suffix.lower() in ['.jpg', '.jpeg'] else None)
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
                
                self.update_progress(progress_window, i + 1)
                
            progress_window.destroy()
            messagebox.showinfo("Success", f"Batch filter applied. Files saved to {target_dir}")
        
        ttk.Button(filter_window, text="Apply Filter", command=apply_batch_filter).pack(pady=20)
        
    def apply_filter_to_image(self, img, filter_name):
        if filter_name == "Grayscale":
            return img.convert('L').convert('RGB')
        elif filter_name == "Sepia":
            img_array = np.array(img)
            sepia_filter = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            sepia_img = img_array.dot(sepia_filter.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            return Image.fromarray(sepia_img)
        elif filter_name == "Blur":
            return img.filter(ImageFilter.BLUR)
        elif filter_name == "Gaussian Blur":
            return img.filter(ImageFilter.GaussianBlur(radius=2))
        elif filter_name == "Edge Enhance":
            return img.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_name == "Emboss":
            return img.filter(ImageFilter.EMBOSS)
        elif filter_name == "Find Edges":
            return img.filter(ImageFilter.FIND_EDGES)
        elif filter_name == "Vintage":
            # Apply sepia
            img_array = np.array(img)
            sepia_filter = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])
            sepia_img = img_array.dot(sepia_filter.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            vintage_img = Image.fromarray(sepia_img)
            
            # Add blur and reduce contrast
            vintage_img = vintage_img.filter(ImageFilter.GaussianBlur(radius=0.5))
            enhancer = ImageEnhance.Contrast(vintage_img)
            return enhancer.enhance(0.9)
        elif filter_name == "Cool":
            img_array = np.array(img).astype(float)
            img_array[:, :, 0] *= 0.8  # Reduce red
            img_array[:, :, 2] *= 1.2  # Boost blue
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            return Image.fromarray(img_array)
        elif filter_name == "Warm":
            img_array = np.array(img).astype(float)
            img_array[:, :, 0] *= 1.2  # Boost red
            img_array[:, :, 1] *= 1.1  # Boost green slightly
            img_array[:, :, 2] *= 0.8  # Reduce blue
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            return Image.fromarray(img_array)
        else:
            return img
            
    def create_progress_window(self, title, total):
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("400x100")
        progress_window.resizable(False, False)
        
        ttk.Label(progress_window, text=f"Processing {total} files...").pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=total)
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        progress_window.progress_var = progress_var
        progress_window.progress_bar = progress_bar
        
        return progress_window
        
    def update_progress(self, progress_window, current):
        if progress_window and progress_window.winfo_exists():
            progress_window.progress_var.set(current)
            progress_window.update()

def main():
    root = tk.Tk()
    app = EnhancedImageManipulator(root)
    root.mainloop()

if __name__ == "__main__":
    main()