"use client";

import { useState } from "react";

export interface ReminderInput {
  remind_at: string;
  message?: string;
}

interface ReminderPickerProps {
  value: ReminderInput[];
  onChange: (reminders: ReminderInput[]) => void;
  dueDate?: string | null; // For quick options relative to due date
  disabled?: boolean;
  maxReminders?: number;
}

const QUICK_OPTIONS = [
  { label: "30 min before", minutes: -30 },
  { label: "1 hour before", minutes: -60 },
  { label: "1 day before", minutes: -1440 },
] as const;

export function ReminderPicker({
  value,
  onChange,
  dueDate,
  disabled,
  maxReminders = 3,
}: ReminderPickerProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [newDateTime, setNewDateTime] = useState("");
  const [newMessage, setNewMessage] = useState("");

  const canAddMore = value.length < maxReminders;

  const handleAddReminder = () => {
    if (!newDateTime) return;

    const newReminder: ReminderInput = {
      remind_at: newDateTime,
      message: newMessage.trim() || undefined,
    };

    onChange([...value, newReminder]);
    setNewDateTime("");
    setNewMessage("");
    setShowAdd(false);
  };

  const handleRemoveReminder = (index: number) => {
    const updated = value.filter((_, i) => i !== index);
    onChange(updated);
  };

  const handleQuickOption = (minutesBefore: number) => {
    if (!dueDate) return;

    const due = new Date(dueDate);
    const reminderTime = new Date(due.getTime() + minutesBefore * 60 * 1000);

    // Don't add if reminder time is in the past
    if (reminderTime <= new Date()) return;

    const newReminder: ReminderInput = {
      remind_at: reminderTime.toISOString().slice(0, 16),
    };

    onChange([...value, newReminder]);
  };

  const formatDateTime = (dateTimeStr: string) => {
    const date = new Date(dateTimeStr);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // Get minimum datetime (now + 1 minute)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 1);
    return now.toISOString().slice(0, 16);
  };

  return (
    <div className="space-y-3">
      {/* Existing Reminders */}
      {value.length > 0 && (
        <div className="space-y-2">
          {value.map((reminder, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-2 bg-yellow-50 border border-yellow-200 rounded-md"
            >
              <div className="flex items-center gap-2">
                <svg
                  className="w-4 h-4 text-yellow-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <div>
                  <div className="text-sm font-medium text-gray-700">
                    {formatDateTime(reminder.remind_at)}
                  </div>
                  {reminder.message && (
                    <div className="text-xs text-gray-500">{reminder.message}</div>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleRemoveReminder(index)}
                disabled={disabled}
                className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50"
                title="Remove reminder"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Quick Options (only if due date is set) */}
      {dueDate && canAddMore && (
        <div className="flex flex-wrap gap-2">
          {QUICK_OPTIONS.map((option) => {
            const due = new Date(dueDate);
            const reminderTime = new Date(due.getTime() + option.minutes * 60 * 1000);
            const isValid = reminderTime > new Date();

            return (
              <button
                key={option.label}
                type="button"
                onClick={() => handleQuickOption(option.minutes)}
                disabled={disabled || !isValid}
                className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                title={isValid ? `Set reminder for ${formatDateTime(reminderTime.toISOString())}` : "Time is in the past"}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Add Reminder Form */}
      {showAdd && canAddMore && (
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-md space-y-2">
          <div>
            <label className="block text-xs text-gray-600 mb-1">
              When to remind
            </label>
            <input
              type="datetime-local"
              value={newDateTime}
              onChange={(e) => setNewDateTime(e.target.value)}
              min={getMinDateTime()}
              disabled={disabled}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">
              Message (optional)
            </label>
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Reminder message..."
              maxLength={255}
              disabled={disabled}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleAddReminder}
              disabled={disabled || !newDateTime}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAdd(false);
                setNewDateTime("");
                setNewMessage("");
              }}
              disabled={disabled}
              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Add Button */}
      {!showAdd && canAddMore && (
        <button
          type="button"
          onClick={() => setShowAdd(true)}
          disabled={disabled}
          className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded disabled:opacity-50"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Reminder
        </button>
      )}

      {/* Max reached message */}
      {!canAddMore && (
        <p className="text-xs text-gray-500">
          Maximum {maxReminders} reminders per task
        </p>
      )}
    </div>
  );
}
