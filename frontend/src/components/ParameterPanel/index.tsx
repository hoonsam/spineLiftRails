import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { ParameterSlider } from './ParameterSlider';
import { PresetSelector } from './PresetSelector';
import type { 
  MeshParameters, 
  ParameterPanelProps, 
  MeshPreset 
} from './types';
import { 
  parameterConfigs, 
  getDefaultParameters 
} from './parameterConfigs';
import { apiClient } from '../../services/apiClient';
import { useWebSocket } from '../../hooks/useWebSocket';

export const ParameterPanel: React.FC<ParameterPanelProps> = ({
  meshId,
  layerId,
  projectId,
  initialParameters,
  disabled = false,
  onParameterChange,
  onRegenerateMesh
}) => {
  const [parameters, setParameters] = useState<MeshParameters>(
    initialParameters || getDefaultParameters()
  );
  const [customPresets, setCustomPresets] = useState<MeshPreset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [autoRegenerate, setAutoRegenerate] = useState(true);

  // Load custom presets from localStorage
  useEffect(() => {
    const loadCustomPresets = () => {
      const saved = localStorage.getItem('meshPresets');
      if (saved) {
        setCustomPresets(JSON.parse(saved));
      }
    };

    loadCustomPresets();
    window.addEventListener('presetsUpdated', loadCustomPresets);
    
    return () => {
      window.removeEventListener('presetsUpdated', loadCustomPresets);
    };
  }, []);

  // WebSocket subscription for real-time updates
  const { subscribe, unsubscribe } = useWebSocket();
  
  useEffect(() => {
    if (!meshId) return;

    const subscription = subscribe(`mesh:${meshId}`, (message) => {
      if (message.type === 'mesh_update') {
        if (message.action === 'parameters_updated' && message.parameters) {
          setParameters(message.parameters);
        }
      }
    });

    return () => {
      if (subscription) unsubscribe(subscription);
    };
  }, [meshId, subscribe, unsubscribe]);

  // Debounced API call for parameter updates
  const updateMeshParameters = useCallback(
    debounce(async (newParams: MeshParameters) => {
      if (!meshId || !layerId || !projectId) return;

      setIsLoading(true);
      try {
        const response = await apiClient.put(
          `/api/v1/projects/${projectId}/layers/${layerId}/mesh/update_parameters`,
          {
            parameters: newParams,
            regenerate: autoRegenerate
          }
        );

        if (response.data.status === 'regenerating' && onRegenerateMesh) {
          onRegenerateMesh();
        }
      } catch (error) {
        console.error('Failed to update mesh parameters:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    [meshId, layerId, projectId, autoRegenerate, onRegenerateMesh]
  );

  const handleParameterChange = (key: keyof MeshParameters, value: number) => {
    const newParams = { ...parameters, [key]: value };
    setParameters(newParams);
    
    if (onParameterChange) {
      onParameterChange(newParams);
    }
    
    updateMeshParameters(newParams);
  };

  const handlePresetSelect = (preset: MeshPreset) => {
    setParameters(preset.parameters);
    
    if (onParameterChange) {
      onParameterChange(preset.parameters);
    }
    
    updateMeshParameters(preset.parameters);
  };

  const resetParameters = () => {
    const defaults = getDefaultParameters();
    setParameters(defaults);
    
    if (onParameterChange) {
      onParameterChange(defaults);
    }
    
    updateMeshParameters(defaults);
  };

  const regenerateMesh = async () => {
    if (!meshId || !layerId || !projectId) return;

    setIsLoading(true);
    try {
      await apiClient.put(
        `/api/v1/projects/${projectId}/layers/${layerId}/mesh/update_parameters`,
        {
          parameters,
          regenerate: true
        }
      );
      
      if (onRegenerateMesh) {
        onRegenerateMesh();
      }
    } catch (error) {
      console.error('Failed to regenerate mesh:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="parameter-panel bg-gray-750 rounded-lg p-4">
      <div className="panel-header flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-white">Mesh Parameters</h3>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="text-gray-400 hover:text-gray-200"
        >
          {isCollapsed ? 'Expand ▼' : 'Collapse ▲'}
        </button>
      </div>

      {!isCollapsed && (
        <>
          {/* Auto-regenerate toggle */}
          <div className="mb-4 flex items-center">
            <input
              type="checkbox"
              id="autoRegenerate"
              checked={autoRegenerate}
              onChange={(e) => setAutoRegenerate(e.target.checked)}
              className="mr-2"
            />
            <label htmlFor="autoRegenerate" className="text-sm text-gray-300">
              Auto-regenerate on parameter change
            </label>
          </div>

          {/* Preset selector */}
          <PresetSelector
            currentParameters={parameters}
            onPresetSelect={handlePresetSelect}
            customPresets={customPresets}
            disabled={disabled || isLoading}
          />

          {/* Parameter sliders */}
          <div className="parameter-sliders space-y-2 my-4">
            {parameterConfigs.map(config => (
              <ParameterSlider
                key={config.key}
                config={config}
                value={parameters[config.key] || config.defaultValue}
                onChange={(value) => handleParameterChange(config.key, value)}
                disabled={disabled || isLoading}
              />
            ))}
          </div>

          {/* Action buttons */}
          <div className="panel-actions flex gap-2 mt-4">
            <button
              onClick={resetParameters}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={disabled || isLoading}
            >
              기본값으로 리셋
            </button>
            
            {!autoRegenerate && (
              <button
                onClick={regenerateMesh}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={disabled || isLoading}
              >
                메시 재생성
              </button>
            )}
          </div>

          {/* Loading indicator */}
          {isLoading && (
            <div className="mt-4 text-center">
              <div className="inline-flex items-center">
                <svg className="animate-spin h-5 w-5 mr-2 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-sm text-gray-600">메시 재생성 중...</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ParameterPanel;