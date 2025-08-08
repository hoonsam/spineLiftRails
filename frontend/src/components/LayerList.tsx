import React from 'react';
import { Layers, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react';
import type { Layer } from '../types/index';

interface LayerListProps {
  layers: Layer[];
  selectedLayerId?: string;
  onSelectLayer: (layer: Layer) => void;
}

export const LayerList: React.FC<LayerListProps> = ({
  layers,
  selectedLayerId,
  onSelectLayer,
}) => {
  const getStatusIcon = (status: Layer['status']) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'completed':
        return <Eye className="w-4 h-4 text-green-500" />;
      default:
        return <EyeOff className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: Layer['status']) => {
    switch (status) {
      case 'processing':
        return 'Generating mesh...';
      case 'failed':
        return 'Failed to generate';
      case 'completed':
        return 'Mesh ready';
      default:
        return 'Pending';
    }
  };

  if (layers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col items-center justify-center text-gray-500">
          <Layers className="w-12 h-12 mb-2" />
          <p className="text-sm">No layers found</p>
          <p className="text-xs mt-1">Upload a PSD file to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 flex items-center">
          <Layers className="w-4 h-4 mr-2" />
          Layers ({layers.length})
        </h3>
      </div>
      
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {layers.map((layer) => (
          <button
            key={layer.id}
            onClick={() => onSelectLayer(layer)}
            className={`w-full px-4 py-3 hover:bg-gray-50 transition-colors text-left ${
              selectedLayerId === layer.id ? 'bg-blue-50' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {layer.name}
                  </p>
                  {layer.bounds && (
                    <span className="text-xs text-gray-500">
                      {layer.bounds.width}×{layer.bounds.height}
                    </span>
                  )}
                </div>
                <div className="flex items-center mt-1 space-x-2">
                  {getStatusIcon(layer.status)}
                  <p className="text-xs text-gray-500">
                    {getStatusText(layer.status)}
                  </p>
                </div>
                {layer.error_message && (
                  <p className="text-xs text-red-600 mt-1 truncate">
                    {layer.error_message}
                  </p>
                )}
              </div>
              
              {layer.image_url && (
                <div className="ml-3 flex-shrink-0">
                  <img
                    src={layer.image_url}
                    alt={layer.name}
                    className="w-12 h-12 object-contain bg-gray-100 rounded"
                  />
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};