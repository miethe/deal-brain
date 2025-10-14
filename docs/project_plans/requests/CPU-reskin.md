# Enhancements and Fixes

Date: 10-09-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Requests

### Global Fields

#### CPUs

- There should be a reskinned page for viewing CPUs, similar to the Listings page. This page should include:
  - A table view with columns (current page) and the ability to sort and filter by any of these columns.
  - A catalog view, similar to the Listings catalog view, showing CPU cards with key details.
  - The ability to click on a CPU in either view to open a modal with full details about the CPU, including all fields from the CPU table.
- There should be a new field which shows a "Good" target price for the CPU, based on the PassMark Single Thread or Multi-Thread Score. This target price should be calculated as follows:
  - Take the average adjusted price for all listings with this CPU.
  - We could also display a range of values, with a "Good" price being the average, a "Great" price being one standard deviation below the average, and a "Fair" price being one standard deviation above the average. Alternatively, if there are enough samples, we could base the prices on actual deals from past Listings.
- There should be a new calculation that the app performs to determine if the $/PassMark score for the CPU is a "Good", "Great", or "Fair" deal, based on the adjusted price of the listing and the PassMark score of the CPU. This calculation should be displayed on both the CPU detail modal and the Listings page when a CPU is selected. It is different than the Listing Deal Meter, which is a historical price of that CPU, whereas this is based on performance of the CPU.
