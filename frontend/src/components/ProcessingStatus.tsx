import React, { useEffect, useState } from 'react';
import { createConsumer } from '@rails/actioncable';
import { Progress } from './ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Button } from './ui/button';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface ProcessingStatusProps {
  projectId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

interface ProcessingState {
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentStep: string;
  totalLayers: number;
  processedLayers: number;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  duration?: number;
  logs: ProcessingLog[];
}

interface ProcessingLog {
  step: string;
  status: string;
  message: string;
  timestamp: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  projectId,
  onComplete,
  onError
}) => {
  const [state, setState] = useState<ProcessingState>({
    status: 'pending',
    progress: 0,
    currentStep: 'Initializing...',
    totalLayers: 0,
    processedLayers: 0,
    logs: []
  });
  const [_subscription, setSubscription] = useState<any>(null);

  useEffect(() => {
    // Initial status fetch
    fetchStatus();

    // Setup WebSocket connection
    const cableUrl = import.meta.env.VITE_CABLE_URL || 'ws://localhost:3000/cable';
    const cable = createConsumer(cableUrl);
    const sub = cable.subscriptions.create(
      { channel: 'ProjectChannel', project_id: projectId },
      {
        connected() {
          console.log('Connected to ProjectChannel');
        },
        disconnected() {
          console.log('Disconnected from ProjectChannel');
        },
        received(data: any) {
          console.log('Received:', data);
          handleWebSocketMessage(data);
        }
      }
    );

    setSubscription(sub);

    // Poll for status every 2 seconds as backup
    const interval = setInterval(fetchStatus, 2000);

    return () => {
      if (sub) {
        sub.unsubscribe();
      }
      clearInterval(interval);
    };
  }, [projectId]);

  const fetchStatus = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1';
      const response = await fetch(`${apiUrl}/projects/${projectId}/processing_status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        const data = result.data.attributes;
        
        setState({
          status: data.status,
          progress: data.progress || 0,
          currentStep: data.current_step || 'Processing...',
          totalLayers: data.total_layers || 0,
          processedLayers: data.processed_layers || 0,
          startedAt: data.started_at,
          completedAt: data.completed_at,
          errorMessage: data.error_message,
          duration: data.duration,
          logs: data.logs || []
        });

        if (data.status === 'completed' && onComplete) {
          onComplete();
        } else if (data.status === 'failed' && onError) {
          onError(data.error_message || 'Processing failed');
        }
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.event) {
      case 'progress_update':
        setState(prev => ({
          ...prev,
          progress: data.progress,
          processedLayers: data.current,
          totalLayers: data.total,
          currentStep: `Processing layer ${data.current} of ${data.total}`
        }));
        break;

      case 'status_change':
        setState(prev => ({
          ...prev,
          status: data.status,
          ...(data.error_message && { errorMessage: data.error_message })
        }));
        
        if (data.status === 'completed' && onComplete) {
          onComplete();
        } else if (data.status === 'failed' && onError) {
          onError(data.error_message || 'Processing failed');
        }
        break;

      case 'error':
        setState(prev => ({
          ...prev,
          status: 'failed',
          errorMessage: data.message
        }));
        if (onError) {
          onError(data.message);
        }
        break;
    }
  };

  const handleCancel = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1';
      const response = await fetch(`${apiUrl}/projects/${projectId}/cancel_processing`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setState(prev => ({ ...prev, status: 'cancelled' }));
      }
    } catch (error) {
      console.error('Error cancelling processing:', error);
    }
  };

  const getStatusIcon = () => {
    switch (state.status) {
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'cancelled':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (state.status) {
      case 'processing':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'cancelled':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <CardTitle className={getStatusColor()}>
              Processing Status: {state.status.charAt(0).toUpperCase() + state.status.slice(1)}
            </CardTitle>
          </div>
          {state.status === 'processing' && (
            <Button variant="outline" size="sm" onClick={handleCancel}>
              Cancel
            </Button>
          )}
        </div>
        <CardDescription>{state.currentStep}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {state.status === 'processing' && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Progress</span>
              <span>{state.progress}%</span>
            </div>
            <Progress value={state.progress} className="h-2" />
            {state.totalLayers > 0 && (
              <div className="text-sm text-gray-500">
                Processing layer {state.processedLayers} of {state.totalLayers}
              </div>
            )}
          </div>
        )}

        {state.errorMessage && (
          <Alert variant="destructive">
            <AlertDescription>{state.errorMessage}</AlertDescription>
          </Alert>
        )}

        {state.duration && state.status === 'completed' && (
          <div className="text-sm text-gray-600">
            Completed in {Math.round(state.duration)} seconds
          </div>
        )}

        {state.logs.length > 0 && (
          <div className="space-y-1">
            <h4 className="text-sm font-medium">Processing Log</h4>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {state.logs.map((log, index) => (
                <div key={index} className="text-xs text-gray-600">
                  <span className="font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  {' - '}
                  <span className={log.status === 'error' ? 'text-red-600' : ''}>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};