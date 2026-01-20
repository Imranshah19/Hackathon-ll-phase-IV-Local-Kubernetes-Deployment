# Frontend Development Guidelines

## Technology Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **State**: React hooks (useState, useEffect, useCallback)
- **Auth**: JWT tokens stored in cookies (js-cookie)

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx         # Landing page
│   │   ├── login/           # Authentication pages
│   │   ├── register/
│   │   ├── tasks/           # Task management (Phase 2)
│   │   └── chat/            # AI Chat interface (Phase 3)
│   ├── components/
│   │   ├── chat/            # Chat UI components (Phase 3)
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── InputBar.tsx
│   │   │   └── FallbackCLI.tsx
│   │   └── TaskFilters.tsx
│   └── lib/
│       ├── api.ts           # API client with all endpoints
│       └── auth.tsx         # Auth context and hooks
└── public/
```

## Coding Conventions

### Components

- Use functional components with TypeScript
- Export named components (not default)
- Props interface defined above component
- "use client" directive for client components

```typescript
"use client";

interface MyComponentProps {
  title: string;
  onClick?: () => void;
}

export function MyComponent({ title, onClick }: MyComponentProps) {
  return <button onClick={onClick}>{title}</button>;
}
```

### State Management

- Use React hooks for local state
- API calls in useEffect with cleanup
- useCallback for memoized functions passed as props

### API Calls

- All API calls go through `src/lib/api.ts`
- Use the `api` singleton instance
- Handle errors with try/catch and ApiClientError

```typescript
import { api, ApiClientError } from "@/lib/api";

try {
  const tasks = await api.getTasks();
} catch (err) {
  if (err instanceof ApiClientError) {
    setError(err.message);
  }
}
```

### Styling

- Use Tailwind CSS classes directly
- Dark mode support with `dark:` prefix
- Responsive design with `sm:`, `md:`, `lg:` prefixes
- No inline styles unless absolutely necessary

### Authentication

- Protected routes use `ProtectedRoute` component
- Token automatically injected by api client
- Redirect to login on 401 errors

## Phase 3 Chat Components

### ChatWindow

Main orchestrator for chat interface:
- Manages message state
- Handles send/confirm actions
- Shows loading and error states
- Auto-scrolls to new messages

### MessageBubble

Displays individual messages:
- User messages: blue, right-aligned
- Assistant messages: gray, left-aligned
- Shows confidence indicator for AI responses
- Displays task data when available

### InputBar

Text input with send button:
- Auto-resize textarea
- Enter to send, Shift+Enter for newline
- Character limit (2000)
- Disabled during loading

### FallbackCLI

Shows CLI alternatives:
- Displayed when AI confidence is low
- Copy-to-clipboard functionality
- Terminal-style code display

## Testing

- Component tests with Jest/Vitest
- E2E tests for critical flows
- Mock API responses in tests

## Don'ts

- Don't access backend database directly
- Don't store sensitive data in localStorage
- Don't use inline styles
- Don't create components larger than 300 lines
- Don't skip TypeScript types
