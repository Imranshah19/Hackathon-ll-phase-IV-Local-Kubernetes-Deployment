"use client";

/**
 * FallbackCLI component for displaying CLI command suggestions.
 *
 * Shown when AI interpretation has low confidence or fails.
 * Provides a copyable CLI command for direct execution.
 */

import { useState } from "react";

interface FallbackCLIProps {
  command: string;
  message?: string;
}

export function FallbackCLI({ command, message }: FallbackCLIProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
      {message && (
        <p className="text-sm text-amber-800 dark:text-amber-200 mb-2">
          {message}
        </p>
      )}
      <div className="flex items-center justify-between gap-2 bg-gray-900 dark:bg-black rounded p-2">
        <code className="text-sm text-green-400 font-mono overflow-x-auto">
          {command}
        </code>
        <button
          onClick={handleCopy}
          className="flex-shrink-0 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600
                     text-gray-200 rounded transition-colors"
          title="Copy to clipboard"
        >
          {copied ? (
            <span className="text-green-400">Copied!</span>
          ) : (
            <CopyIcon />
          )}
        </button>
      </div>
      <p className="text-xs text-amber-700 dark:text-amber-300 mt-2">
        Run this command in your terminal to execute directly.
      </p>
    </div>
  );
}

function CopyIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
    </svg>
  );
}

export default FallbackCLI;
