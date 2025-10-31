# Feature Requirements: Auto-Close Modal

**Status:** Draft
**Priority:** High
**Affects:** Creation workflow, user experience

---

## Overview

Streamline the listing creation workflow by automatically closing the modal after successful submission and refreshing the list view with the newly created item highlighted.

---

## User Story

As a Deal Brain user, I want the creation modal to close automatically after I successfully create a new listing, so that I can immediately see my new listing in the list view without manual dismissal.

---

## Acceptance Criteria

### Successful Creation Flow

1. After successful API response (201 Created), modal automatically closes
2. List view automatically refreshes to include new listing
3. New listing is highlighted/scrolled into view (if not already visible)
4. Success toast notification displays: "Listing created successfully"

### Error Handling

1. On validation errors (400), modal remains open with error messages
2. On server errors (500), modal remains open with retry option
3. Network errors show appropriate error state without closing modal
4. Form data preserved if modal remains open for corrections

### User Feedback

1. Loading state visible during save operation
2. Optimistic UI updates (item appears before full refresh)
3. Smooth transition from modal close to list update
4. Visual indicator on newly created item (highlight animation, badge, etc.)

### Accessibility

1. Focus returns to appropriate location in list view (newly created item row)
2. Screen reader announces creation success
3. Keyboard navigation works throughout flow

---

## UI/UX Specifications

- **Close Animation:** 200ms fade-out for modal
- **List Refresh:** React Query invalidation triggers automatic refetch
- **Highlight Duration:** 2 seconds with subtle background color pulse
- **Scroll Behavior:** Smooth scroll if new item outside viewport
- **Toast Position:** Top-right, auto-dismiss after 3 seconds

---

## Technical Considerations

- Use React Query's `onSuccess` mutation callback for modal close
- Invalidate queries: `['listings', 'records']` and `['listings', 'count']`
- Store newly created listing ID for highlight targeting
- Use Zustand store or URL params for highlight state management
- Consider optimistic updates for perceived performance

---

## Edge Cases

1. Multiple rapid creations (prevent race conditions)
2. Creation while filters active (ensure new item visible or notify)
3. Creation in paginated list (navigate to page containing new item)
4. Concurrent edits by other users (show latest state)

---

## Mockup Reference

```
User fills listing form
  ↓
Clicks "Create Listing" button
  ↓
Loading state: button disabled, spinner visible
  ↓
API request succeeds (201)
  ↓
Success toast appears: "Listing created successfully"
  ↓
Modal closes automatically (200ms fade)
  ↓
List view refreshes (React Query invalidation)
  ↓
New listing appears, highlighted (2s animation)
  ↓
Focus moves to new listing row
```

---

## Implementation Tasks

See [Implementation Plan - Phase 1: Auto-Close Modal](../../IMPLEMENTATION_PLAN.md#phase-1-auto-close-modal-week-1) for detailed tasks and code changes.

**Key Tasks:**
- TASK-101: Modify AddListingForm with onSuccess callback
- TASK-102: Enhance AddListingModal auto-close logic
- TASK-103: Implement list refresh and highlight
- TASK-104: Focus management after modal close
- TASK-105: Add success toast notification

---

## Success Criteria (QA)

- [ ] Modal closes automatically after successful creation (201 response)
- [ ] Modal remains open on validation errors (400) or server errors (500)
- [ ] New listing appears in table within 2 seconds
- [ ] New listing is highlighted with 2-second pulse animation
- [ ] Focus moves to new listing row
- [ ] Success toast displays
- [ ] Keyboard navigation works throughout flow
- [ ] Works correctly with filters active
- [ ] Works correctly in paginated lists
- [ ] Handles rapid consecutive creations without issues

---

## Related Documentation

- **[Implementation Plan - Phase 1](../../IMPLEMENTATION_PLAN.md#phase-1-auto-close-modal-week-1)**
- **[Testing Strategy - Creation Flow Tests](../../IMPLEMENTATION_PLAN.md#unit-tests)**
- **[Auto-Close Feature in Main PRD](../PRD.md)**
