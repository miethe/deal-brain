# Deal Builder - Design Summary

## Quick Reference

This document provides a high-level overview of the Deal Builder feature design. For detailed specifications, see:

- **[UX/UI Specification](./deal-builder-ux-specification.md)** - Complete user experience and visual design
- **[Wireframes](./deal-builder-wireframes.md)** - Visual mockups and interaction flows
- **[Implementation Guide](./deal-builder-implementation-guide.md)** - Technical architecture and code examples

## Feature Overview

**Deal Builder** allows users to create custom PC builds by selecting individual components and receiving real-time valuation and performance calculations, leveraging Deal Brain's existing pricing intelligence and benchmark data.

### Core Value Proposition

1. **Build Transparency**: See exactly how component choices affect total value
2. **Data-Driven Decisions**: Compare custom builds to pre-built systems in the database
3. **Save & Share**: Track builds over time and share with others
4. **Real-time Intelligence**: Instant feedback on deal quality using existing valuation rules

## User Journey

```
Landing → Select CPU (Required) → Add RAM → Add Storage → Add GPU →
  ↓
View Live Valuation & Metrics → Save Build → Share or Compare to Market
```

## Key Design Decisions

### 1. Progressive Disclosure
- CPU selection first (required for metrics)
- Other components revealed progressively
- Advanced options collapsed by default

### 2. Real-time Feedback
- Instant price updates (300ms debounce)
- Live deal meter visualization
- Performance metric calculations

### 3. Existing Pattern Reuse
- Same valuation logic as listings
- Consistent color-coded deal indicators
- Familiar UI components (shadcn/ui)

### 4. Mobile-First Responsive
- Stacked layout on mobile
- Floating valuation drawer
- Touch-optimized interactions

## Technical Architecture

### Frontend Stack
```
Next.js 14 (App Router)
├─ React 18 (Components)
├─ React Query (Data fetching)
├─ Tailwind CSS (Styling)
└─ shadcn/ui (UI components)
```

### Backend Stack
```
FastAPI
├─ SQLAlchemy (ORM)
├─ PostgreSQL (Database)
└─ Core valuation logic (packages/core)
```

### Data Flow
```
User Selection → React Context → Debounced API Call →
Backend Calculation → Valuation Result → UI Update
```

## Component Hierarchy

### Frontend
```
BuilderPage
├─ BuilderProvider (Context)
├─ ComponentBuilder
│  ├─ ComponentCard (CPU)
│  ├─ ComponentCard (RAM)
│  ├─ ComponentCard (Storage)
│  ├─ ComponentCard (GPU)
│  └─ SavedBuildsSection
├─ ValuationPanel (Sticky)
│  ├─ PriceDisplay
│  ├─ DealMeter
│  ├─ PerformanceMetrics
│  └─ ValuationBreakdown
└─ Modals
   ├─ ComponentSelectorModal
   ├─ SaveBuildModal
   └─ ShareModal
```

### Backend
```
/v1/builder/
├─ POST /calculate (Valuation)
├─ POST /builds (Save)
├─ GET  /builds (List)
├─ GET  /builds/{id} (Get)
└─ GET  /compare (Comparison)
```

## Key Features by Priority

### MVP (Priority 1)
- [x] Component selection (CPU, RAM, Storage, GPU)
- [x] Real-time price calculation
- [x] Basic valuation display with deal meter
- [x] Save build functionality
- [x] Performance metrics display

### Enhanced (Priority 2)
- [x] Full valuation breakdown
- [x] Share build via URL
- [x] Saved builds persistence
- [x] Component recommendations
- [x] Mobile responsive design

### Polish (Priority 3)
- [ ] Compare to listings feature
- [ ] Export to PDF/Text
- [ ] Component compatibility warnings
- [ ] Accessibility enhancements (full WCAG AA)

### Future (Priority 4)
- [ ] Price history tracking
- [ ] Build templates
- [ ] Community build gallery
- [ ] AI-powered recommendations

## Design System

### Color-Coded Deal Indicators

| Quality | Range | Color | Usage |
|---------|-------|-------|-------|
| Great Deal | 25%+ savings | Dark Green | `bg-green-600` |
| Good Deal | 15-25% savings | Medium Green | `bg-green-500` |
| Fair Deal | 0-15% savings | Light Green | `bg-green-100` |
| Premium | 10%+ markup | Red | `bg-red-500` |
| Neutral | No change | Gray | `bg-gray-200` |

### Typography Scale
```css
Page Title:      text-3xl font-bold
Section Header:  text-xl font-semibold
Card Title:      text-lg font-medium
Price (Primary): text-2xl font-bold tabular-nums
Price (Adjusted): text-lg font-semibold tabular-nums
Metric Label:    text-sm font-medium text-muted-foreground
Body Text:       text-base
Helper Text:     text-sm text-muted-foreground
```

### Spacing System
```css
Card Gap:        gap-4 (16px)
Section Gap:     gap-6 (24px)
Card Padding:    p-6 (24px)
Button Height:   h-10 (40px)
Border Radius:   rounded-lg (8px)
```

## Database Schema

### New Table: `saved_builds`

