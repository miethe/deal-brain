# Enhancements and Fixes

Created Date: 10-24-25
Updated Date: 10-31-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Existing Behaviors

### Listings

- On the /listings page, when viewing the Data tab, the site becomes very slow to respond. We should optimize the performance of this page to ensure a smooth user experience even with large datasets.

- On the /listings detail page - /listings/{id}, there a few requested enhancements:
  - The Adjusted Price section should have a hover tooltip explaining how the adjusted price is calculated, including a brief overview of the valuation rules applied. This field should also be universally renamed to Adjusted "Value".
  - On the Specifications tabs, under Compute, the Score and $/CPU Mark fields should be paired, so that Single-Thread Score is next to $/Single-Thread Mark, and Multi-Thread Score is next to $/Multi-Thread Mark. This will improve readability and make it easier for users to compare these related metrics.
    - Additionally, the $/CPU Mark fields should show both base value and adjusted value side-by-side, similar to how it is displayed on the card on the /listings catalog view. The adjusted value should have a hover tooltip similar to the adjusted price field above. All adjusted pricing fields should have dynamic styling/coloring to indicate how "good" of a deal it is, with the thresholds defined as a configuration variable.

- The images displayed on the listings detail page and dashboard listing cards should be unified, with the image locations pulled out into a configuration file for easy updating. Architect a powerful and extensible, yet easy-to-use method for adding images for various manufacturers and form factors, ideally without needing to update the codebase, maintaining the clear fallbacks when no specific image is available.
