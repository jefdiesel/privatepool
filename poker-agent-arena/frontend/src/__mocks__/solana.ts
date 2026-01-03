/**
 * Mock implementations for Solana wallet adapter and web3.js
 * Used for testing components that interact with Solana wallets
 */

import { PublicKey } from '@solana/web3.js';

// Mock public key for testing
export const MOCK_PUBLIC_KEY = new PublicKey('11111111111111111111111111111111');
export const MOCK_PUBLIC_KEY_STRING = MOCK_PUBLIC_KEY.toBase58();

// Mock wallet adapter state
export interface MockWalletState {
  connected: boolean;
  connecting: boolean;
  disconnecting: boolean;
  publicKey: PublicKey | null;
  wallet: MockWallet | null;
}

// Mock wallet interface
export interface MockWallet {
  adapter: MockWalletAdapter;
  readyState: 'Installed' | 'NotDetected' | 'Loadable' | 'Unsupported';
}

// Mock wallet adapter interface
export interface MockWalletAdapter {
  name: string;
  url: string;
  icon: string;
  publicKey: PublicKey | null;
  connecting: boolean;
  connected: boolean;
  connect: jest.Mock;
  disconnect: jest.Mock;
  sendTransaction: jest.Mock;
  signTransaction: jest.Mock;
  signAllTransactions: jest.Mock;
  signMessage: jest.Mock;
}

// Create a mock wallet adapter
export function createMockWalletAdapter(overrides?: Partial<MockWalletAdapter>): MockWalletAdapter {
  return {
    name: 'Mock Wallet',
    url: 'https://mockwallet.com',
    icon: 'data:image/svg+xml;base64,...',
    publicKey: MOCK_PUBLIC_KEY,
    connecting: false,
    connected: true,
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn().mockResolvedValue(undefined),
    sendTransaction: jest.fn().mockResolvedValue('mock-transaction-signature'),
    signTransaction: jest.fn().mockImplementation((tx) => Promise.resolve(tx)),
    signAllTransactions: jest.fn().mockImplementation((txs) => Promise.resolve(txs)),
    signMessage: jest.fn().mockResolvedValue(new Uint8Array(64).fill(1)),
    ...overrides,
  };
}

// Create a mock wallet
export function createMockWallet(overrides?: Partial<MockWallet>): MockWallet {
  return {
    adapter: createMockWalletAdapter(),
    readyState: 'Installed',
    ...overrides,
  };
}

// Default mock wallet state
export function createMockWalletState(overrides?: Partial<MockWalletState>): MockWalletState {
  return {
    connected: true,
    connecting: false,
    disconnecting: false,
    publicKey: MOCK_PUBLIC_KEY,
    wallet: createMockWallet(),
    ...overrides,
  };
}

// Mock useWallet hook return value
export function createMockUseWalletReturn(overrides?: Partial<MockWalletState>) {
  const state = createMockWalletState(overrides);
  const adapter = state.wallet?.adapter;

  return {
    autoConnect: false,
    wallets: [createMockWallet()],
    wallet: state.wallet,
    publicKey: state.publicKey,
    connected: state.connected,
    connecting: state.connecting,
    disconnecting: state.disconnecting,
    select: jest.fn(),
    connect: adapter?.connect ?? jest.fn(),
    disconnect: adapter?.disconnect ?? jest.fn(),
    sendTransaction: adapter?.sendTransaction ?? jest.fn(),
    signTransaction: adapter?.signTransaction ?? jest.fn(),
    signAllTransactions: adapter?.signAllTransactions ?? jest.fn(),
    signMessage: adapter?.signMessage ?? jest.fn(),
  };
}

// Mock useConnection hook return value
export function createMockUseConnectionReturn() {
  return {
    connection: {
      rpcEndpoint: 'https://api.devnet.solana.com',
      commitment: 'confirmed',
      getBalance: jest.fn().mockResolvedValue(1000000000), // 1 SOL in lamports
      getLatestBlockhash: jest.fn().mockResolvedValue({
        blockhash: 'mock-blockhash-123',
        lastValidBlockHeight: 123456789,
      }),
      confirmTransaction: jest.fn().mockResolvedValue({ value: { err: null } }),
      sendRawTransaction: jest.fn().mockResolvedValue('mock-tx-signature'),
      getAccountInfo: jest.fn().mockResolvedValue(null),
      getProgramAccounts: jest.fn().mockResolvedValue([]),
    },
  };
}

// Mock WalletContextProvider for testing
export const mockWalletContextValue = {
  ...createMockUseWalletReturn(),
};

// Mock ConnectionContext for testing
export const mockConnectionContextValue = {
  ...createMockUseConnectionReturn(),
};

// Helper to create disconnected wallet state
export function createDisconnectedWalletState(): MockWalletState {
  return createMockWalletState({
    connected: false,
    publicKey: null,
    wallet: null,
  });
}

// Helper to create connecting wallet state
export function createConnectingWalletState(): MockWalletState {
  return createMockWalletState({
    connected: false,
    connecting: true,
    publicKey: null,
  });
}

// Jest mock factory for @solana/wallet-adapter-react
export const mockWalletAdapterReact = {
  useWallet: jest.fn(() => createMockUseWalletReturn()),
  useConnection: jest.fn(() => createMockUseConnectionReturn()),
  WalletProvider: ({ children }: { children: React.ReactNode }) => children,
  ConnectionProvider: ({ children }: { children: React.ReactNode }) => children,
};

// Export for use in tests
export default mockWalletAdapterReact;