```sql
saved_builds
├─ id (SERIAL PRIMARY KEY)
├─ name (VARCHAR)
├─ description (TEXT)
├─ tags (TEXT[])
├─ visibility (VARCHAR) -- 'private', 'public', 'unlisted'
├─ share_token (VARCHAR) -- Unique shareable URL token
├─ Component References
│  ├─ cpu_id (FK)
│  ├─ gpu_id (FK)
│  ├─ ram_spec_id (FK)
│  ├─ primary_storage_profile_id (FK)
│  └─ secondary_storage_profile_id (FK)
├─ Pricing Snapshot
│  ├─ base_price_usd (DECIMAL)
│  ├─ adjusted_price_usd (DECIMAL)
│  └─ component_prices (JSONB)
├─ Performance Metrics
│  ├─ dollar_per_cpu_mark_multi (DECIMAL)
│  ├─ dollar_per_cpu_mark_single (DECIMAL)
│  └─ composite_score (DECIMAL)
├─ valuation_breakdown (JSONB)
└─ Timestamps
   ├─ created_at
   ├─ updated_at
   └─ deleted_at
```

## API Contracts

### Calculate Build
```typescript
POST /v1/builder/calculate
Request: {
  components: {
    cpu_id?: number;
    gpu_id?: number;
    ram_spec_id?: number;
    primary_storage_profile_id?: number;
    secondary_storage_profile_id?: number;
  }
}
Response: {
  pricing: {
    base_price: number;
    adjusted_price: number;
    component_prices: Record<string, number>;
  };
  metrics: {
    dollar_per_cpu_mark_multi?: number;
    dollar_per_cpu_mark_single?: number;
    composite_score?: number;
  };
  valuation_breakdown: ValuationBreakdown;
}
```

### Save Build
```typescript
POST /v1/builder/builds
Request: {
  name: string;
  description?: string;
  tags?: string[];
  visibility: 'private' | 'public' | 'unlisted';
  components: { ... };
  pricing: { ... };
  metrics: { ... };
  valuation_breakdown: { ... };
}
Response: {
  id: number;
  share_token: string;
  ... (full build object)
}
```

## Implementation Timeline

### Week 1 (Days 1-5)
- Day 1-2: Frontend page structure and routing
- Day 3-4: Component selection UI
- Day 5: State management (React Context)

### Week 2 (Days 6-10)
- Day 6-7: Backend API endpoints
- Day 8-9: Valuation calculation integration
- Day 10: Frontend-backend integration

### Week 3 (Days 11-15)
- Day 11-12: Save/load functionality
- Day 13-14: Share feature
- Day 15: Saved builds gallery

### Week 4 (Days 16-20)
- Day 16-17: Mobile responsive design
- Day 18: Accessibility improvements
- Day 19: Testing and bug fixes
- Day 20: Documentation and deployment

## Testing Strategy

### Unit Tests
- Component selection logic
- Valuation calculation
- State management reducers
- API endpoint handlers

### Integration Tests
- Full user flows (create, save, load, share)
- API integration
- Database operations
- Valuation rule application

### E2E Tests
- Complete build creation flow
- Save and load builds
- Share URL functionality
- Mobile responsive behavior

### Performance Tests
- Page load time < 2s
- Calculation update < 300ms
- Component selection < 500ms

## Accessibility Requirements

### Keyboard Navigation
- Tab through all interactive elements
- Enter to select components
- Escape to close modals
- Arrow keys in component lists

### Screen Reader Support
- All buttons labeled with ARIA
- Live regions for price updates
- Semantic HTML structure
- Form inputs properly associated

### Visual Accessibility
- 4.5:1 text contrast minimum
- 3:1 UI component contrast
- Focus indicators on all interactive elements
- Color not sole indicator of meaning

## Performance Optimizations

### Frontend
- React.memo for expensive components
- Debounced API calls (300ms)
- Lazy loading for modals
- Image optimization (Next.js Image)
- Virtual scrolling for long lists

### Backend
- Database query optimization
- Response caching (React Query)
- Async operations
- Connection pooling

## Success Metrics

### User Engagement
- Builds created per user
- Saved builds ratio
- Share rate
- Return visits

### Performance
- Page load time
- Time to first interaction
- Calculation response time
- API error rate

### Business Value
- User retention increase
- Feature adoption rate
- Conversion to premium features (future)
- Community engagement (shared builds)

## Related Documentation

### Design Documents
- [UX/UI Specification](./deal-builder-ux-specification.md) - Detailed UX design
- [Wireframes](./deal-builder-wireframes.md) - Visual mockups
- [Implementation Guide](./deal-builder-implementation-guide.md) - Technical specs

### Codebase References
- `/apps/web/app/listings/` - Similar patterns for component display
- `/apps/web/components/listings/valuation-cell.tsx` - Valuation display component
- `/apps/api/dealbrain_api/services/listings.py` - Listing service patterns
- `/packages/core/dealbrain_core/valuation.py` - Core valuation logic

### API Documentation
- `/docs/api/` - API endpoint documentation
- `/docs/architecture/` - System architecture diagrams

## Next Steps

1. **Review & Approval**
   - Stakeholder review of UX design
   - Technical architecture approval
   - Timeline confirmation

2. **Setup**
   - Create feature branch
   - Set up development environment
   - Initialize project structure

3. **Implementation**
   - Follow phased implementation plan
   - Regular check-ins and demos
   - Iterative feedback and refinement

4. **Launch**
   - Beta testing with select users
   - Performance monitoring
   - Bug fixes and polish
   - Full production launch

---

**Last Updated**: 2025-11-12
**Status**: Design Complete - Ready for Implementation
**Owner**: Deal Brain Team
