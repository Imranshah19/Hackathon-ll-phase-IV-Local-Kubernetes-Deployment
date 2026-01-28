"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Tag, api } from "@/lib/api";

interface TagPickerProps {
  selectedTagIds: string[];
  onChange: (tagIds: string[]) => void;
  availableTags: Tag[];
  onCreateTag?: (name: string) => Promise<Tag>;
  disabled?: boolean;
}

/**
 * Tag picker component with autocomplete and tag creation.
 *
 * Allows selecting existing tags or creating new ones on the fly.
 */
export function TagPicker({
  selectedTagIds,
  onChange,
  availableTags,
  onCreateTag,
  disabled = false,
}: TagPickerProps) {
  const [inputValue, setInputValue] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<Tag[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Filter suggestions based on input
  useEffect(() => {
    if (!inputValue.trim()) {
      setSuggestions(availableTags.filter((t) => !selectedTagIds.includes(t.id)));
    } else {
      const filtered = availableTags.filter(
        (t) =>
          t.name.toLowerCase().includes(inputValue.toLowerCase()) &&
          !selectedTagIds.includes(t.id)
      );
      setSuggestions(filtered);
    }
  }, [inputValue, availableTags, selectedTagIds]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectTag = (tag: Tag) => {
    onChange([...selectedTagIds, tag.id]);
    setInputValue("");
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleRemoveTag = (tagId: string) => {
    onChange(selectedTagIds.filter((id) => id !== tagId));
  };

  const handleCreateTag = async () => {
    if (!onCreateTag || !inputValue.trim()) return;

    try {
      const newTag = await onCreateTag(inputValue.trim());
      onChange([...selectedTagIds, newTag.id]);
      setInputValue("");
      setIsOpen(false);
    } catch (err) {
      console.error("Failed to create tag:", err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      if (suggestions.length > 0) {
        handleSelectTag(suggestions[0]);
      } else if (inputValue.trim() && onCreateTag) {
        handleCreateTag();
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    } else if (e.key === "Backspace" && !inputValue && selectedTagIds.length > 0) {
      handleRemoveTag(selectedTagIds[selectedTagIds.length - 1]);
    }
  };

  const selectedTags = availableTags.filter((t) => selectedTagIds.includes(t.id));
  const showCreateOption =
    inputValue.trim() &&
    onCreateTag &&
    !availableTags.some((t) => t.name.toLowerCase() === inputValue.toLowerCase());

  return (
    <div ref={containerRef} className="relative">
      <div
        className={`
          flex flex-wrap items-center gap-2 min-h-[42px] p-2 rounded-md border
          ${disabled ? "bg-gray-100" : "bg-white"}
          ${isOpen ? "border-blue-500 ring-2 ring-blue-200" : "border-gray-300"}
        `}
        onClick={() => inputRef.current?.focus()}
      >
        {/* Selected Tags */}
        {selectedTags.map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center px-2 py-1 rounded-full text-sm"
            style={{ backgroundColor: tag.color + "20", color: tag.color }}
          >
            <span
              className="w-2 h-2 rounded-full mr-1.5"
              style={{ backgroundColor: tag.color }}
            />
            {tag.name}
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveTag(tag.id);
                }}
                className="ml-1 hover:text-red-500"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </span>
        ))}

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={selectedTags.length === 0 ? "Add tags..." : ""}
          className="flex-1 min-w-[100px] outline-none text-sm bg-transparent"
        />
      </div>

      {/* Dropdown */}
      {isOpen && (suggestions.length > 0 || showCreateOption) && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
          {suggestions.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => handleSelectTag(tag)}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center"
            >
              <span
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: tag.color }}
              />
              {tag.name}
              <span className="ml-auto text-xs text-gray-400">
                {tag.task_count} tasks
              </span>
            </button>
          ))}

          {showCreateOption && (
            <button
              type="button"
              onClick={handleCreateTag}
              className="w-full px-3 py-2 text-left text-sm hover:bg-blue-50 text-blue-600 flex items-center border-t"
            >
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create "{inputValue}"
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Simple tag badge for display purposes.
 */
interface TagBadgeProps {
  tag: { name: string; color: string };
  onClick?: () => void;
  removable?: boolean;
  onRemove?: () => void;
}

export function TagBadge({ tag, onClick, removable, onRemove }: TagBadgeProps) {
  return (
    <span
      onClick={onClick}
      className={`
        inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
        ${onClick ? "cursor-pointer hover:opacity-80" : ""}
      `}
      style={{
        backgroundColor: tag.color + "20",
        color: tag.color,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full mr-1"
        style={{ backgroundColor: tag.color }}
      />
      {tag.name}
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-1 hover:text-red-500"
        >
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  );
}
