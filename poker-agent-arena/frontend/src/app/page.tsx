"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useOnboardingStore } from "@/stores/onboardingStore";

export default function Home() {
  const router = useRouter();
  const { isOnboardingComplete } = useOnboardingStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      if (isOnboardingComplete) {
        router.replace('/tournaments');
      } else {
        router.replace('/onboarding');
      }
    }
  }, [mounted, isOnboardingComplete, router]);

  // Loading state while checking onboarding
  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
