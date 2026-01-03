/**
 * Tests for useSocket hook
 */

import { renderHook, act } from '@testing-library/react';
import { useSocket } from '@/hooks/useSocket';

// Mock api module
jest.mock('@/lib/api', () => ({
  getSessionToken: jest.fn(),
}));

// Mock socket client
jest.mock('@/lib/socket', () => ({
  socketClient: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    joinTournament: jest.fn(),
    leaveTournament: jest.fn(),
    subscribeTable: jest.fn(),
    unsubscribeTable: jest.fn(),
  },
}));

import { getSessionToken } from '@/lib/api';
import { socketClient } from '@/lib/socket';

beforeEach(() => {
  jest.clearAllMocks();
});

describe('useSocket', () => {
  describe('initialization', () => {
    it('should not connect when no session token', () => {
      (getSessionToken as jest.Mock).mockReturnValue(null);

      const { result } = renderHook(() => useSocket());

      expect(result.current.isConnected).toBe(false);
      expect(socketClient.connect).not.toHaveBeenCalled();
    });

    it('should auto-connect when session token exists', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');

      renderHook(() => useSocket());

      expect(socketClient.connect).toHaveBeenCalled();
    });

    it('should not auto-connect when autoConnect is false', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');

      renderHook(() => useSocket({ autoConnect: false }));

      expect(socketClient.connect).not.toHaveBeenCalled();
    });
  });

  describe('connection callbacks', () => {
    it('should set isConnected to true on connect', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { result } = renderHook(() => useSocket());

      act(() => {
        onConnectCallback();
      });

      expect(result.current.isConnected).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should set isConnected to false on disconnect', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;
      let onDisconnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
        onDisconnectCallback = callbacks.onDisconnect;
      });

      const { result } = renderHook(() => useSocket());

      act(() => {
        onConnectCallback();
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        onDisconnectCallback();
      });

      expect(result.current.isConnected).toBe(false);
    });

    it('should set error on connection error', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onErrorCallback: (err: Error) => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onErrorCallback = callbacks.onError;
      });

      const { result } = renderHook(() => useSocket());

      act(() => {
        onErrorCallback(new Error('Connection failed'));
      });

      expect(result.current.error).toBe('Connection failed');
    });
  });

  describe('manual connection', () => {
    it('should connect when connect is called', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');

      const { result } = renderHook(() => useSocket({ autoConnect: false }));

      act(() => {
        result.current.connect();
      });

      expect(socketClient.connect).toHaveBeenCalled();
    });

    it('should set error when connecting without token', () => {
      (getSessionToken as jest.Mock).mockReturnValue(null);

      const { result } = renderHook(() => useSocket({ autoConnect: false }));

      act(() => {
        result.current.connect();
      });

      expect(result.current.error).toBe('Not authenticated');
      expect(socketClient.connect).not.toHaveBeenCalled();
    });

    it('should disconnect when disconnect is called', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { result } = renderHook(() => useSocket());

      act(() => {
        onConnectCallback();
      });

      act(() => {
        result.current.disconnect();
      });

      expect(socketClient.disconnect).toHaveBeenCalled();
      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('tournament rooms', () => {
    it('should join tournament when connected and tournamentId provided', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { result } = renderHook(() =>
        useSocket({ tournamentId: 'tournament-123' })
      );

      act(() => {
        onConnectCallback();
      });

      expect(socketClient.joinTournament).toHaveBeenCalledWith('tournament-123');
    });

    it('should leave tournament on unmount', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { unmount } = renderHook(() =>
        useSocket({ tournamentId: 'tournament-123' })
      );

      act(() => {
        onConnectCallback();
      });

      unmount();

      expect(socketClient.leaveTournament).toHaveBeenCalledWith('tournament-123');
    });
  });

  describe('table subscription', () => {
    it('should subscribe to table when connected and tableId provided', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { result } = renderHook(() => useSocket({ tableId: 'table-456' }));

      act(() => {
        onConnectCallback();
      });

      expect(socketClient.subscribeTable).toHaveBeenCalledWith('table-456');
    });

    it('should unsubscribe from table on unmount', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onConnectCallback: () => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onConnectCallback = callbacks.onConnect;
      });

      const { unmount } = renderHook(() => useSocket({ tableId: 'table-456' }));

      act(() => {
        onConnectCallback();
      });

      unmount();

      expect(socketClient.unsubscribeTable).toHaveBeenCalledWith('table-456');
    });
  });

  describe('callback forwarding', () => {
    it('should call custom callbacks when events occur', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');
      let onTableStateCallback: (data: any) => void;

      (socketClient.connect as jest.Mock).mockImplementation((callbacks) => {
        onTableStateCallback = callbacks.onTableState;
      });

      const mockOnTableState = jest.fn();

      renderHook(() =>
        useSocket({
          callbacks: {
            onTableState: mockOnTableState,
          },
        })
      );

      const tableData = { table_id: 'table-1', pot: 500 };

      act(() => {
        onTableStateCallback(tableData);
      });

      expect(mockOnTableState).toHaveBeenCalledWith(tableData);
    });
  });

  describe('cleanup', () => {
    it('should disconnect on unmount', () => {
      (getSessionToken as jest.Mock).mockReturnValue('test-token');

      const { unmount } = renderHook(() => useSocket());

      unmount();

      expect(socketClient.disconnect).toHaveBeenCalled();
    });
  });
});
