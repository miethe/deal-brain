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

### Valuation Rules

- Currently, there is no way to delete existing Valuation RuleGroups or Rulesets. This functionality should be added to allow users to manage their Rules more effectively.
- Rules support versioning, however there is no method for rolling back or viewing previous versions of a Rule, RuleGroup, or Ruleset. This functionality should be added to allow users to revert to previous versions if needed.

### Dashboard

- The Dashboard should more clearly indicate the values of the Listings in each section. This entire page needs a reskin.

## Refactors

- `rules.py`: There seems to be much duplicated code and complexity in this file. It should be refactored to improve readability and maintainability. Consider breaking down large functions into smaller, more focused functions, and removing or abstracting any redundant code.
