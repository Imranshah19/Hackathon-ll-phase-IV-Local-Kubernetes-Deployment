"use client";

import { useState } from "react";
import { RecurrenceInput, RecurrenceFrequency, RecurrenceEndType } from "@/lib/api";

interface RecurrencePickerProps {
  value: RecurrenceInput | null;
  onChange: (recurrence: RecurrenceInput | null) => void;
  disabled?: boolean;
}

const FREQUENCY_OPTIONS: { value: RecurrenceFrequency; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

const END_TYPE_OPTIONS: { value: RecurrenceEndType; label: string }[] = [
  { value: "never", label: "Never" },
  { value: "count", label: "After X times" },
  { value: "date", label: "On date" },
];

export function RecurrencePicker({ value, onChange, disabled }: RecurrencePickerProps) {
  const [isEnabled, setIsEnabled] = useState(value !== null);
  const [frequency, setFrequency] = useState<RecurrenceFrequency>(value?.frequency || "daily");
  const [interval, setInterval] = useState(value?.interval || 1);
  const [endType, setEndType] = useState<RecurrenceEndType>(value?.end_type || "never");
  const [endCount, setEndCount] = useState(value?.end_count || 5);
  const [endDate, setEndDate] = useState(value?.end_date || "");

  const handleToggle = (enabled: boolean) => {
    setIsEnabled(enabled);
    if (enabled) {
      updateValue(frequency, interval, endType, endCount, endDate);
    } else {
      onChange(null);
    }
  };

  const updateValue = (
    freq: RecurrenceFrequency,
    int: number,
    end: RecurrenceEndType,
    count: number,
    date: string
  ) => {
    const newValue: RecurrenceInput = {
      frequency: freq,
      interval: int,
      end_type: end,
    };
    if (end === "count") {
      newValue.end_count = count;
    } else if (end === "date" && date) {
      newValue.end_date = date;
    }
    onChange(newValue);
  };

  const handleFrequencyChange = (freq: RecurrenceFrequency) => {
    setFrequency(freq);
    if (isEnabled) {
      updateValue(freq, interval, endType, endCount, endDate);
    }
  };

  const handleIntervalChange = (int: number) => {
    setInterval(int);
    if (isEnabled) {
      updateValue(frequency, int, endType, endCount, endDate);
    }
  };

  const handleEndTypeChange = (end: RecurrenceEndType) => {
    setEndType(end);
    if (isEnabled) {
      updateValue(frequency, interval, end, endCount, endDate);
    }
  };

  const handleEndCountChange = (count: number) => {
    setEndCount(count);
    if (isEnabled && endType === "count") {
      updateValue(frequency, interval, endType, count, endDate);
    }
  };

  const handleEndDateChange = (date: string) => {
    setEndDate(date);
    if (isEnabled && endType === "date") {
      updateValue(frequency, interval, endType, endCount, date);
    }
  };

  const getIntervalLabel = () => {
    switch (frequency) {
      case "daily":
        return interval === 1 ? "day" : "days";
      case "weekly":
        return interval === 1 ? "week" : "weeks";
      case "monthly":
        return interval === 1 ? "month" : "months";
      case "yearly":
        return interval === 1 ? "year" : "years";
      default:
        return "days";
    }
  };

  return (
    <div className="space-y-3">
      {/* Toggle */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isEnabled}
          onChange={(e) => handleToggle(e.target.checked)}
          disabled={disabled}
          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
        />
        <span className="text-sm font-medium text-gray-700">
          Repeat this task
        </span>
        {isEnabled && (
          <svg
            className="w-4 h-4 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        )}
      </label>

      {/* Recurrence Options */}
      {isEnabled && (
        <div className="pl-6 space-y-3 border-l-2 border-blue-200">
          {/* Frequency and Interval */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-gray-600">Every</span>
            <input
              type="number"
              min={1}
              max={99}
              value={interval}
              onChange={(e) => handleIntervalChange(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={disabled}
              className="w-16 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            />
            <select
              value={frequency}
              onChange={(e) => handleFrequencyChange(e.target.value as RecurrenceFrequency)}
              disabled={disabled}
              className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            >
              {FREQUENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {interval === 1 ? opt.label.replace(/ly$/, "") : opt.label.replace(/ly$/, "s")}
                </option>
              ))}
            </select>
          </div>

          {/* End Condition */}
          <div className="space-y-2">
            <span className="text-sm text-gray-600">Ends</span>
            <div className="flex flex-col gap-2">
              {END_TYPE_OPTIONS.map((opt) => (
                <label key={opt.value} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="endType"
                    value={opt.value}
                    checked={endType === opt.value}
                    onChange={() => handleEndTypeChange(opt.value)}
                    disabled={disabled}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{opt.label}</span>

                  {/* Count input */}
                  {opt.value === "count" && endType === "count" && (
                    <input
                      type="number"
                      min={1}
                      max={999}
                      value={endCount}
                      onChange={(e) => handleEndCountChange(Math.max(1, parseInt(e.target.value) || 1))}
                      disabled={disabled}
                      className="w-16 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}

                  {/* Date input */}
                  {opt.value === "date" && endType === "date" && (
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => handleEndDateChange(e.target.value)}
                      disabled={disabled}
                      min={new Date().toISOString().split("T")[0]}
                      className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Summary */}
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
            Repeats every {interval} {getIntervalLabel()}
            {endType === "count" && `, ${endCount} times`}
            {endType === "date" && endDate && `, until ${new Date(endDate).toLocaleDateString()}`}
            {endType === "never" && ", forever"}
          </div>
        </div>
      )}
    </div>
  );
}
