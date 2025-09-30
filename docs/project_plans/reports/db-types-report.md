# Database Types Report

## 1. Issue Summary

**Problem:**  
The backend is encountering a runtime error when attempting to insert values like `"usb_a"` into the `port_type` column of the `port` table. The error message is:

```
invalid input value for enum port_type: "usb_a"
```

**Root Cause:**  
- The `port_type` column in the database is defined as a PostgreSQL enum.
- The allowed values for this enum are set at the time of the initial migration.
- When new values (e.g., `"usb_a"`, `"usb_c"`, etc.) are added to the Python `PortType` enum, the database enum is not automatically updated.
- As a result, inserting new enum values not present in the database enum causes a failure, requiring a manual database migration to add the new values.

---

## 2. Backend Architecture Explanation

**Current Enum Handling:**
- The backend uses SQLAlchemy models, with fields like `port_type` mapped to Python enums (e.g., `PortType`).
- These enums are also mapped to PostgreSQL enums in the database schema via Alembic migrations.
- When the schema is first created, the enum values in the database match those in the Python code.
- If the Python enum is updated (new values added/removed), the database enum does not update automatically. A new migration must be created and applied to sync the database with the code.

**Implications:**
- This pattern is common in strongly-typed, relational database-backed systems.
- It ensures data integrity (only allowed values can be stored).
- However, it creates operational friction: every time a new enum value is needed, a migration is required, which can be error-prone and slow down development.

---

## 3. Recommendations for Future Improvements

**Goal:**  
Allow new types (for ports or any other field) to be added without requiring a database migration.

**General Ideas:**

1. **Use Strings Instead of Enums in the Database**
   - Store the type as a plain string (`VARCHAR`) in the database.
   - Enforce allowed values only at the application level (Python enums, validation).
   - This allows new types to be added in code without any DB migration.
   - Tradeoff: Slightly weaker data integrity at the DB level, but much more flexibility.

2. **Dynamic Lookup Tables**
   - Instead of enums, use a separate table (e.g., `port_type`) to store allowed types.
   - Reference this table via a foreign key.
   - New types can be added by inserting a row, not by altering the schema.
   - This is more flexible and still allows for referential integrity.

3. **Hybrid Approach**
   - Use a string field in the DB, but provide a management UI or API to add new types.
   - Optionally, cache allowed types in the application for validation.

4. **Schema-less or Semi-Structured Storage**
   - For highly dynamic fields, consider using JSONB columns (PostgreSQL) or a NoSQL store for that part of the data.
   - This is only recommended if the data model is expected to change frequently and unpredictably.

**Best Practice:**  
For most business applications, switching from DB enums to string fields (with application-level validation) is the simplest and most effective way to decouple code and schema changes, while still maintaining reasonable data quality.

---

**Summary:**  
The current enum pattern is robust but inflexible. Moving to string fields or lookup tables for type fields will allow you to add new types without DB migrations, improving developer velocity and reducing operational overhead.