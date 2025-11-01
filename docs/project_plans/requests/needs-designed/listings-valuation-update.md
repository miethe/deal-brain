# Enhancements

Created Date: 11-01-25

The following requests are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Behaviors

### Listings

- Currently, adjusted valuation fields such as `dollar_per_cpu_mark_single_adjusted` are calculated erroneously. An adjusted valuation is calculated for the listing, with that new (higher) price used to calculate the adjusted metrics. However, there are 2 types of calculations which should be made based on the adjusted values:
  1. The higher adjusted price, which is the adjusted 'value' of the listing. This is how much the listing is 'worth', and should only be used when comparing the listing's value against the base price to show the overall value of the listing.
  2. The adjusted delta, which is the difference between the base price and the adjusted price based on the various included components, the amount calculated by the valuation rules. When calculating adjusted valuation metrics, such as $/Single-Thread Mark adjusted, the app should subtract the adjusted delta from the base price, and use that new price to calculate the adjusted metrics. This allows for fields such as `dollar_per_cpu_mark_single_adjusted` to reflect the adjusted price of the CPU in the listing. IE, given a listing with a base price of $500, and an adjusted price of $600 (due to valuation rules from 32GB DDR5 RAM), the adjusted delta is $100. When calculating adjusted metrics for the CPU, the app should use a price of $400 ($500 - $100) to calculate the adjusted metrics, reflecting the adjusted value of specifically the CPU in the listing minus the value of the included components (in this case, the RAM).
  - Perform an in-depth analysis of all sections of code utilizing the adjusted valuation fields and determine which of the 2 above calculation methods should be applied in each case, then update them accordingly. For the method `listings.calculate_cpu_performance_metrics()`, the adjusted delta method (2) should be used.

- There is currently no way to delete listings from the app. There should be a delete button in the listing detail modal and listing detail page, which prompts the user to confirm deletion before permanently deleting the listing from the database. This button should be located in the top right corner of the detail page and in the bottom bar next to the `View Full Page` button in the detail modal.

- The `/listings` catalog view should include an import button next to the "Add listing" button in the top right. This button should open the listing import modal, allowing users to import listings directly from the catalog view using the same functions and screens from the `/import` page.