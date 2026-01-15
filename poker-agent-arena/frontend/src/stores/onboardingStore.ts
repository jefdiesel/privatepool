/**
 * Onboarding flow state store using Zustand
 * Manages the user's progress through the initial setup flow
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AgentTier = 'FREE' | 'BASIC' | 'PRO';

interface OnboardingState {
  // Flow state
  hasAgreedToTOS: boolean;
  selectedTier: AgentTier | null;
  agentName: string;
  agentImageUrl: string | null;
  isOnboardingComplete: boolean;

  // Current step tracking
  currentStep: 'home' | 'tos' | 'tier' | 'agent' | 'complete';

  // Actions
  agreeTOS: () => void;
  selectTier: (tier: AgentTier) => void;
  setAgentName: (name: string) => void;
  setAgentImage: (url: string | null) => void;
  completeOnboarding: () => void;
  setCurrentStep: (step: OnboardingState['currentStep']) => void;
  resetOnboarding: () => void;
}

const initialState = {
  hasAgreedToTOS: false,
  selectedTier: null,
  agentName: '',
  agentImageUrl: null,
  isOnboardingComplete: false,
  currentStep: 'home' as const,
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      ...initialState,

      agreeTOS: () => set({ hasAgreedToTOS: true, currentStep: 'tier' }),

      selectTier: (tier) => set({ selectedTier: tier, currentStep: 'agent' }),

      setAgentName: (name) => set({ agentName: name }),

      setAgentImage: (url) => set({ agentImageUrl: url }),

      completeOnboarding: () => set({ isOnboardingComplete: true, currentStep: 'complete' }),

      setCurrentStep: (step) => set({ currentStep: step }),

      resetOnboarding: () => set(initialState),
    }),
    {
      name: 'fap-onboarding',
      partialize: (state) => ({
        hasAgreedToTOS: state.hasAgreedToTOS,
        selectedTier: state.selectedTier,
        agentName: state.agentName,
        agentImageUrl: state.agentImageUrl,
        isOnboardingComplete: state.isOnboardingComplete,
      }),
    }
  )
);

// Selectors
export const selectIsOnboardingComplete = (state: OnboardingState) => state.isOnboardingComplete;
export const selectSelectedTier = (state: OnboardingState) => state.selectedTier;
export const selectAgentName = (state: OnboardingState) => state.agentName;
