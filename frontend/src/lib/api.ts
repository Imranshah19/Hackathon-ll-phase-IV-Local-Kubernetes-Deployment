/**
 * API Client for backend communication.
 *
 * Handles all HTTP requests with automatic JWT token injection.
 */

import Cookies from "js-cookie";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Cookie configuration
const TOKEN_COOKIE = "access_token";
const COOKIE_OPTIONS = {
  secure: process.env.NODE_ENV === "production",
  sameSite: "strict" as const,
  expires: 1, // 1 day
};

// =============================================================================
// Token Management
// =============================================================================

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_COOKIE);
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_COOKIE, token, COOKIE_OPTIONS);
}

export function removeToken(): void {
  Cookies.remove(TOKEN_COOKIE);
}

// =============================================================================
// API Types
// =============================================================================

export interface User {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  is_completed: boolean;
  priority: number; // 1=Critical, 2=High, 3=Medium, 4=Low, 5=None
  due: string | null;
  tags: string[];
  recurrence_rule_id: string | null;
  parent_task_id: string | null;
  created_at: string;
  updated_at: string;
}

// Priority configuration
export const PRIORITY_CONFIG = {
  1: { label: "Critical", color: "#EF4444", bgColor: "bg-red-100", textColor: "text-red-700" },
  2: { label: "High", color: "#F97316", bgColor: "bg-orange-100", textColor: "text-orange-700" },
  3: { label: "Medium", color: "#EAB308", bgColor: "bg-yellow-100", textColor: "text-yellow-700" },
  4: { label: "Low", color: "#22C55E", bgColor: "bg-green-100", textColor: "text-green-700" },
  5: { label: "None", color: "#6B7280", bgColor: "bg-gray-100", textColor: "text-gray-700" },
} as const;

export type PriorityLevel = keyof typeof PRIORITY_CONFIG;

// Tag types (Phase 5 - US2)
export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color: string;
  created_at: string;
  task_count: number;
}

export interface TagCreateRequest {
  name: string;
  color?: string;
}

