# Enhancements and Fixes

Date: 10-09-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Requests

### New Page: Deal Builder

- There should be a new page called "Deal Builder" which allows users to create a custom build by selecting components (CPU, RAM, Storage, etc.) from dropdowns or search fields.
- As the user selects components, the page should dynamically calculate and display the total price of the build, as well as the adjusted value based on the selected components and any applicable valuation rules.
- Specifically, the user would choose a CPU first, which would set the baseline value. Then, as they add RAM, Storage, and other components, the adjusted value would update in real-time to reflect the total value of the build, based on the Ruleset applied (same logic as for Listings).
- The page would also allow users to save their custom builds for future reference, and potentially share them with others.
- The page would show a deal meter, with different prices indicating "Good", "Great", and "Fair" deals based on the adjusted value of the build in terms of $/passmark score.
