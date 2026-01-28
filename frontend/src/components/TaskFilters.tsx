"use client";

import { useState, useEffect } from "react";
import { PRIORITY_CONFIG, PriorityLevel, Tag } from "@/lib/api";

export type FilterStatus = "all" | "pending" | "completed";
export type SortField = "created_at" | "updated_at" | "priority" | "due" | "title";
export type SortOrder = "asc" | "desc";

export interface TaskFilterState {
  status: FilterStatus;
  search: string;
  priorities: number[];
  tagIds: string[];
  dueFrom: string | null;
  dueTo: string | null;
  sortBy: SortField;
  sortOrder: SortOrder;
}

interface TaskFiltersProps {
  onFilterChange: (filters: TaskFilterState) => void;
  taskCounts?: {
    all: number;
    pending: number;
    completed: number;
  };
  availableTags?: Tag[];
  initialFilters?: TaskFilterState;
}

export function TaskFilters({ onFilterChange, taskCounts, availableTags = [], initialFilters }: TaskFiltersProps) {
  const [status, setStatus] = useState<FilterStatus>(initialFilters?.status ?? "all");
  const [search, setSearch] = useState(initialFilters?.search ?? "");
  const [debouncedSearch, setDebouncedSearch] = useState(initialFilters?.search ?? "");
  const [priorities, setPriorities] = useState<number[]>(initialFilters?.priorities ?? []);
  const [tagIds, setTagIds] = useState<string[]>(initialFilters?.tagIds ?? []);
  const [dueFrom, setDueFrom] = useState<string | null>(initialFilters?.dueFrom ?? null);
  const [dueTo, setDueTo] = useState<string | null>(initialFilters?.dueTo ?? null);
  const [sortBy, setSortBy] = useState<SortField>(initialFilters?.sortBy ?? "created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>(initialFilters?.sortOrder ?? "desc");
  // Show advanced if any advanced filters are active
  const [showAdvanced, setShowAdvanced] = useState(
    (initialFilters?.priorities?.length ?? 0) > 0 ||
    (initialFilters?.tagIds?.length ?? 0) > 0 ||
    !!initialFilters?.dueFrom ||
    !!initialFilters?.dueTo ||
    initialFilters?.sortBy !== "created_at" ||
    initialFilters?.sortOrder !== "desc"
  );

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);

    return () => clearTimeout(timer);
  }, [search]);

  // Notify parent when filters change
  useEffect(() => {
    onFilterChange({
      status,
      search: debouncedSearch,
      priorities,
      tagIds,
      dueFrom,
      dueTo,
      sortBy,
      sortOrder,
    });
  }, [status, debouncedSearch, priorities, tagIds, dueFrom, dueTo, sortBy, sortOrder, onFilterChange]);

  const tabs: { key: FilterStatus; label: string }[] = [
    { key: "all", label: "All" },
    { key: "pending", label: "Pending" },
    { key: "completed", label: "Completed" },
  ];

  const togglePriority = (priority: number) => {
    setPriorities((prev) =>
      prev.includes(priority)
        ? prev.filter((p) => p !== priority)
        : [...prev, priority]
    );
  };

  const toggleTag = (tagId: string) => {
    setTagIds((prev) =>
      prev.includes(tagId)
        ? prev.filter((id) => id !== tagId)
        : [...prev, tagId]
    );
  };

  const sortOptions: { value: SortField; label: string }[] = [
    { value: "created_at", label: "Created" },
    { value: "updated_at", label: "Updated" },
    { value: "priority", label: "Priority" },
    { value: "due", label: "Due Date" },
    { value: "title", label: "Title" },
  ];

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <input
          type="text"
          placeholder="Search tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {search && (
          <button
            onClick={() => setSearch("")}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <svg
              className="h-5 w-5 text-gray-400 hover:text-gray-600"
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
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {tabs.map((tab) => {
          const count = taskCounts?.[tab.key];
          const isActive = status === tab.key;

          return (
            <button
              key={tab.key}
              onClick={() => setStatus(tab.key)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-colors ${
                isActive
                  ? "bg-white text-gray-900 shadow"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.label}
              {count !== undefined && (
                <span
                  className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                    isActive
                      ? "bg-blue-100 text-blue-600"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Advanced Filters Toggle */}
      <button
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        <svg
          className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
        {showAdvanced ? "Hide" : "Show"} Advanced Filters
      </button>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
          {/* Priority Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(PRIORITY_CONFIG).map(([level, config]) => {
                const priority = Number(level);
                const isSelected = priorities.includes(priority);
                return (
                  <button
                    key={priority}
                    type="button"
                    onClick={() => togglePriority(priority)}
                    className={`
                      px-3 py-1 text-xs font-medium rounded-full transition-all
                      ${isSelected
                        ? `${config.bgColor} ${config.textColor} ring-2 ring-offset-1`
                        : "bg-white border border-gray-300 text-gray-600 hover:bg-gray-50"
                      }
                    `}
                  >
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1"
                      style={{ backgroundColor: config.color }}
                    />
                    {config.label}
                  </button>
                );
              })}
              {priorities.length > 0 && (
                <button
                  onClick={() => setPriorities([])}
                  className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Tag Filter */}
          {availableTags.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2">
                {availableTags.map((tag) => {
                  const isSelected = tagIds.includes(tag.id);
                  return (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => toggleTag(tag.id)}
                      className={`
                        px-3 py-1 text-xs font-medium rounded-full transition-all flex items-center
                        ${isSelected
                          ? "ring-2 ring-offset-1 ring-blue-500"
                          : "hover:opacity-80"
                        }
                      `}
                      style={{
                        backgroundColor: isSelected ? tag.color + "30" : tag.color + "20",
                        color: tag.color,
                      }}
                    >
                      <span
                        className="inline-block w-2 h-2 rounded-full mr-1"
                        style={{ backgroundColor: tag.color }}
                      />
                      {tag.name}
                    </button>
                  );
                })}
                {tagIds.length > 0 && (
                  <button
                    onClick={() => setTagIds([])}
                    className="px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Due Date Range Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Due Date Range
            </label>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">From</label>
                <input
                  type="date"
                  value={dueFrom || ""}
                  onChange={(e) => setDueFrom(e.target.value || null)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-3 py-2 border"
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">To</label>
                <input
                  type="date"
                  value={dueTo || ""}
                  onChange={(e) => setDueTo(e.target.value || null)}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-3 py-2 border"
                />
              </div>
              {(dueFrom || dueTo) && (
                <button
                  onClick={() => {
                    setDueFrom(null);
                    setDueTo(null);
                  }}
                  className="self-end px-2 py-2 text-xs text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Sort Options */}
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortField)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-3 py-2 border"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as SortOrder)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-3 py-2 border"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
