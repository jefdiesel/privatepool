'use client';

import { useState, useCallback, useEffect } from 'react';
import SliderControl from './SliderControl';

export interface LiveSettings {
  activeAggression: number;
  activeTightness: number;
  pendingAggression: number | null;
  pendingTightness: number | null;
  confirmedAggression: number | null;
  confirmedTightness: number | null;
  confirmedAt: string | null;
}

interface SettingsPanelProps {
  settings: LiveSettings;
  tier: 'basic' | 'pro';
  isLoading?: boolean;
  onUpdate: (aggression: number, tightness: number) => Promise<void>;
  onConfirm: () => Promise<void>;
}

export default function SettingsPanel({
  settings,
  tier,
  isLoading = false,
  onUpdate,
  onConfirm,
}: SettingsPanelProps) {
  // Local state for slider values (allows dragging without API calls)
  const [localAggression, setLocalAggression] = useState(
    settings.pendingAggression ?? settings.activeAggression
  );
  const [localTightness, setLocalTightness] = useState(
    settings.pendingTightness ?? settings.activeTightness
  );
  const [isUpdating, setIsUpdating] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  // Update local state when settings change externally
  useEffect(() => {
    setLocalAggression(settings.pendingAggression ?? settings.activeAggression);
    setLocalTightness(settings.pendingTightness ?? settings.activeTightness);
  }, [settings]);

  // Check if there are unsaved changes
  const hasUnsavedChanges =
    localAggression !== (settings.pendingAggression ?? settings.activeAggression) ||
    localTightness !== (settings.pendingTightness ?? settings.activeTightness);

  // Check if there are pending (but unconfirmed) changes
  const hasPendingChanges =
    settings.pendingAggression !== null || settings.pendingTightness !== null;

  // Check if changes are confirmed and waiting for next hand
  const isWaitingForNextHand =
    settings.confirmedAggression !== null || settings.confirmedTightness !== null;

  // Debounced update handler
  const handleUpdate = useCallback(async () => {
    if (!hasUnsavedChanges) return;

    setIsUpdating(true);
    try {
      await onUpdate(localAggression, localTightness);
    } catch (error) {
      console.error('Failed to update settings:', error);
    } finally {
      setIsUpdating(false);
    }
  }, [hasUnsavedChanges, localAggression, localTightness, onUpdate]);

  // Update on mouse/touch release
  const handleSliderRelease = useCallback(() => {
    if (hasUnsavedChanges) {
      handleUpdate();
    }
  }, [hasUnsavedChanges, handleUpdate]);

  // Confirm handler
  const handleConfirm = useCallback(async () => {
    // First save any unsaved changes
    if (hasUnsavedChanges) {
      await handleUpdate();
    }

    setIsConfirming(true);
    try {
      await onConfirm();
    } catch (error) {
      console.error('Failed to confirm settings:', error);
    } finally {
      setIsConfirming(false);
    }
  }, [hasUnsavedChanges, handleUpdate, onConfirm]);

  // Check if values differ from active
  const hasChanges =
    localAggression !== settings.activeAggression ||
    localTightness !== settings.activeTightness;

  return (
    <div className="bg-slate-800 rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Agent Settings</h3>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            tier === 'pro'
              ? 'bg-purple-500/20 text-purple-300'
              : 'bg-blue-500/20 text-blue-300'
          }`}
        >
          {tier.toUpperCase()} Tier
        </span>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin h-6 w-6 border-2 border-slate-500 border-t-white rounded-full" />
        </div>
      ) : (
        <>
          <div className="space-y-6">
            <SliderControl
              label="Aggression"
              description="How your agent plays hands - betting/raising vs checking/calling"
              minLabel="Passive"
              maxLabel="Aggressive"
              value={localAggression}
              activeValue={settings.activeAggression}
              onChange={setLocalAggression}
              disabled={isUpdating || isConfirming}
            />

            <SliderControl
              label="Tightness"
              description="Hand selection - how many different starting hands to play"
              minLabel="Loose"
              maxLabel="Tight"
              value={localTightness}
              activeValue={settings.activeTightness}
              onChange={setLocalTightness}
              disabled={isUpdating || isConfirming}
            />
          </div>

          {/* Status indicator */}
          <div className="text-sm text-center py-2">
            {isWaitingForNextHand ? (
              <span className="text-green-400 animate-pulse">
                Changes will take effect next hand
              </span>
            ) : hasPendingChanges || hasUnsavedChanges ? (
              <span className="text-amber-400">Unsaved changes</span>
            ) : (
              <span className="text-slate-500">Current settings active</span>
            )}
          </div>

          {/* Confirm button */}
          <button
            onClick={handleConfirm}
            disabled={
              isConfirming ||
              isUpdating ||
              isWaitingForNextHand ||
              (!hasChanges && !hasPendingChanges && !hasUnsavedChanges)
            }
            className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
              isWaitingForNextHand
                ? 'bg-green-500/20 text-green-400 cursor-not-allowed'
                : hasChanges || hasPendingChanges || hasUnsavedChanges
                ? 'bg-green-600 hover:bg-green-500 text-white'
                : 'bg-slate-700 text-slate-400 cursor-not-allowed'
            }`}
          >
            {isConfirming ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full" />
                Confirming...
              </span>
            ) : isWaitingForNextHand ? (
              'Waiting for next hand...'
            ) : (
              'Confirm Changes'
            )}
          </button>

          {/* Help text */}
          <p className="text-xs text-slate-500 text-center">
            Changes take effect at the start of the next hand
          </p>
        </>
      )}
    </div>
  );
}
