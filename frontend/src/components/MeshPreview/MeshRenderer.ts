// Mesh rendering utilities
export class MeshRenderer {
  private ctx: CanvasRenderingContext2D;
  private image: HTMLImageElement | null = null;
  private zoom: number = 1;
  private pan: { x: number; y: number } = { x: 0, y: 0 };

  constructor(canvas: HTMLCanvasElement) {
    this.ctx = canvas.getContext('2d')!;
  }

  setImage(imageUrl: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      
      img.onload = () => {
        this.image = img;
        resolve();
      };
      
      img.onerror = reject;
      img.src = imageUrl;
    });
  }

  clear() {
    this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
  }

  renderImage(opacity: number = 1) {
    if (!this.image) return;

    this.ctx.save();
    this.ctx.globalAlpha = opacity;
    this.ctx.translate(this.pan.x, this.pan.y);
    this.ctx.scale(this.zoom, this.zoom);

    // Scale image to fit canvas
    const canvas = this.ctx.canvas;
    const scale = Math.min(
      canvas.width / this.image.width,
      canvas.height / this.image.height
    );

    const width = this.image.width * scale;
    const height = this.image.height * scale;
    const x = (canvas.width - width) / 2;
    const y = (canvas.height - height) / 2;

    this.ctx.drawImage(this.image, x, y, width, height);
    this.ctx.restore();
  }

  renderMesh(meshData: any, options: {
    wireframeColor?: string;
    fillColor?: string;
    vertexColor?: string;
    showVertices?: boolean;
    showWireframe?: boolean;
    showFill?: boolean;
  } = {}) {
    const {
      wireframeColor = '#3b82f6',
      fillColor = 'rgba(59, 130, 246, 0.1)',
      vertexColor = '#ef4444',
      showVertices = true,
      showWireframe = true,
      showFill = true
    } = options;

    if (!meshData?.vertices || !meshData?.triangles) return;

    const { vertices, triangles, bounds } = meshData;
    const canvas = this.ctx.canvas;

    this.ctx.save();
    this.ctx.translate(this.pan.x, this.pan.y);
    this.ctx.scale(this.zoom, this.zoom);

    // Calculate scale to fit
    const padding = 40;
    const scaleX = (canvas.width - padding * 2) / (bounds?.width || 100);
    const scaleY = (canvas.height - padding * 2) / (bounds?.height || 100);
    const scale = Math.min(scaleX, scaleY);

    // Center offset
    const offsetX = (canvas.width - (bounds?.width || 100) * scale) / 2;
    const offsetY = (canvas.height - (bounds?.height || 100) * scale) / 2;

    // Draw triangles
    triangles.forEach((triangle: number[]) => {
      this.ctx.beginPath();
      
      triangle.forEach((vertexIndex, i) => {
        const vertex = vertices[vertexIndex];
        if (!vertex) return;
        
        const x = offsetX + (vertex[0] - (bounds?.x || 0)) * scale;
        const y = offsetY + (vertex[1] - (bounds?.y || 0)) * scale;
        
        if (i === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      });
      
      this.ctx.closePath();
      
      // Fill
      if (showFill) {
        this.ctx.fillStyle = fillColor;
        this.ctx.fill();
      }
      
      // Wireframe
      if (showWireframe) {
        this.ctx.strokeStyle = wireframeColor;
        this.ctx.lineWidth = 1.5 / this.zoom;
        this.ctx.stroke();
      }
    });

    // Draw vertices
    if (showVertices) {
      this.ctx.fillStyle = vertexColor;
      vertices.forEach((vertex: number[]) => {
        const x = offsetX + (vertex[0] - (bounds?.x || 0)) * scale;
        const y = offsetY + (vertex[1] - (bounds?.y || 0)) * scale;
        
        this.ctx.beginPath();
        this.ctx.arc(x, y, 3 / this.zoom, 0, Math.PI * 2);
        this.ctx.fill();
      });
    }

    this.ctx.restore();
  }

  renderComposite(imageUrl: string | null, meshData: any, options: {
    imageOpacity?: number;
    showImage?: boolean;
    showMesh?: boolean;
  } = {}) {
    const {
      imageOpacity = 0.5,
      showImage = true,
      showMesh = true
    } = options;

    this.clear();

    // Render image first (background)
    if (showImage && imageUrl) {
      this.renderImage(imageOpacity);
    }

    // Render mesh overlay
    if (showMesh && meshData) {
      this.renderMesh(meshData, {
        showFill: false, // Only wireframe over image
        showWireframe: true,
        showVertices: true
      });
    }
  }

  setZoom(zoom: number) {
    this.zoom = Math.max(0.1, Math.min(5, zoom));
  }

  setPan(x: number, y: number) {
    this.pan = { x, y };
  }

  getZoom() {
    return this.zoom;
  }

  getPan() {
    return { ...this.pan };
  }
}