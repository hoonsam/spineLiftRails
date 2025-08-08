import React, { useState } from 'react';
import { 
  Settings, 
  Sliders, 
  Save, 
  Download, 
  RefreshCw,
  Zap,
  Eye,
  Gauge
} from 'lucide-react';
import { ParameterPanel } from '../ParameterPanel';
import type { Layer } from '../../types';

interface MeshToolsProps {
  layer: Layer;
  projectId: string;
  onMeshUpdate: () => void;
}

export const MeshTools: React.FC<MeshToolsProps> = ({
  layer,
  projectId,
  onMeshUpdate
}) => {
  const [activeTab, setActiveTab] = useState<'parameters' | 'preview'>('parameters');
  const [autoPreview, setAutoPreview] = useState(true);
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('medium');

  const stats = layer.mesh ? {
    vertices: layer.mesh.data?.vertices?.length || 0,
    triangles: layer.mesh.data?.triangles?.length || 0,
    size: layer.mesh.metadata?.vertex_count || 0
  } : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold">Mesh Tools</h3>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('parameters')}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded text-sm
              ${activeTab === 'parameters' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}
            `}
          >
            <Sliders className="w-4 h-4" />
            Parameters
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded text-sm
              ${activeTab === 'preview' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}
            `}
          >
            <Eye className="w-4 h-4" />
            Preview
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'parameters' ? (
          <>
            {/* Layer Info */}
            <div className="mb-6 p-4 bg-gray-750 rounded">
              <h4 className="text-sm font-medium mb-2">Layer: {layer.name}</h4>
              {stats && (
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Vertices:</span>
                    <span className="ml-1 font-mono">{stats.vertices}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Triangles:</span>
                    <span className="ml-1 font-mono">{stats.triangles}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Size:</span>
                    <span className="ml-1 font-mono">{stats.size}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Parameters */}
            {layer.mesh ? (
              <ParameterPanel
                meshId={layer.mesh.id}
                layerId={layer.id}
                projectId={projectId}
                initialParameters={layer.mesh.parameters}
                onRegenerateMesh={onMeshUpdate}
                onParameterChange={() => {
                  if (autoPreview) {
                    onMeshUpdate();
                  }
                }}
              />
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">No mesh generated yet</p>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded">
                  <RefreshCw className="w-4 h-4 inline mr-2" />
                  Generate Mesh
                </button>
              </div>
            )}
          </>
        ) : (
          /* Preview Tab */
          <div className="space-y-4">
            {/* Preview Settings */}
            <div className="p-4 bg-gray-750 rounded space-y-3">
              <h4 className="text-sm font-medium mb-2">Preview Settings</h4>
              
              {/* Auto Preview Toggle */}
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={autoPreview}
                  onChange={(e) => setAutoPreview(e.target.checked)}
                  className="rounded bg-gray-700 border-gray-600"
                />
                <span className="text-sm">Real-time Preview</span>
              </label>

              {/* Quality Selector */}
              <div>
                <label className="text-sm text-gray-400 block mb-1">
                  Preview Quality
                </label>
                <div className="flex gap-2">
                  {(['low', 'medium', 'high'] as const).map((q) => (
                    <button
                      key={q}
                      onClick={() => setQuality(q)}
                      className={`
                        px-3 py-1 rounded text-sm capitalize
                        ${quality === q 
                          ? 'bg-blue-600' 
                          : 'bg-gray-700 hover:bg-gray-600'}
                      `}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2">
              <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded">
                <Gauge className="w-4 h-4" />
                Optimize Mesh
              </button>
              <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded">
                <Zap className="w-4 h-4" />
                Auto-Adjust Parameters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-700 space-y-2">
        <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded">
          <Save className="w-4 h-4" />
          Save Mesh
        </button>
        <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>
    </div>
  );
};