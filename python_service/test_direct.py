#!/usr/bin/env python3
"""
Direct test of mesh generation without running the service
"""
import asyncio
from mesh_service import MeshService
from PIL import Image, ImageDraw
import json

async def test_mesh_generation():
    """Test mesh generation directly"""
    
    # Create test image
    img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill=(255, 255, 255, 255))
    img.save('test_image.png')
    print("Created test image")
    
    # Initialize service
    service = MeshService()
    
    # Test parameters
    params = {
        "detail_factor": 0.01,
        "alpha_threshold": 10,
        "concave_factor": 0.0,
        "internal_vertex_density": 0
    }
    
    try:
        # Read image data
        with open('test_image.png', 'rb') as f:
            image_data = f.read()
        
        print("\nGenerating mesh...")
        result = await service.generate_mesh_from_file(
            image_data=image_data,
            parameters=params
        )
        
        print("\nMesh generated successfully!")
        print(f"Vertices: {len(result['vertices'])}")
        print(f"Triangles: {len(result['triangles'])}")
        print(f"UVs: {len(result['uvs'])}")
        print(f"Bounds: {result['bounds']}")
        print(f"Metadata: {result['metadata']}")
        
        # Save result
        with open('mesh_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("\nSaved result to mesh_result.json")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mesh_generation())