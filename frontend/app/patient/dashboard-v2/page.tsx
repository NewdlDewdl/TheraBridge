'use client';

import { useState } from 'react';
import DashboardMockupSerene from './mockup-1-serene';
import DashboardMockupWarmGrid from './mockup-2-warm-grid';

/**
 * Dashboard Mockup Viewer
 *
 * View both dashboard design prototypes:
 * - Mockup 1: "Serene Analytics" - Refined minimalism with soft gradients
 * - Mockup 2: "Warm Grid" - Masonry-style with warmer, approachable colors
 *
 * Toggle between them to compare layouts, color schemes, and data presentation
 */

export default function DashboardMockupsPage() {
  const [activeView, setActiveView] = useState<'serene' | 'warm'>('serene');

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Toggle Controls - Fixed at top */}
      <div className="sticky top-0 z-50 bg-gray-900 border-b border-gray-700 shadow-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">Dashboard Prototypes</h1>
              <p className="text-sm text-gray-400">Compare two dashboard design approaches</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setActiveView('serene')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  activeView === 'serene'
                    ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/50'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                Mockup 1: Serene Analytics
              </button>
              <button
                onClick={() => setActiveView('warm')}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  activeView === 'warm'
                    ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/50'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                Mockup 2: Warm Grid
              </button>
            </div>
          </div>

          {/* Design Details */}
          <div className="mt-4 p-4 bg-gray-800 rounded-lg">
            {activeView === 'serene' ? (
              <div className="text-sm text-gray-300 space-y-1">
                <p className="font-semibold text-white mb-2">Mockup 1: "Serene Analytics"</p>
                <ul className="space-y-1 text-gray-400">
                  <li>• <strong>Style:</strong> Refined minimalism with generous spacing</li>
                  <li>• <strong>Colors:</strong> Soft teal (#5AB9B4), warm lavender (#B8A5D6), gentle coral (#F4A69D)</li>
                  <li>• <strong>Typography:</strong> Crimson Pro (serif headings) + Inter (body)</li>
                  <li>• <strong>Layout:</strong> 2-column clinical progress card + stats, vertical timeline, stacked sections</li>
                  <li>• <strong>Vibe:</strong> Editorial, calm, clinical-but-warm, trust-building</li>
                </ul>
              </div>
            ) : (
              <div className="text-sm text-gray-300 space-y-1">
                <p className="font-semibold text-white mb-2">Mockup 2: "Warm Grid"</p>
                <ul className="space-y-1 text-gray-400">
                  <li>• <strong>Style:</strong> Masonry grid with organic card sizes, compact spacing</li>
                  <li>• <strong>Colors:</strong> Warm peach (#FFB499), sage green (#A8C69F), soft blue (#8FB8DE)</li>
                  <li>• <strong>Typography:</strong> DM Sans (rounded, friendly) + Space Mono (data)</li>
                  <li>• <strong>Layout:</strong> Responsive grid, session cards as individual tiles, timeline at bottom</li>
                  <li>• <strong>Vibe:</strong> Approachable, warmer, more casual, encouraging</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard Preview */}
      <div className="transition-opacity duration-300">
        {activeView === 'serene' ? <DashboardMockupSerene /> : <DashboardMockupWarmGrid />}
      </div>

      {/* Bottom Instructions */}
      <div className="bg-gray-900 border-t border-gray-700 py-8">
        <div className="max-w-4xl mx-auto px-6 text-center text-gray-400 space-y-3">
          <p className="text-sm">
            <strong className="text-white">Next steps:</strong> Choose your preferred design or identify elements to combine from both.
          </p>
          <p className="text-xs">
            These are interactive prototypes with real React components. Session cards are clickable and will route to full session detail pages when implemented.
          </p>
        </div>
      </div>
    </div>
  );
}
