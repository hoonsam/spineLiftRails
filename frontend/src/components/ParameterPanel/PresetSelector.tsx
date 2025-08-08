import React from 'react';
import type { MeshPreset, MeshParameters } from './types';
import { systemPresets } from './parameterConfigs';

interface PresetSelectorProps {
  currentParameters: MeshParameters;
  onPresetSelect: (preset: MeshPreset) => void;
  customPresets?: MeshPreset[];
  disabled?: boolean;
}

export const PresetSelector: React.FC<PresetSelectorProps> = ({
  currentParameters,
  onPresetSelect,
  customPresets = [],
  disabled = false
}) => {
  const [selectedPresetId, setSelectedPresetId] = React.useState<string | null>(null);
  const [showCustomDialog, setShowCustomDialog] = React.useState(false);
  const [customPresetName, setCustomPresetName] = React.useState('');

  const allPresets = [...systemPresets, ...customPresets];

  const handlePresetSelect = (preset: MeshPreset) => {
    setSelectedPresetId(preset.id);
    onPresetSelect(preset);
  };

  const saveCustomPreset = () => {
    if (customPresetName.trim()) {
      const newPreset: MeshPreset = {
        id: `custom-${Date.now()}`,
        name: customPresetName,
        parameters: { ...currentParameters },
        isSystem: false,
        createdAt: new Date()
      };
      
      // Save to localStorage
      const savedPresets = JSON.parse(localStorage.getItem('meshPresets') || '[]');
      savedPresets.push(newPreset);
      localStorage.setItem('meshPresets', JSON.stringify(savedPresets));
      
      setShowCustomDialog(false);
      setCustomPresetName('');
      
      // Trigger parent component update if needed
      window.dispatchEvent(new Event('presetsUpdated'));
    }
  };

  return (
    <div className="preset-selector">
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          프리셋
        </label>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {allPresets.map(preset => (
            <button
              key={preset.id}
              onClick={() => handlePresetSelect(preset)}
              disabled={disabled}
              className={`
                px-3 py-2 text-sm rounded-lg border transition-all
                ${selectedPresetId === preset.id 
                  ? 'bg-blue-500 text-white border-blue-600' 
                  : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="font-medium">{preset.name}</div>
              {preset.description && (
                <div className="text-xs opacity-80 mt-1">{preset.description}</div>
              )}
              {!preset.isSystem && (
                <span className="inline-block mt-1 px-1 py-0.5 text-xs bg-gray-200 text-gray-600 rounded">
                  사용자 정의
                </span>
              )}
            </button>
          ))}
        </div>
        
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => setShowCustomDialog(true)}
            disabled={disabled}
            className="px-3 py-1.5 text-sm bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            현재 설정 저장
          </button>
          
          {customPresets.length > 0 && (
            <button
              onClick={() => {
                localStorage.removeItem('meshPresets');
                window.dispatchEvent(new Event('presetsUpdated'));
              }}
              disabled={disabled}
              className="px-3 py-1.5 text-sm bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              사용자 프리셋 초기화
            </button>
          )}
        </div>
      </div>
      
      {showCustomDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full">
            <h3 className="text-lg font-semibold mb-4">프리셋 저장</h3>
            <input
              type="text"
              value={customPresetName}
              onChange={(e) => setCustomPresetName(e.target.value)}
              placeholder="프리셋 이름 입력"
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCustomDialog(false);
                  setCustomPresetName('');
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                취소
              </button>
              <button
                onClick={saveCustomPreset}
                disabled={!customPresetName.trim()}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};