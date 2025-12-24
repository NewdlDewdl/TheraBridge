'use client';

/**
 * Demo Transcript Uploader
 * Allows uploading pre-selected JSON transcripts from mock-therapy-data
 */

import { useState } from 'react';
import { demoApiClient } from '@/lib/demo-api-client';
import { useProcessing } from '@/contexts/ProcessingContext';

const DEMO_TRANSCRIPTS = [
  {
    filename: 'session_12_thriving.json',
    label: 'Session 12: Thriving',
    description: 'Final session showing sustained progress and thriving',
  },
  {
    filename: 'session_11_rebuilding.json',
    label: 'Session 11: Rebuilding',
    description: 'Rebuilding after coming out, strengthening resilience',
  },
];

interface DemoTranscriptUploaderProps {
  onUploadSuccess?: (sessionId: string) => void;
}

export default function DemoTranscriptUploader({ onUploadSuccess }: DemoTranscriptUploaderProps) {
  const [selectedTranscript, setSelectedTranscript] = useState(DEMO_TRANSCRIPTS[0].filename);
  const [isUploading, setIsUploading] = useState(false);
  const { startTracking } = useProcessing();

  const handleUpload = async () => {
    setIsUploading(true);

    try {
      const result = await demoApiClient.uploadDemoTranscript(selectedTranscript);

      if (result) {
        console.log('[Demo Upload] ✓ Session created:', result.session_id);

        // Start tracking processing status
        startTracking(result.session_id);

        // Notify parent component
        onUploadSuccess?.(result.session_id);
      } else {
        alert('Failed to upload demo transcript. Please try again.');
      }
    } catch (error) {
      console.error('[Demo Upload] Error:', error);
      alert('An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const selectedInfo = DEMO_TRANSCRIPTS.find(t => t.filename === selectedTranscript);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-[#1a1625] border-2 border-dashed border-[#5AB9B4] dark:border-[#a78bfa] rounded-xl p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-[#5AB9B4] dark:text-[#a78bfa]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <h3 className="text-xl font-light text-gray-900 dark:text-gray-100 mb-2">
            Upload Demo Session
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Select a pre-loaded therapy transcript to showcase AI analysis
          </p>
        </div>

        {/* Transcript Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Session
          </label>
          <select
            value={selectedTranscript}
            onChange={(e) => setSelectedTranscript(e.target.value)}
            disabled={isUploading}
            className="w-full px-4 py-3 bg-gray-50 dark:bg-[#2d2438] border border-gray-300 dark:border-[#3d3548] rounded-lg text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[#5AB9B4] dark:focus:ring-[#a78bfa] focus:border-transparent transition-all disabled:opacity-50"
          >
            {DEMO_TRANSCRIPTS.map((transcript) => (
              <option key={transcript.filename} value={transcript.filename}>
                {transcript.label}
              </option>
            ))}
          </select>

          {/* Description */}
          {selectedInfo && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              {selectedInfo.description}
            </p>
          )}
        </div>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full py-3 px-6 bg-[#5AB9B4] dark:bg-[#a78bfa] hover:bg-[#4a9a95] dark:hover:bg-[#9370db] text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Uploading...
            </span>
          ) : (
            'Upload & Analyze'
          )}
        </button>

        {/* Info Banner */}
        <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-xs text-blue-700 dark:text-blue-300">
            <strong>Demo Mode:</strong> This will create a new session and run real AI analysis (mood, topics, breakthroughs). Processing takes ~10 seconds.
          </p>
        </div>
      </div>
    </div>
  );
}
