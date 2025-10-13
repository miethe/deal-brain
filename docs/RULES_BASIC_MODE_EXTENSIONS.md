# Rules API Extensions for Basic Mode Support

## Overview

Extended the Rules CRUD APIs to properly handle metadata fields required by the Basic mode interface, including `basic_managed`, `entity_key`, and `modifiers_json`.

## Implementation Details

### 1. Schema Extensions

#### Rule Group Schemas
- **Added fields to `RuleGroupCreateRequest`, `RuleGroupUpdateRequest`, and `RuleGroupResponse`:**
  - `basic_managed: bool | None` - Indicates if group is managed by Basic mode
  - `entity_key: str | None` - Entity type (Listing, CPU, GPU, RamSpec, StorageProfile, PortsProfile)

- **Added validation:**
  - `basic_managed=true` requires `entity_key` to be set
  - `entity_key` must be from the valid set of entities

#### Action Schema Enhancement
- **Enhanced `ActionSchema.modifiers` field documentation:**
  - Supports `min_usd`, `max_usd` for value clamping
  - `clamp: bool` flag to enable clamping
  - `explanation: str` for UI tooltips
  - `formula_notes: str` for formula documentation
  - `unit: str` (multiplier, usd, percentage, formula)

### 2. Validation Module

Created `/apps/api/dealbrain_api/validation/rules_validation.py` with:

#### Core Functions
- `validate_basic_managed_group()` - Prevents manual edits to basic-managed groups
- `validate_entity_key()` - Validates entity keys against allowed set
- `validate_modifiers_json()` - Validates action modifiers consistency
- `extract_metadata_fields()` - Extracts basic_managed and entity_key from metadata
- `merge_metadata_fields()` - Merges metadata fields properly

#### Validation Rules
- Basic-managed groups cannot be manually updated or deleted (403 Forbidden)
- Rules in basic-managed groups cannot be manually edited or deleted
- Entity keys must be from: Listing, CPU, GPU, RamSpec, StorageProfile, PortsProfile
- Clamp modifiers must have at least min_usd or max_usd
- min_usd cannot be greater than max_usd

### 3. API Endpoint Updates

#### Rule Groups Endpoints
- **POST `/api/v1/rule-groups`**: Accepts basic_managed and entity_key, validates and stores in metadata
- **PUT `/api/v1/rule-groups/{id}`**: Checks for basic-managed flag, prevents edits if set
- **GET `/api/v1/rule-groups`**: Returns basic_managed and entity_key in response
- **GET `/api/v1/rule-groups/{id}`**: Returns full metadata including basic fields

#### Rules Endpoints
- **POST `/api/v1/valuation-rules`**: Validates modifiers_json for actions
- **PUT `/api/v1/valuation-rules/{id}`**: Checks parent group for basic-managed flag
- **DELETE `/api/v1/valuation-rules/{id}`**: Prevents deletion from basic-managed groups

#### Ruleset Endpoints
- **GET `/api/v1/rulesets/{id}`**: Properly extracts and returns basic_managed and entity_key for nested groups

### 4. Data Storage

The implementation uses the existing `metadata_json` field in `ValuationRuleGroup` to store:
```json
{
  "basic_managed": true,
  "entity_key": "CPU",
  "other_metadata": "..."
}
```

The existing `modifiers_json` field in `ValuationRuleAction` stores:
```json
{
  "clamp": true,
  "min_usd": 50.0,
  "max_usd": 200.0,
  "explanation": "CPU benchmark adjustment",
  "formula_notes": "$10 per 1000 CPU Mark points",
  "unit": "multiplier"
}
```

## Usage Examples

### Creating a Basic-Managed Group

```python
POST /api/v1/rule-groups
{
  "ruleset_id": 1,
  "name": "Basic CPU Rules",
  "category": "cpu",
  "description": "CPU rules managed by Basic mode",
  "basic_managed": true,
  "entity_key": "CPU"
}
```

### Creating a Rule with Modifiers

```python
POST /api/v1/valuation-rules
{
  "group_id": 1,
  "name": "CPU Performance Rule",
  "actions": [{
    "action_type": "per_unit",
    "metric": "cpu_mark",
    "value_usd": 10.0,
    "modifiers": {
      "clamp": true,
      "min_usd": 50.0,
      "max_usd": 500.0,
      "explanation": "CPU performance adjustment",
      "unit": "multiplier"
    }
  }]
}
```

## Error Handling

### Basic-Managed Protection
```
PUT /api/v1/rule-groups/{basic_managed_group_id}
Response: 403 Forbidden
{
  "detail": "Cannot update basic-managed rule groups. These groups are automatically managed by the Basic mode interface."
}
```

### Invalid Entity Key
```
POST /api/v1/rule-groups
{
  "entity_key": "InvalidEntity"
}
Response: 400 Bad Request
{
  "detail": "Invalid entity_key: 'InvalidEntity'. Must be one of: CPU, GPU, Listing, PortsProfile, RamSpec, StorageProfile"
}
```

### Invalid Modifiers
```
POST /api/v1/valuation-rules
{
  "actions": [{
    "modifiers": {
      "clamp": true
      // Missing min_usd and max_usd
    }
  }]
}
Response: 400 Bad Request
{
  "detail": "When 'clamp' is true, at least one of 'min_usd' or 'max_usd' must be specified"
}
```

## Testing

Tests are provided in `/tests/test_rules_basic_mode_extensions.py` covering:
- Creating groups with basic_managed and entity_key
- Validation of entity keys
- Prevention of manual edits to basic-managed groups
- Rule creation with modifiers
- Modifiers validation
- Full ruleset retrieval with metadata

## Migration Notes

No database migrations are required as this implementation uses existing JSON columns:
- `ValuationRuleGroup.metadata_json` - Already exists
- `ValuationRuleAction.modifiers_json` - Already exists

## Future Considerations

1. **Baseline Ingestion Integration**: The baseline ingestion process should set `basic_managed=true` and appropriate `entity_key` when creating groups
2. **UI Integration**: The frontend should check `basic_managed` flag to disable edit/delete buttons
3. **Audit Trail**: Consider adding specific audit events for basic-managed operations
4. **Permissions**: Could integrate with permission system to enforce basic-managed constraints at a higher level