export interface TagUpdateRequest {
  name?: string;
  color?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

// Recurrence types (Phase 5 - US4)
export type RecurrenceFrequency = "daily" | "weekly" | "monthly" | "yearly";
export type RecurrenceEndType = "never" | "count" | "date";

export interface RecurrenceInput {
  frequency: RecurrenceFrequency;
  interval?: number;
  end_type?: RecurrenceEndType;
  end_count?: number;
  end_date?: string; // ISO date string
}

export interface TaskCreateRequest {
  title: string;
  description?: string;
  is_completed?: boolean;
  priority?: number;
  due?: string;
  tag_ids?: string[];
  recurrence?: RecurrenceInput; // Phase 5 - US4
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string;
  is_completed?: boolean;
  priority?: number;
  due?: string;
  tag_ids?: string[];
  update_series?: boolean; // Phase 5 - US4
}

// Complete task response (Phase 5 - US4)
export interface TaskCompleteResponse {
  task: Task;
  next_instance: Task | null;
}

// Task filter options
export interface TaskFilterOptions {
  completed?: boolean;
  search?: string;
  priority?: number[];
  due_from?: string;
  due_to?: string;
  tags?: string[];
  sort_by?: "created_at" | "updated_at" | "priority" | "due" | "title";
  sort_order?: "asc" | "desc";
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
  errors?: Array<{
    field: string;
    message: string;
    type: string;
  }>;
}

// =============================================================================
// Chat Types (Phase 3)
// =============================================================================

export interface ChatMessageRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatMessageResponse {
  message: string;
  confidence: number;
  action: string | null;
  suggested_cli: string | null;
  needs_confirmation: boolean;
  is_fallback: boolean;
  conversation_id: string;
  message_id: string;
  task: Task | null;
  tasks: Task[] | null;
}

export interface ConfirmActionRequest {
  conversation_id: string;
  confirmed: boolean;
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationList {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  generated_command: string | null;
  confidence_score: number | null;
  timestamp: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// =============================================================================
// API Client
// =============================================================================

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(includeAuth = true): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (includeAuth) {
      const token = getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    includeAuth = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(includeAuth),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `Request failed with status ${response.status}`,
      }));
      throw new ApiClientError(response.status, error);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // ---------------------------------------------------------------------------
  // Auth Endpoints
  // ---------------------------------------------------------------------------

  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await this.request<RegisterResponse>(
      "/api/auth/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      false
    );
    setToken(response.access_token);
    return response;
  }

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await this.request<TokenResponse>(
      "/api/auth/login",
      {
        method: "POST",
        body: JSON.stringify(data),
      },
      false
    );
    setToken(response.access_token);
    return response;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/api/auth/me");
  }

  logout(): void {
    removeToken();
  }

  // ---------------------------------------------------------------------------
  // Task Endpoints
  // ---------------------------------------------------------------------------

  async getTasks(options?: TaskFilterOptions): Promise<Task[]> {
    const params = new URLSearchParams();
    if (options?.completed !== undefined) {
      params.append("completed", String(options.completed));
    }
    if (options?.search) {
      params.append("search", options.search);
    }
    // Phase 5: Priority filter
    if (options?.priority && options.priority.length > 0) {
      options.priority.forEach((p) => params.append("priority", String(p)));
    }
    // Phase 5: Due date filters
    if (options?.due_from) {
      params.append("due_from", options.due_from);
    }
    if (options?.due_to) {
      params.append("due_to", options.due_to);
    }
    // Phase 5: Tags filter
    if (options?.tags && options.tags.length > 0) {
      options.tags.forEach((t) => params.append("tags", t));
    }
    // Phase 5: Sorting
    if (options?.sort_by) {
      params.append("sort_by", options.sort_by);
    }
    if (options?.sort_order) {
      params.append("sort_order", options.sort_order);
    }
    const queryString = params.toString();
    return this.request<Task[]>(`/api/tasks${queryString ? `?${queryString}` : ""}`);
  }

  async getTask(id: string): Promise<Task> {
    return this.request<Task>(`/api/tasks/${id}`);
  }

  async createTask(data: TaskCreateRequest): Promise<Task> {
    return this.request<Task>("/api/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateTask(id: string, data: TaskUpdateRequest): Promise<Task> {
    return this.request<Task>(`/api/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteTask(id: string, deleteSeries?: boolean): Promise<void> {
    const params = new URLSearchParams();
    if (deleteSeries) {
      params.append("delete_series", "true");
    }
    const queryString = params.toString();
    return this.request<void>(`/api/tasks/${id}${queryString ? `?${queryString}` : ""}`, {
      method: "DELETE",
    });
  }

  // Phase 5 - US4: Complete task with recurrence support
  async completeTask(id: string): Promise<TaskCompleteResponse> {
    return this.request<TaskCompleteResponse>(`/api/tasks/${id}/complete`, {
      method: "POST",
    });
  }

  // ---------------------------------------------------------------------------
  // Tag Endpoints (Phase 5)
  // ---------------------------------------------------------------------------

  async getTags(): Promise<Tag[]> {
    return this.request<Tag[]>("/api/tags");
  }

  async createTag(data: TagCreateRequest): Promise<Tag> {
    return this.request<Tag>("/api/tags", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateTag(id: string, data: TagUpdateRequest): Promise<Tag> {
    return this.request<Tag>(`/api/tags/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteTag(id: string): Promise<void> {
    return this.request<void>(`/api/tags/${id}`, {
      method: "DELETE",
    });
  }

  async suggestTags(prefix: string = ""): Promise<string[]> {
    const params = new URLSearchParams();
    if (prefix) {
      params.append("prefix", prefix);
    }
    const queryString = params.toString();
    return this.request<string[]>(`/api/tags/suggest${queryString ? `?${queryString}` : ""}`);
  }

  // ---------------------------------------------------------------------------
  // Chat Endpoints (Phase 3)
  // ---------------------------------------------------------------------------

  async sendChatMessage(data: ChatMessageRequest): Promise<ChatMessageResponse> {
    return this.request<ChatMessageResponse>("/api/chat/message", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async confirmChatAction(data: ConfirmActionRequest): Promise<ChatMessageResponse> {
    return this.request<ChatMessageResponse>("/api/chat/confirm", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getConversations(options?: { limit?: number; offset?: number }): Promise<ConversationList> {
    const params = new URLSearchParams();
    if (options?.limit !== undefined) {
      params.append("limit", String(options.limit));
    }
    if (options?.offset !== undefined) {
      params.append("offset", String(options.offset));
    }
    const queryString = params.toString();
    return this.request<ConversationList>(`/api/conversations${queryString ? `?${queryString}` : ""}`);
  }

  async getConversation(id: string): Promise<ConversationDetail> {
    return this.request<ConversationDetail>(`/api/conversations/${id}`);
  }

  async createConversation(title?: string): Promise<Conversation> {
    return this.request<Conversation>("/api/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  }

  async updateConversation(id: string, title: string): Promise<Conversation> {
    return this.request<Conversation>(`/api/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  }

  async deleteConversation(id: string): Promise<void> {
    return this.request<void>(`/api/conversations/${id}`, {
      method: "DELETE",
    });
  }
}

// =============================================================================
// Error Handling
// =============================================================================

export class ApiClientError extends Error {
  status: number;
  error: ApiError;

  constructor(status: number, error: ApiError) {
    super(error.detail);
    this.name = "ApiClientError";
    this.status = status;
    this.error = error;
  }
}

// =============================================================================
// Export
// =============================================================================

export const api = new ApiClient(API_BASE_URL);
