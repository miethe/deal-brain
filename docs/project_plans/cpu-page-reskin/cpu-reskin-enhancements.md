# CPU Page Reskin Enhancements

Created Date: 11-06-25

## Key Instructions

Review the relevant sections of the PRD linked in the Context section below before proceeding with any designs or implementations. If the below requests fall outside the existing specifications, then create a very brief PRD addendum for the relevant sections before proceeding.

You should not be creating new documentation outside of the PRD addendum unless specifically instructed to do so. You should create new context and progress files (1x each) titled cpu-reskin-enhancements in the relevant docs/project_plans/cpu-page-reskin/context and docs/project_plans/cpu-page-reskin/progress directories respectively, and use these for all future enhancements related to the CPU page reskin project. Remember, neither are intended to be user documentation; rather, each is intended to serve as dedicated context caches to assist your development process as an AI Agent.

## Context

- PRD: docs/project_plans/cpu-page-reskin/PRD.md
- Implementation Plan: docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md
- Context Files: docs/project_plans/cpu-page-reskin/context

## Requests

- The new CPUs page at /cpus is not present in the sidebar, and so the only way to access it is via direct link. Please add the CPUs page to the sidebar navigation under a new "Catalogs" dropdown section, ensuring it is easily discoverable by users.

- On the CPUs catalog page, filtering only seems to function in the "Grid" view. The other 2 views do not update the displayed CPUs when filters are applied. Please ensure that filtering works consistently across all view modes (Grid, List, and Table).
- There should be a method to filter CPUs to only those attached to active listings. This could be a toggle or checkbox labeled "Show only CPUs with active listings" that, when enabled, filters the CPU catalog to display only those CPUs that have at least one active listing in the system. This should be enabled by default to reduce the total number of CPUs fetched initially, as many CPUs do not have any active listings.

- There is no way to click into a CPU detail page from the CPUs catalog. In the Grid view, clicking on the CPU "card" does nothing, but should open a modal with a detail view of the CPU. In the List and Table views, clicking on the CPU row should navigate to the CPU detail modal.
    - If this modal does not yet exist, it should look similar to the detailed view shown in the right panel on the "Compare" view. It should also pull data from the existing detail page at /catalog/cpus/{id}, ie the "Used In Listings" section.

- When viewing Listings, if a user clicks on the CPU name in a Listing, it currently navigates to the old CPU detail page at /catalog/cpus/{id}. This should be updated to navigate the user to the /cpus catalog view with the target CPU in focus, and open the new CPU detail modal instead, providing a consistent user experience.