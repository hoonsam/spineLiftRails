import { useEffect, useRef, useState, useCallback } from 'react';
import { createConsumer, Subscription } from '@rails/actioncable';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface WebSocketCallbacks {
  onMessage?: (message: WebSocketMessage) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
}

export const useWebSocket = () => {
  const consumerRef = useRef<any>(null);
  const subscriptionsRef = useRef<Map<string, Subscription>>(new Map());
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Create consumer if not exists
    if (!consumerRef.current) {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:3000/cable';
      consumerRef.current = createConsumer(wsUrl);
      setIsConnected(true);
    }

    return () => {
      // Cleanup on unmount
      if (consumerRef.current) {
        subscriptionsRef.current.forEach(subscription => {
          subscription.unsubscribe();
        });
        subscriptionsRef.current.clear();
        consumerRef.current.disconnect();
        consumerRef.current = null;
        setIsConnected(false);
      }
    };
  }, []);

  const subscribe = useCallback((channelName: string, callbacks: WebSocketCallbacks | ((message: WebSocketMessage) => void)) => {
    if (!consumerRef.current) return null;

    // If callbacks is a function, wrap it in an object
    const callbacksObj: WebSocketCallbacks = typeof callbacks === 'function' 
      ? { onMessage: callbacks }
      : callbacks;

    // Parse channel name to determine channel type and id
    const [channelType, channelId] = channelName.split(':');
    
    let channelParams: any = {};
    if (channelType === 'project') {
      channelParams = { channel: 'ProjectChannel', project_id: channelId };
    } else if (channelType === 'mesh') {
      channelParams = { channel: 'MeshChannel', mesh_id: channelId };
    } else {
      // Default channel
      channelParams = { channel: channelName };
    }

    const subscription = consumerRef.current.subscriptions.create(channelParams, {
      connected: () => {
        console.log(`Connected to ${channelName}`);
        if (callbacksObj.onConnected) {
          callbacksObj.onConnected();
        }
      },
      disconnected: () => {
        console.log(`Disconnected from ${channelName}`);
        if (callbacksObj.onDisconnected) {
          callbacksObj.onDisconnected();
        }
      },
      received: (data: WebSocketMessage) => {
        console.log(`Received message on ${channelName}:`, data);
        if (callbacksObj.onMessage) {
          callbacksObj.onMessage(data);
        }
      }
    });

    subscriptionsRef.current.set(channelName, subscription);
    return subscription;
  }, []);

  const unsubscribe = useCallback((subscription: Subscription | string) => {
    if (typeof subscription === 'string') {
      const sub = subscriptionsRef.current.get(subscription);
      if (sub) {
        sub.unsubscribe();
        subscriptionsRef.current.delete(subscription);
      }
    } else if (subscription) {
      subscription.unsubscribe();
      // Remove from map
      subscriptionsRef.current.forEach((sub, key) => {
        if (sub === subscription) {
          subscriptionsRef.current.delete(key);
        }
      });
    }
  }, []);

  const send = useCallback((channelName: string, data: any) => {
    const subscription = subscriptionsRef.current.get(channelName);
    if (subscription) {
      subscription.send(data);
    }
  }, []);

  return {
    isConnected,
    subscribe,
    unsubscribe,
    send
  };
};

// Hook for project-specific WebSocket subscription
export const useProjectWebSocket = (projectId: string | undefined, onMessage: (message: WebSocketMessage) => void) => {
  const { subscribe, unsubscribe } = useWebSocket();
  
  useEffect(() => {
    if (!projectId) return;

    const subscription = subscribe(`project:${projectId}`, onMessage);

    return () => {
      if (subscription) {
        unsubscribe(subscription);
      }
    };
  }, [projectId, onMessage, subscribe, unsubscribe]);
};

// Hook for mesh-specific WebSocket subscription
export const useMeshWebSocket = (meshId: string | undefined, onMessage: (message: WebSocketMessage) => void) => {
  const { subscribe, unsubscribe } = useWebSocket();
  
  useEffect(() => {
    if (!meshId) return;

    const subscription = subscribe(`mesh:${meshId}`, onMessage);

    return () => {
      if (subscription) {
        unsubscribe(subscription);
      }
    };
  }, [meshId, onMessage, subscribe, unsubscribe]);
};