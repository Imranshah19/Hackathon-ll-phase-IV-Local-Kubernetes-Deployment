"use client";

import { useState, useEffect, useCallback } from "react";
import { Tag, api, ApiClientError } from "@/lib/api";

interface TagManagerProps {
  onClose: () => void;
}

/**
 * Tag manager modal for creating, editing, and deleting tags.
 */
export function TagManager({ onClose }: TagManagerProps) {
  const [tags, setTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#6B7280");
  const [isCreating, setIsCreating] = useState(false);

  const predefinedColors = [
    "#EF4444", // Red
    "#F97316", // Orange
    "#EAB308", // Yellow
    "#22C55E", // Green
    "#3B82F6", // Blue
    "#8B5CF6", // Purple
    "#EC4899", // Pink
    "#6B7280", // Gray
  ];

  const fetchTags = useCallback(async () => {
    try {
      setError("");
      const data = await api.getTags();
      setTags(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to load tags");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTags();
  }, [fetchTags]);

  const handleCreate = async () => {
    if (!newTagName.trim()) return;

    setIsCreating(true);
    try {
      const newTag = await api.createTag({
        name: newTagName.trim(),
        color: newTagColor,
      });
      setTags((prev) => [...prev, newTag]);
      setNewTagName("");
      setNewTagColor("#6B7280");
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdate = async (tag: Tag) => {
    try {
      const updated = await api.updateTag(tag.id, {
        name: tag.name,
        color: tag.color,
      });
      setTags((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      setEditingTag(null);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
    }
  };

  const handleDelete = async (tagId: string) => {
    const tag = tags.find((t) => t.id === tagId);
    if (!tag) return;

    const message =
      tag.task_count > 0
        ? `This tag is used by ${tag.task_count} task(s). Are you sure you want to delete it?`
        : "Are you sure you want to delete this tag?";

    if (!confirm(message)) return;

    try {
      await api.deleteTag(tagId);
      setTags((prev) => prev.filter((t) => t.id !== tagId));
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Manage Tags</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-md">
            {error}
          </div>
        )}

        {/* Create New Tag */}
        <div className="p-4 border-b">
          <div className="flex gap-2">
            <input
              type="text"
              value={newTagName}
              onChange={(e) => setNewTagName(e.target.value)}
              placeholder="New tag name..."
              maxLength={50}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="flex gap-1">
              {predefinedColors.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setNewTagColor(color)}
                  className={`w-6 h-6 rounded-full ${
                    newTagColor === color ? "ring-2 ring-offset-1 ring-blue-500" : ""
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <button
              onClick={handleCreate}
              disabled={!newTagName.trim() || isCreating}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Add
            </button>
          </div>
        </div>

        {/* Tag List */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            </div>
          ) : tags.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No tags yet. Create your first tag above.
            </p>
          ) : (
            <div className="space-y-2">
              {tags.map((tag) => (
                <div
                  key={tag.id}
                  className="flex items-center justify-between p-2 rounded-md hover:bg-gray-50"
                >
                  {editingTag?.id === tag.id ? (
                    <div className="flex items-center gap-2 flex-1">
                      <input
                        type="text"
                        value={editingTag.name}
                        onChange={(e) =>
                          setEditingTag({ ...editingTag, name: e.target.value })
                        }
                        className="flex-1 px-2 py-1 border rounded text-sm"
                        autoFocus
                      />
                      <div className="flex gap-1">
                        {predefinedColors.map((color) => (
                          <button
                            key={color}
                            type="button"
                            onClick={() => setEditingTag({ ...editingTag, color })}
                            className={`w-5 h-5 rounded-full ${
                              editingTag.color === color
                                ? "ring-2 ring-offset-1 ring-blue-500"
                                : ""
                            }`}
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <button
                        onClick={() => handleUpdate(editingTag)}
                        className="text-green-600 hover:text-green-800"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                      <button
                        onClick={() => setEditingTag(null)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-2">
                        <span
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: tag.color }}
                        />
                        <span className="font-medium">{tag.name}</span>
                        <span className="text-xs text-gray-400">
                          {tag.task_count} tasks
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setEditingTag(tag)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(tag.id)}
                          className="text-gray-400 hover:text-red-600"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
