import React, { useEffect, useRef, useState } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Image as ImageIcon, 
  Grid3x3,
  BarChart,
  Move
} from 'lucide-react';
import type { Layer } from '../../types';

interface MeshPreviewProps {
  layer: Layer | null;
  showOriginalImage: boolean;
  showMesh: boolean;
  onToggleImage: () => void;
  onToggleMesh: () => void;
}

export const MeshPreview: React.FC<MeshPreviewProps> = ({
  layer,
  showOriginalImage,
  showMesh,
  onToggleImage,
  onToggleMesh
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Draw mesh on canvas
  useEffect(() => {
    console.log('MeshPreview render:', { 
      hasLayer: !!layer, 
      hasMesh: !!layer?.mesh,
      hasMeshData: !!layer?.mesh?.data,
      showMesh,
      meshData: layer?.mesh?.data
    });
    
    if (!layer?.mesh?.data || !canvasRef.current || !showMesh) {
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        }
      }
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { vertices, triangles } = layer.mesh.data;
    const bounds = layer.bounds || { x: 0, y: 0, width: 100, height: 100 };
    
    console.log('Drawing mesh:', { 
      verticesCount: vertices?.length,
      trianglesCount: triangles?.length,
      bounds 
    });
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Apply transformations
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);
    
    // Calculate scale to fit canvas
    const padding = 20;
    const scaleX = (canvas.width - padding * 2) / (bounds?.width || 100);
    const scaleY = (canvas.height - padding * 2) / (bounds?.height || 100);
    const scale = Math.min(scaleX, scaleY);
    
    // Draw triangles
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 1 / zoom;
    ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
    
    triangles.forEach(triangle => {
      ctx.beginPath();
      triangle.forEach((vertexIndex, i) => {
        const vertex = vertices[vertexIndex];
        const x = padding + vertex[0] * scale;
        const y = padding + vertex[1] * scale;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
    
    // Draw vertices
    ctx.fillStyle = '#ef4444';
    vertices.forEach(vertex => {
      const x = padding + vertex[0] * scale;
      const y = padding + vertex[1] * scale;
      ctx.beginPath();
      ctx.arc(x, y, 3 / zoom, 0, Math.PI * 2);
      ctx.fill();
    });
    
    ctx.restore();
  }, [layer, showMesh, zoom, pan]);

  // Load image
  useEffect(() => {
    console.log('Image load:', {
      imageUrl: layer?.image_url,
      showOriginalImage
    });
    
    if (layer?.image_url && showOriginalImage) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        console.log('Image loaded successfully');
        imageRef.current = img;
        // Trigger redraw
        if (canvasRef.current) {
          const ctx = canvasRef.current.getContext('2d');
          if (ctx && showOriginalImage && !showMesh) {
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            ctx.save();
            ctx.translate(pan.x, pan.y);
            ctx.scale(zoom, zoom);
            ctx.drawImage(img, 0, 0, canvasRef.current.width, canvasRef.current.height);
            ctx.restore();
          }
        }
      };
      img.onerror = (err) => {
        console.error('Failed to load image:', err, layer.image_url);
      };
      img.src = layer.image_url;
    }
  }, [layer?.image_url, showOriginalImage, zoom, pan]);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => setZoom(z => Math.min(z * 1.2, 5));
  const handleZoomOut = () => setZoom(z => Math.max(z / 1.2, 0.2));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const stats = layer?.mesh ? {
    vertices: layer.mesh.data?.vertices?.length || 0,
    triangles: layer.mesh.data?.triangles?.length || 0
  } : null;

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h3 className="font-semibold">
              Mesh Preview {layer && `- ${layer.name}`}
            </h3>
            
            {/* View toggles */}
            <div className="flex gap-2">
              <button
                onClick={onToggleImage}
                className={`p-2 rounded ${showOriginalImage ? 'bg-blue-600' : 'bg-gray-700'}`}
                title="Toggle Original Image"
              >
                <ImageIcon className="w-4 h-4" />
              </button>
              <button
                onClick={onToggleMesh}
                className={`p-2 rounded ${showMesh ? 'bg-blue-600' : 'bg-gray-700'}`}
                title="Toggle Mesh"
              >
                <Grid3x3 className="w-4 h-4" />
              </button>
            </div>

            {/* Zoom controls */}
            <div className="flex gap-2">
              <button
                onClick={handleZoomOut}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="px-3 py-1 bg-gray-700 rounded text-sm">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
                title="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={handleReset}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded"
                title="Reset View"
              >
                <Maximize className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Statistics */}
          {stats && (
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <div className="flex items-center gap-1">
                <BarChart className="w-4 h-4" />
                <span>Vertices: {stats.vertices}</span>
              </div>
              <div>
                <span>Triangles: {stats.triangles}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 bg-gray-900 p-4 overflow-hidden">
        {layer ? (
          <div className="w-full h-full flex items-center justify-center">
            <canvas
              ref={canvasRef}
              width={800}
              height={600}
              className={`bg-gray-850 border border-gray-700 ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain'
              }}
            />
          </div>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Grid3x3 className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p>Select a layer to preview its mesh</p>
            </div>
          </div>
        )}
      </div>

      {/* Info bar */}
      {layer && (
        <div className="p-2 border-t border-gray-700 bg-gray-800 text-xs text-gray-400 flex items-center gap-4">
          <span className="flex items-center gap-1">
            <Move className="w-3 h-3" />
            Drag to pan
          </span>
          <span>Scroll to zoom</span>
          {layer.bounds && (
            <>
              <span>Size: {Math.round(layer.bounds.width)}x{Math.round(layer.bounds.height)}</span>
              <span>Position: ({Math.round(layer.bounds.x)}, {Math.round(layer.bounds.y)})</span>
            </>
          )}
        </div>
      )}
    </div>
  );
};