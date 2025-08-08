#!/usr/bin/env python3
"""
Create a real test PSD file with multiple layers for testing
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create three different layers
width, height = 800, 600

# Layer 1: Background with gradient
background = Image.new('RGBA', (width, height), (255, 255, 255, 255))
draw = ImageDraw.Draw(background)
for i in range(height):
    color_value = int(255 * (i / height))
    draw.rectangle([(0, i), (width, i+1)], fill=(color_value, color_value, 255, 255))
background.save('layer_background.png')

# Layer 2: Red circle
circle_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(circle_layer)
draw.ellipse([(100, 100), (300, 300)], fill=(255, 0, 0, 200))
circle_layer.save('layer_circle.png')

# Layer 3: Green rectangle
rect_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(rect_layer)
draw.rectangle([(400, 200), (700, 400)], fill=(0, 255, 0, 180))
rect_layer.save('layer_rectangle.png')

# Layer 4: Blue triangle
triangle_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(triangle_layer)
draw.polygon([(200, 400), (400, 550), (300, 550)], fill=(0, 0, 255, 200))
triangle_layer.save('layer_triangle.png')

# Composite all layers into one image for preview
composite = Image.alpha_composite(background, circle_layer)
composite = Image.alpha_composite(composite, rect_layer)
composite = Image.alpha_composite(composite, triangle_layer)
composite.save('test_composite.png')

print("Created individual layer images:")
print("- layer_background.png")
print("- layer_circle.png")
print("- layer_rectangle.png")
print("- layer_triangle.png")
print("- test_composite.png (preview)")
print("\nNote: These are PNG files. For actual PSD testing:")
print("1. Use Photoshop to create a real PSD file")
print("2. Or use GIMP to create an XCF file and export as PSD")
print("3. Or use the test_composite.png as a single-layer test")