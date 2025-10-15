# Enhancements and Fixes

Date: 10-15-25

The following requests and fixes are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Bugs

### Valuation Rules



### Listings

- When adding a new Listing with all data populated, I get the following errors:

```log
app-index.js:35 Post-creation update failed: TypeError: Failed to fetch
    at apiFetch (utils.ts:28:26)
    at updateListingPorts (listings.ts:74:17)
    at Object.onSuccess (add-listing-form.tsx:346:37)
```

```log
INFO:     10.0.2.218:49510 - "POST /v1/listings/6/ports HTTP/1.1" 500 Internal Server Error

ERROR:    Exception in ASGI application

Traceback (most recent call last):

  File "/usr/local/lib/python3.11/site-packages/dealbrain_api/api/listings.py", line 485, in update_listing_ports

    ports = await ports_service.get_listing_ports(session, listing_id)

            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/dealbrain_api/services/ports.py", line 106, in get_listing_ports

    listing = result.scalar_one_or_none()

              ^^^^^^^^^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/result.py", line 1492, in scalar_one_or_none

    return self._only_one_row(

           ^^^^^^^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/result.py", line 784, in _only_one_row

    existing_row_hash = strategy(row) if strategy else row

                        ^^^^^^^^^^^^^

  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/orm/loading.py", line 286, in require_unique

    raise sa_exc.InvalidRequestError(

sqlalchemy.exc.InvalidRequestError: The unique() method must be invoked on this Result, as it contains results that include joined eager loads against collections
```

```log
app-index.js:35 Failed to fetch CPU data: ApiError: Not Found
    at apiFetch (utils.ts:53:11)
    at async handleCpuChange (add-listing-form.tsx:181:23)
```

```log
INFO:     10.0.2.218:64839 - "OPTIONS /v1/catalog/cpus/4653 HTTP/1.1" 200 OK

INFO:     10.0.2.218:64839 - "GET /v1/catalog/cpus/4653 HTTP/1.1" 404 Not Found
```


## Requests

### Listings

- After successfully creating a new Listing, the creation modal should close, showing the Listings page with the new Listing visible in the list. Currently, the modal remains open, and must be closed manually.
- In the Listing detail Modal, on the Valuation tab, the Rules which are contributing to the Total Adjustment for that Listing should be displayed at top, with the remaining Rules in alphabetical order below.
    - The Valuation Tab should only display Rules with active adjustments being applied in the Current valuation pane of the modal, up to the max amount able to be shown based on the available size (currently 4 are shown).
    - The Valuation Breakdown screen (from clicking the "View Breakdown" button) should show all Rules, with those contributing to the Current valuation at top, and the rest in alphabetical order below. Additionally, all Rules should clearly indicate which RuleGroup and Ruleset they belong to.

#### Listings Detail Page

- The full Listings detail page should be given a facelift. Currently, the design is very basic and displays only a subset of the total details for a given Listing. Instead, the page should be redesigned to display all available information in a clean and organized manner. This should include:
    - A summary section at the top with key details (name, model, price, valuation, etc).
    - An optional product image pulled from the listing URL or placeholder icon based on either the Manufacturer or fallback to Form Factor.
    - Tabs or sections for different categories of information (specifications, valuation details, history, etc).
    - Improved layout and styling to enhance readability and user experience.
    - Ensure that all data is displayed correctly and is easy to navigate.
    - Every field which links to another entity (eg Manufacturer, CPU, GPU, RAM Spec, etc) should be a clickable link to that entity's detail page. Each field should also have a hover tooltip with key details about that entity, similar to the tooltips on the /listings?tab=data view.
    - The Valuation tab should be redesigned to show a clear breakdown of the valuation, including the base price, adjustments from each Rule, and the final valuation. This should be visually appealing and easy to understand.

### Valuation Rules

- Currently, there is no way to delete existing Valuation RuleGroups or Rulesets. This functionality should be added to allow users to manage their Rules more effectively.
- Rules support versioning, however there is no method for rolling back or viewing previous versions of a Rule, RuleGroup, or Ruleset. This functionality should be added to allow users to revert to previous versions if needed.

### Dashboard

- The Dashboard should more clearly indicate the values of the Listings in each section. This entire page needs a reskin.

## Refactors

- `rules.py`: There seems to be much duplicated code and complexity in this file. It should be refactored to improve readability and maintainability. Consider breaking down large functions into smaller, more focused functions, and removing or abstracting any redundant code.
