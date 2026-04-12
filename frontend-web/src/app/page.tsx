"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { A2UIInterruptHandler } from "@/components/a2ui/A2UIInterruptHandler";
import { OnboardingWelcome } from "@/components/OnboardingWelcome";
import { Toaster } from "@/components/ui/sonner";
import React from "react";

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <OnboardingWelcome>
        <ThreadProvider>
          <StreamProvider>
            <ArtifactProvider>
              <Thread />
              <A2UIInterruptHandler />
            </ArtifactProvider>
          </StreamProvider>
        </ThreadProvider>
      </OnboardingWelcome>
    </React.Suspense>
  );
}
