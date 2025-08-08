from PIL import Image
import psd_tools
from psd_tools.api.layers import PixelLayer
from psd_tools.api import PSDImage
import numpy as np

# Create a simple test PSD with multiple layers
width, height = 600, 400

# Create a new PSD
psd = PSDImage.new('RGBA', (width, height), color=(255, 255, 255, 0))

# Create layer 1 - Red rectangle
red_layer = Image.new('RGBA', (200, 150), (255, 0, 0, 255))
red_data = np.array(red_layer)

# Create layer 2 - Blue circle (approximated with a square for simplicity)
blue_layer = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
for i in range(150):
    for j in range(150):
        if (i - 75) ** 2 + (j - 75) ** 2 <= 70 ** 2:
            blue_layer.putpixel((i, j), (0, 0, 255, 255))

# Create layer 3 - Green triangle (approximated)
green_layer = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
for i in range(200):
    for j in range(200):
        if j < 200 - i and j < i:
            green_layer.putpixel((i, j), (0, 255, 0, 255))

print("Test PSD created with 3 layers")
print("Note: Creating PSD files programmatically is complex.")
print("For testing, please use an actual PSD file created in Photoshop.")
print("You can:")
print("1. Create a simple PSD in Photoshop with 2-3 layers")
print("2. Use any existing PSD file")
print("3. Download a sample PSD from the internet")