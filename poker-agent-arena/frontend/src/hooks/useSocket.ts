/**
 * React hook for Socket.IO connection management
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { socketClient, SocketEventCallbacks, TableState } from '@/lib/socket';
import { getSessionToken } from '@/lib/api';

interface UseSocketOptions {
  autoConnect?: boolean;
  tournamentId?: string;
  tableId?: string;
  callbacks?: SocketEventCallbacks;
}

export function useSocket(options: UseSocketOptions = {}) {
  const { autoConnect = true, tournamentId, tableId, callbacks } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const callbacksRef = useRef(callbacks);
  callbacksRef.current = callbacks;

  // Connect to socket
  const connect = useCallback(() => {
    const token = getSessionToken();
    if (!token) {
      setError('Not authenticated');
      return;
    }

    socketClient.connect({
      onConnect: () => {
        setIsConnected(true);
        setError(null);
        callbacksRef.current?.onConnect?.();
      },
      onDisconnect: () => {
        setIsConnected(false);
        callbacksRef.current?.onDisconnect?.();
      },
      onError: (err) => {
        setError(err.message);
        callbacksRef.current?.onError?.(err);
      },
      onAuthenticated: (data) => {
        callbacksRef.current?.onAuthenticated?.(data);
      },
      onTournamentStarted: (data) => {
        callbacksRef.current?.onTournamentStarted?.(data);
      },
      onLevelUp: (data) => {
        callbacksRef.current?.onLevelUp?.(data);
      },
      onTournamentCompleted: (data) => {
        callbacksRef.current?.onTournamentCompleted?.(data);
      },
      onPlayerEliminated: (data) => {
        callbacksRef.current?.onPlayerEliminated?.(data);
      },
      onPlayerMoved: (data) => {
        callbacksRef.current?.onPlayerMoved?.(data);
      },
      onTableState: (data) => {
        callbacksRef.current?.onTableState?.(data);
      },
      onHandNew: (data) => {
        callbacksRef.current?.onHandNew?.(data);
      },
      onHandDeal: (data) => {
        callbacksRef.current?.onHandDeal?.(data);
      },
      onHandCommunity: (data) => {
        callbacksRef.current?.onHandCommunity?.(data);
      },
      onHandAction: (data) => {
        callbacksRef.current?.onHandAction?.(data);
      },
      onHandShowdown: (data) => {
        callbacksRef.current?.onHandShowdown?.(data);
      },
      onDecisionStart: (data) => {
        callbacksRef.current?.onDecisionStart?.(data);
      },
      onSettingsConfirmed: (data) => {
        callbacksRef.current?.onSettingsConfirmed?.(data);
      },
      onSettingsApplied: (data) => {
        callbacksRef.current?.onSettingsApplied?.(data);
      },
    });
  }, []);

  // Disconnect from socket
  const disconnect = useCallback(() => {
    socketClient.disconnect();
    setIsConnected(false);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      const token = getSessionToken();
      if (token) {
        connect();
      }
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Join tournament room when tournamentId changes
  useEffect(() => {
    if (isConnected && tournamentId) {
      socketClient.joinTournament(tournamentId);
      return () => {
        socketClient.leaveTournament(tournamentId);
      };
    }
  }, [isConnected, tournamentId]);

  // Subscribe to table when tableId changes
  useEffect(() => {
    if (isConnected && tableId) {
      socketClient.subscribeTable(tableId);
      return () => {
        socketClient.unsubscribeTable(tableId);
      };
    }
  }, [isConnected, tableId]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
    joinTournament: socketClient.joinTournament.bind(socketClient),
    leaveTournament: socketClient.leaveTournament.bind(socketClient),
    subscribeTable: socketClient.subscribeTable.bind(socketClient),
    unsubscribeTable: socketClient.unsubscribeTable.bind(socketClient),
  };
}
