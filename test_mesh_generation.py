#!/usr/bin/env python3
"""
Test script for mesh generation service
"""
import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_image.png"

def create_test_image():
    """Create a simple test image if it doesn't exist"""
    from PIL import Image, ImageDraw
    
    if not Path(TEST_IMAGE_PATH).exists():
        # Create a 200x200 image with a white circle on black background
        img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 150, 150], fill=(255, 255, 255, 255))
        img.save(TEST_IMAGE_PATH)
        print(f"Created test image: {TEST_IMAGE_PATH}")

def test_health_check():
    """Test if the service is running"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.json()}")
    assert response.status_code == 200

def test_mesh_generation_from_file():
    """Test mesh generation from uploaded file"""
    create_test_image()
    
    with open(TEST_IMAGE_PATH, 'rb') as f:
        files = {'file': f}
        data = {
            'detail_factor': 0.01,
            'alpha_threshold': 10
        }
        
        print("\nGenerating mesh from file...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/generate_mesh_from_file",
            files=files,
            data=data
        )
        
        elapsed = time.time() - start_time
        print(f"Generation took {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            mesh = result['mesh']
            print(f"\nMesh generated successfully!")
            print(f"Vertices: {len(mesh['vertices'])}")
            print(f"Triangles: {len(mesh['triangles'])}")
            print(f"Bounds: {mesh['bounds']}")
            print(f"Metadata: {mesh['metadata']}")
            
            # Verify data structure
            assert 'vertices' in mesh
            assert 'triangles' in mesh
            assert 'uvs' in mesh
            assert len(mesh['vertices']) > 0
            assert len(mesh['triangles']) > 0
            assert len(mesh['uvs']) == len(mesh['vertices'])
            
            print("\n✅ All tests passed!")
        else:
            print(f"Error: {response.status_code}")
            print(response.json())

def test_psd_extraction():
    """Test PSD layer extraction"""
    # This would require a test PSD file
    print("\nPSD extraction test - skipped (requires PSD file)")

if __name__ == "__main__":
    print("Testing SpineLift Python Service...")
    
    try:
        test_health_check()
        test_mesh_generation_from_file()
        # test_psd_extraction()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to Python service.")
        print("Make sure the service is running: python main.py")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise