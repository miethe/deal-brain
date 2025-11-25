# Enhancements and Fixes

Date: 10-15-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Requests

### Listings

- After successfully creating a new Listing, the creation modal should close, showing the Listings page with the new Listing visible in the list. Currently, the modal remains open, and must be closed manually.
- In the Listing detail Modal, on the Valuation tab, only the Rules which are contributing to the Total Adjustment for that Listing should be displayed at top, with all remaining Rules hidden by default.
    - The Valuation Tab should only display Rules with active adjustments being applied in the Current valuation pane of the modal, up to the max amount able to be shown based on the available size (currently 4 are shown).
    - The Valuation Breakdown screen (from clicking the "View Breakdown" button) should show all Rules, with those contributing to the Current valuation at top, and the rest in alphabetical order below. Additionally, all Rules should clearly indicate which RuleGroup and Ruleset they belong to. Users should be able to click on the Rule name to navigate to the Rule's detail page.

#### Listings Detail Page

- The full Listings detail page should be given a facelift. Currently, the design is very basic and displays only a subset of the total details for a given Listing. Instead, the page should be redesigned to display all available information in a clean and organized manner. This should include:
    - A summary section at the top with key details (name, model, price, valuation, etc).
    - An optional product image pulled from the listing URL or placeholder icon based on either the Manufacturer or fallback to Form Factor.
    - Tabs or sections for different categories of information (specifications, valuation details, history, etc).
    - Improved layout and styling to enhance readability and user experience.
    - Ensure that all data is displayed correctly and is easy to navigate.
    - Every field which links to another entity (eg Manufacturer, CPU, GPU, RAM Spec, etc) should be a clickable link to that entity's detail page. Each field should also have a hover tooltip with key details about that entity, similar to the tooltips on the /listings?tab=data view.
    - The Valuation tab should be redesigned to show a clear breakdown of the valuation, including the base price, adjustments from each Rule, and the final valuation. This should be visually appealing and easy to understand. It should have a similar layout to the Valuation section of the Listing modal.
