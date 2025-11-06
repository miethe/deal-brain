# Frontend Setup and Configuration

This guide covers setting up the Deal Brain frontend (Next.js 14 App Router) for local development.

## Prerequisites

- **Node.js** 18.17 or higher
- **pnpm** 8.0 or higher (we use pnpm for dependency management)
- **Git** for version control

Verify your versions:

```bash
node --version  # Should be >= 18.17
pnpm --version  # Should be >= 8.0
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd deal-brain
```

### 2. Install Dependencies

From the monorepo root:

```bash
# Install all dependencies (Python and JavaScript)
make setup

# Or install only JavaScript dependencies
pnpm install --frozen-lockfile=false
```

Navigate to the web app:

```bash
cd apps/web
```

## Environment Configuration

### Environment Variables

Create a `.env.local` file in `apps/web/`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development
NODE_ENV=development

# Optional: Analytics (if configured)
# NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Environment Variable Details

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `http://localhost:8000` | `http://localhost:8000` or Docker IP |
| `NODE_ENV` | Development mode | `development` | `development`, `production` |

#### Docker Environment Setup

When running the full stack with Docker Compose:

```bash
# .env.local for Docker
NEXT_PUBLIC_API_URL=http://10.42.9.11:8020
```

Replace `10.42.9.11` with your host machine's IP address (visible in Docker Compose logs).

## Running the Development Server

### Local Development

From `apps/web/`:

```bash
# Start the Next.js dev server
pnpm dev

# Server runs at: http://localhost:3000
```

The development server:
- Hot-reloads on file changes
- Shows TypeScript errors in the browser overlay
- Provides detailed error messages

### With Docker Compose

From the monorepo root:

```bash
# Start the full stack (API, web, database, Redis, etc.)
make up

# Web server runs at: http://localhost:3020
# API server runs at: http://localhost:8020
```

## Building for Production

### Development Build

```bash
pnpm build
```

This:
- Compiles TypeScript and JSX
- Optimizes bundle size
- Generates static assets

### Production Build

```bash
# Build optimized production bundle
pnpm build

# Start production server
pnpm start

# Server runs at: http://localhost:3000
```

## Code Quality

### TypeScript Compilation

Check for TypeScript errors without building:

```bash
pnpm typecheck
```

### Linting

Lint TypeScript and JSX:

```bash
pnpm lint
```

### Format Code

Format with Prettier (from monorepo root):

```bash
make format
```

## Project Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `next` | 14.1.0 | React framework with App Router |
| `react` | 18.2.0 | UI library |
| `@tanstack/react-query` | ^5.24.3 | Data fetching and caching |
| `react-hook-form` | ^7.50.1 | Form state management |
| `zod` | ^3.22.4 | Schema validation |
| `zustand` | ^5.0.8 | State management |
| `tailwindcss` | ^3.4.1 | Utility CSS framework |

### UI and Components

| Package | Version | Purpose |
|---------|---------|---------|
| `@radix-ui/*` | Various | Headless UI components |
| `lucide-react` | ^0.319.0 | Icon library |
| `recharts` | ^2.12.0 | React charting library |
| `framer-motion` | ^11.0.3 | Animation library |

### Development Tools

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | 5.3.3 | Type checking |
| `eslint` | ^8.56.0 | Code linting |
| `autoprefixer` | ^10.4.17 | CSS vendor prefixes |
| `@types/react` | 18.2.47 | TypeScript types |

### Utility Libraries

| Package | Version | Purpose |
|---------|---------|---------|
| `use-debounce` | ^10.0.0 | Debounce hook (200ms search) |
| `date-fns` | ^3.0.0 | Date formatting |
| `clsx` | ^2.1.0 | Conditional class names |
| `tailwind-merge` | ^2.2.1 | Merge Tailwind classes |
| `@dnd-kit/*` | Various | Drag-and-drop functionality |
| `@tanstack/react-table` | ^8.10.8 | Headless table library |
| `@tanstack/react-virtual` | ^3.13.12 | Virtual scrolling |

## TypeScript Configuration

The project uses strict TypeScript (`strict: true`):

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "strict": true,
    "jsxFactory": "React.createElement",
    "module": "esnext",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

## Path Aliases

Use `@/` to reference the `apps/web/` directory:

```typescript
// Instead of:
import { Component } from '../../../components/listing/component'

// Use:
import { Component } from '@/components/listings/component'
```

Available aliases:
- `@/components` → `apps/web/components/`
- `@/hooks` → `apps/web/hooks/`
- `@/lib` → `apps/web/lib/`
- `@/stores` → `apps/web/stores/`
- `@/types` → `apps/web/types/`
- `@/public` → `apps/web/public/`

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or specify a different port
pnpm dev -- -p 3001
```

### Module Not Found

Clear Next.js cache and reinstall:

```bash
rm -rf .next node_modules
pnpm install
pnpm build
```

### API Connection Issues

1. Check `NEXT_PUBLIC_API_URL` is correct
2. Verify backend is running: `make api`
3. Check CORS headers in backend
4. Inspect network requests in browser DevTools

### TypeScript Errors

```bash
# Check for compilation errors
pnpm typecheck

# Rebuild if needed
pnpm build
```

### Hot Reload Not Working

1. Check file permissions
2. Clear Next.js cache: `rm -rf .next`
3. Restart dev server: `pnpm dev`

## Next Steps

- Read [Project Structure](./project-structure.md) to understand directory organization
- Review [Component Patterns](./component-patterns.md) for coding standards
- Check [Data Fetching](./data-fetching.md) for API integration patterns
