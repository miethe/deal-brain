# Enhancements and Fixes

Date: 10-09-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Requests

### Listings



### Valuation Rules

#### Adjusted Values

  File "/usr/local/lib/python3.11/site-packages/dealbrain_api/api/rules.py", line 577, in update_rule

    rule = await service.update_rule(session, rule_id, updates)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/dealbrain_api/services/rules.py", line 518, in update_rule

    enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="rule_updated")

  File "/usr/local/lib/python3.11/site-packages/dealbrain_api/tasks/valuation.py", line 165, in enqueue_listing_recalculation

    recalculate_listings_task(**payload)

  File "/usr/local/lib/python3.11/site-packages/celery/local.py", line 182, in __call__

    return self._get_current_object()(*a, **kw)

           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/celery/app/task.py", line 411, in __call__

    return self.run(*args, **kwargs)

           ^^^^^^^^^^^^^^^^^^^^^^^^^

TypeError: recalculate_listings_task() got an unexpected keyword argument 'reason'

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


### New Page: Deal Builder

- There should be a new page called "Deal Builder" which allows users to create a custom build by selecting components (CPU, RAM, Storage, etc.) from dropdowns or search fields.
- As the user selects components, the page should dynamically calculate and display the total price of the build, as well as the adjusted value based on the selected components and any applicable valuation rules.
- Specifically, the user would choose a CPU first, which would set the baseline value. Then, as they add RAM, Storage, and other components, the adjusted value would update in real-time to reflect the total value of the build, based on the Ruleset applied (same logic as for Listings).
- The page would also allow users to save their custom builds for future reference, and potentially share them with others.
- The page would show a deal meter, with different prices indicating "Good", "Great", and "Fair" deals based on the adjusted value of the build in terms of $/passmark score.


### Dashboard


## Bugs

