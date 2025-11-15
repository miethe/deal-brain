# Enhancements

Created Date: 10-31-25

The following requests are proposed to improve the user experience and functionality of the application. Each item needs to be evaluated and designed thoroughly for implementation into the app. The implementation of each should then be planned.

## Notes

- Review @architecture.md for current architecture overview.

## Existing Behaviors

### Entities

- Every entity should have a dedicated view on the /global-fields page, similar to Listings and CPUs. This will provide a consistent experience across all entity types, allowing fields and data to be viewed and managed in one place.
  - This would allow creating/editing Entity specs from a central location. Currently, it is not possible to edit entities like RAM Specs or Storage Specs, so mistakes persist and can't be fixed.
  - There is already a details view for linked entities like CPUs at /catalog/{entity}/{id}, so this would extend that functionality to all entity types. The page should also be updated to support editing and deleting entities and all related fields.
