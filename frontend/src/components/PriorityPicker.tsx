"use client";

import { PRIORITY_CONFIG, PriorityLevel } from "@/lib/api";

interface PriorityPickerProps {
  value: number;
  onChange: (priority: number) => void;
  disabled?: boolean;
  compact?: boolean;
}

/**
 * Priority picker component for selecting task priority levels.
 *
 * Priority levels:
 * - 1: Critical (Red)
 * - 2: High (Orange)
 * - 3: Medium (Yellow) - Default
 * - 4: Low (Green)
 * - 5: None (Gray)
 */
export function PriorityPicker({
  value,
  onChange,
  disabled = false,
  compact = false,
}: PriorityPickerProps) {
  const priorities = Object.entries(PRIORITY_CONFIG).map(([level, config]) => ({
    level: Number(level) as PriorityLevel,
    ...config,
  }));

  if (compact) {
    // Compact mode: Dropdown select
    return (
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm px-3 py-2 border"
      >
        {priorities.map((p) => (
          <option key={p.level} value={p.level}>
            {p.label}
          </option>
        ))}
      </select>
    );
  }

  // Full mode: Button group
  return (
    <div className="flex flex-wrap gap-2">
      {priorities.map((p) => {
        const isSelected = value === p.level;
        return (
          <button
            key={p.level}
            type="button"
            onClick={() => onChange(p.level)}
            disabled={disabled}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-full transition-all
              ${isSelected
                ? `${p.bgColor} ${p.textColor} ring-2 ring-offset-1`
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
            style={isSelected ? { ringColor: p.color } : undefined}
          >
            <span
              className="inline-block w-2 h-2 rounded-full mr-1.5"
              style={{ backgroundColor: p.color }}
            />
            {p.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Priority badge component for displaying priority in task lists.
 */
interface PriorityBadgeProps {
  priority: number;
  showLabel?: boolean;
}

export function PriorityBadge({ priority, showLabel = true }: PriorityBadgeProps) {
  const config = PRIORITY_CONFIG[priority as PriorityLevel] || PRIORITY_CONFIG[3];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full mr-1"
        style={{ backgroundColor: config.color }}
      />
      {showLabel && config.label}
    </span>
  );
}
