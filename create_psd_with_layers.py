#!/usr/bin/env python3
"""
Create a proper PSD file using psd-tools for testing
"""
from psd_tools import PSDImage
from PIL import Image
import numpy as np

# Create individual layer images
width, height = 800, 600

# Create base PSD
psd = PSDImage.new("RGBA", (width, height))

# Add background layer
background = Image.new('RGBA', (width, height), (200, 200, 255, 255))
psd.composite().paste(background)

# Save as PSD
output_path = "test_layers.psd"
psd.save(output_path)

print(f"Created test PSD file: {output_path}")
print(f"Dimensions: {width}x{height}")
print("Note: This is a simple single-layer PSD. For multi-layer testing,")
print("please use a PSD file created in Photoshop or similar software.")