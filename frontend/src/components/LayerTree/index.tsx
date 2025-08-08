import React from 'react';
import { 
  CheckSquare, 
  Square, 
  Eye, 
  Zap, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Layers,
  Play
} from 'lucide-react';
import type { Layer } from '../../types';

interface LayerTreeProps {
  layers: Layer[];
  selectedLayers: Set<string>;
  currentLayer: Layer | null;
  onLayerSelect: (layer: Layer) => void;
  onLayerToggle: (layerId: string) => void;
  onBatchProcess: () => void;
}

export const LayerTree: React.FC<LayerTreeProps> = ({
  layers,
  selectedLayers,
  currentLayer,
  onLayerSelect,
  onLayerToggle,
  onBatchProcess
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const completedCount = layers.filter(l => l.status === 'completed').length;
  const progressPercentage = layers.length > 0 ? (completedCount / layers.length) * 100 : 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold">Layer Tree</h3>
          </div>
          <span className="text-sm text-gray-400">
            {layers.length} layers
          </span>
        </div>
        
        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Progress</span>
            <span>{completedCount}/{layers.length}</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Batch Actions */}
        {selectedLayers.size > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={onBatchProcess}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm"
            >
              <Zap className="w-4 h-4" />
              Batch Process ({selectedLayers.size})
            </button>
          </div>
        )}
      </div>

      {/* Layer List */}
      <div className="flex-1 overflow-y-auto">
        {layers.map((layer) => (
          <div
            key={layer.id}
            className={`
              flex items-center gap-3 px-4 py-3 border-b border-gray-700
              hover:bg-gray-750 cursor-pointer transition-colors
              ${currentLayer?.id === layer.id ? 'bg-gray-700' : ''}
            `}
            onClick={() => onLayerSelect(layer)}
          >
            {/* Checkbox */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onLayerToggle(layer.id);
              }}
              className="flex-shrink-0"
            >
              {selectedLayers.has(layer.id) ? (
                <CheckSquare className="w-5 h-5 text-blue-500" />
              ) : (
                <Square className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {/* Layer Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium truncate">{layer.name}</span>
                {getStatusIcon(layer.status)}
              </div>
              {layer.mesh && (
                <div className="text-xs text-gray-500 mt-1">
                  Mesh ready
                </div>
              )}
            </div>

            {/* Visibility Toggle */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Toggle visibility
              }}
              className="flex-shrink-0"
            >
              <Eye className="w-4 h-4 text-gray-500 hover:text-gray-300" />
            </button>
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-700">
        <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded">
          <Play className="w-4 h-4" />
          Generate All Meshes
        </button>
      </div>
    </div>
  );
};