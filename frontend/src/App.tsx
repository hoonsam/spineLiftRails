import { useState, useEffect } from 'react';
import { LayerTree } from './components/LayerTree';
import { MeshPreview } from './components/MeshPreview';
import { MeshTools } from './components/MeshTools';
import { LoginForm } from './components/LoginForm';
import { ProcessingStatus } from './components/ProcessingStatus';
import { useStore } from './store/useStore';
import { projectsApi, layersApi, authApi } from './lib/api';
import { Loader2, LogOut, Upload, FolderOpen } from 'lucide-react';
import './App.css';

function App() {
  const { 
    user,
    token,
    setAuth,
    currentProject, 
    layers, 
    currentLayer,
    setCurrentProject,
    setLayers,
    setCurrentLayer,
    isLoading,
    setLoading
  } = useStore();
  
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showProcessingStatus, setShowProcessingStatus] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [selectedLayers, setSelectedLayers] = useState<Set<string>>(new Set());
  const [showOriginalImage, setShowOriginalImage] = useState(true);
  const [showMesh, setShowMesh] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (token && !user) {
        try {
          const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            const userData = data.user?.data ? 
              { id: data.user.data.id, ...data.user.data.attributes } : 
              data.user;
            setAuth(userData, token);
          } else {
            setAuth(null, null);
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          setAuth(null, null);
        }
      }
      setIsCheckingAuth(false);
    };
    
    checkAuth();
  }, []);

  // Load saved project when user is authenticated
  useEffect(() => {
    const loadSavedProject = async () => {
      if (user && token && !currentProject) {
        const savedProjectId = localStorage.getItem('currentProjectId');
        console.log('Checking for saved project:', { 
          savedProjectId, 
          user: user?.email, 
          hasToken: !!token,
          hasCurrentProject: !!currentProject 
        });
        
        if (savedProjectId) {
          try {
            setLoading(true);
            console.log('Loading project:', savedProjectId);
            const project = await projectsApi.get(savedProjectId);
            setCurrentProject(project);
            console.log('Project loaded:', project.name);
            
            const layersData = await layersApi.list(savedProjectId);
            setLayers(layersData);
            console.log('Layers loaded:', layersData.length);
          } catch (error: any) {
            console.error('Failed to load saved project:', error);
            console.error('Error details:', {
              message: error.message,
              response: error.response?.data,
              status: error.response?.status
            });
            // Don't remove the ID immediately - let user retry
            // localStorage.removeItem('currentProjectId');
          } finally {
            setLoading(false);
          }
        }
      }
    };

    loadSavedProject();
  }, [user, token]);

  // Save current project ID when it changes
  useEffect(() => {
    if (currentProject) {
      localStorage.setItem('currentProjectId', currentProject.id);
      console.log('Saved project ID to localStorage:', currentProject.id);
    } else {
      console.log('currentProject became null - NOT removing from localStorage');
      // Don't automatically remove - user might be navigating temporarily
      // localStorage.removeItem('currentProjectId');
    }
  }, [currentProject]);

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setUploadError(null);
    
    try {
      const projectName = file.name.replace(/\.psd$/i, '');
      console.log('Creating project with name:', projectName);
      const project = await projectsApi.create(projectName, file);
      console.log('Project created:', project);
      console.log('Project ID:', project.id, 'Type:', typeof project.id);
      setCurrentProject(project);
      setShowProcessingStatus(true);
      setLoading(false);
    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadError(error.response?.data?.error || 'Failed to upload file');
      setLoading(false);
    }
  };

  const handleProcessingComplete = async () => {
    if (currentProject) {
      try {
        const layersData = await layersApi.list(currentProject.id);
        setLayers(layersData);
        setShowProcessingStatus(false);
      } catch (error) {
        console.error('Error loading layers:', error);
      }
    }
  };

  const handleLayerToggle = (layerId: string) => {
    const newSelected = new Set(selectedLayers);
    if (newSelected.has(layerId)) {
      newSelected.delete(layerId);
    } else {
      newSelected.add(layerId);
    }
    setSelectedLayers(newSelected);
  };

  const handleBatchProcess = () => {
    console.log('Batch processing layers:', Array.from(selectedLayers));
    // Implement batch processing
  };

  const handleLogout = () => {
    authApi.logout();
    setAuth(null, null);
    setCurrentProject(null);
    setLayers([]);
    // Clear project ID only on logout
    localStorage.removeItem('currentProjectId');
    console.log('User logged out - cleared localStorage');
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <p className="text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoginForm />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">SpineLift Mesh Editor</h1>
            {currentProject && (
              <span className="text-sm text-gray-400">
                Project: {currentProject.name}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            {!currentProject && (
              <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded cursor-pointer">
                <Upload className="w-4 h-4" />
                <span>Upload PSD</span>
                <input
                  type="file"
                  accept=".psd"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  className="hidden"
                />
              </label>
            )}
            
            <button
              onClick={() => {
                console.log('Navigating to projects list');
                setCurrentProject(null);
              }}
              className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-700 rounded"
            >
              <FolderOpen className="w-4 h-4" />
              Projects
            </button>
            
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">{user.email}</span>
              <button
                onClick={handleLogout}
                className="hover:text-gray-300"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex h-[calc(100vh-56px)]">
        {showProcessingStatus ? (
          <div className="flex-1 flex items-center justify-center">
            <ProcessingStatus
              projectId={currentProject?.id || ''}
              onComplete={handleProcessingComplete}
              onError={(error) => setUploadError(error)}
            />
          </div>
        ) : currentProject ? (
          <>
            {/* Left Panel - Layer Tree */}
            <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
              <LayerTree
                layers={layers}
                selectedLayers={selectedLayers}
                currentLayer={currentLayer}
                onLayerSelect={setCurrentLayer}
                onLayerToggle={handleLayerToggle}
                onBatchProcess={handleBatchProcess}
              />
            </div>

            {/* Center Panel - Mesh Preview */}
            <div className="flex-1 bg-gray-850 flex flex-col">
              <MeshPreview
                layer={currentLayer}
                showOriginalImage={showOriginalImage}
                showMesh={showMesh}
                onToggleImage={() => setShowOriginalImage(!showOriginalImage)}
                onToggleMesh={() => setShowMesh(!showMesh)}
              />
            </div>

            {/* Right Panel - Mesh Tools */}
            <div className="w-96 bg-gray-800 border-l border-gray-700">
              {currentLayer ? (
                <MeshTools
                  layer={currentLayer}
                  projectId={currentProject.id}
                  onMeshUpdate={() => {
                    // Refresh mesh preview
                    console.log('Mesh updated');
                  }}
                />
              ) : (
                <div className="p-6 text-center text-gray-500">
                  Select a layer to access mesh tools
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Welcome to SpineLift</h2>
              <p className="text-gray-400 mb-8">
                Upload a PSD file to start creating meshes
              </p>
              <label className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg cursor-pointer">
                <Upload className="w-5 h-5" />
                <span>Upload PSD File</span>
                <input
                  type="file"
                  accept=".psd"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        )}
      </main>

      {/* Error message */}
      {uploadError && (
        <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg">
          {uploadError}
        </div>
      )}

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 flex items-center space-x-3">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <p>Processing...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;