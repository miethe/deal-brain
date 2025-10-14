# Valuation Rules: Mode Switching Guide

**Last Updated:** 2025-10-14
**Audience:** Deal Brain users working with valuation rules
**Related Guides:** [Basic Valuation Mode](basic-valuation-mode.md), [Valuation Rules](valuation-rules.md)

---

## Table of Contents

1. [Overview of Basic vs Advanced Mode](#overview-of-basic-vs-advanced-mode)
2. [Preparing Baseline Rules for Advanced Editing](#preparing-baseline-rules-for-advanced-editing)
3. [Understanding Expanded Rules](#understanding-expanded-rules)
4. [Best Practices](#best-practices)
5. [FAQ](#faq)
6. [Troubleshooting](#troubleshooting)

---

## Overview of Basic vs Advanced Mode

Deal Brain's Valuation Rules system offers two distinct interfaces for managing pricing adjustments: **Basic Mode** and **Advanced Mode**. Understanding when and how to use each mode will help you configure valuations efficiently.

### Basic Mode

**Purpose:** Simplified interface for common valuation adjustments without needing to understand rule concepts.

**Best For:**
- New users getting started with valuations
- Quick adjustments to common factors (RAM, storage, condition)
- Standard use cases with straightforward pricing logic
- Users who prefer a streamlined, form-based interface

**Key Features:**
- Pre-configured baseline fields (DDR generation, RAM capacity, condition, etc.)
- Simple override controls using multipliers and fixed values
- No need to manage conditions, actions, or rule hierarchy
- Immediate visual feedback with clear labels

**Example Use Case:**
> "I want used listings to get a 20% deduction and listings with DDR5 RAM to get a 30% premium."

### Advanced Mode

**Purpose:** Full control over rule hierarchy, conditions, actions, and evaluation logic.

**Best For:**
- Power users needing complex conditional logic
- Custom rules beyond baseline fields
- Fine-tuning individual rule conditions and actions
- Managing rule priority and evaluation order
- Creating rules based on multiple conditions (AND/OR logic)

**Key Features:**
- Complete rule hierarchy (Rulesets → Rule Groups → Rules)
- Custom conditions with multiple operators (equals, greater than, contains, etc.)
- Multiple action types (fixed value, per-unit, formula-based)
- Rule priority and evaluation order control
- Nested condition groups with AND/OR logic

**Example Use Case:**
> "I want to apply a $75 deduction only if the listing has 8GB RAM AND is in used condition, but apply a $100 deduction if it's for parts."

### Prerequisites

Before working with valuation rules, ensure:
- You have a basic understanding of how Deal Brain calculates adjusted prices
- You have the necessary permissions to edit valuation rules (admin or rule manager role)
- At least one active ruleset exists in your system

---

## Preparing Baseline Rules for Advanced Editing

When you create rules in Basic Mode, Deal Brain stores them as **placeholder rules** — simplified representations optimized for the Basic Mode interface. To edit these rules in Advanced Mode with full flexibility, you need to **prepare** (or "hydrate") them first.

### What is Hydration?

**Hydration** is the process of converting placeholder baseline rules into fully expanded rule structures that can be edited in Advanced Mode.

**Why is it needed?**
- Placeholder rules store configuration as metadata (multipliers, formulas) but don't have executable conditions and actions
- Advanced Mode requires complete rule structures with explicit conditions and actions
- Hydration preserves your existing valuation logic while making it editable at a granular level

**Important:** Hydration does NOT change your valuation calculations. Adjusted prices remain identical before and after hydration.

### Step-by-Step Hydration Guide

Follow these steps to prepare baseline rules for Advanced Mode editing:

#### Step 1: Switch to Advanced Mode

1. Navigate to the **Valuation Rules** page
2. Select your active ruleset from the dropdown (if multiple rulesets exist)
3. Click the **"Advanced"** tab at the top of the page

#### Step 2: Check for Hydration Banner

If your ruleset contains non-hydrated baseline rules, you'll see a blue banner at the top of the page:

```
ℹ️ Baseline Rules Need Preparation

Baseline rules are currently in placeholder mode. To edit them in Advanced mode,
they need to be converted to full rule structures.

[Prepare Baseline Rules for Editing]
```

**If you don't see this banner:**
- Your rules are already hydrated, or
- Your ruleset doesn't contain baseline placeholder rules (it was created in Advanced Mode)

#### Step 3: Prepare Rules

1. Click the **"Prepare Baseline Rules for Editing"** button
2. The button will show a loading state: "Preparing Rules..."
3. Hydration typically completes in 1-3 seconds

#### Step 4: Verify Hydration Success

After hydration completes, you'll see:

1. **Success notification:**
   ```
   ✓ Baseline Rules Prepared
   Created 18 rules from 12 baseline fields.
   ```

2. **Banner disappears** — The hydration prompt is no longer visible

3. **Rules list updates** — Your rules now show:
   - Explicit conditions (e.g., "DDR Generation = DDR4")
   - Non-zero action values
   - Multiple rules for enum fields (e.g., separate rules for DDR3, DDR4, DDR5)

4. **Rules are now editable** — You can click "Edit" on any rule to modify conditions and actions

**Example Before and After:**

| Before Hydration | After Hydration |
|------------------|-----------------|
| **DDR Generation** (1 rule)<br>Conditions: None<br>Actions: Multiplier (0.0) | **DDR Generation: DDR3**<br>Condition: DDR Gen = DDR3<br>Action: Multiplier 0.7x<br><br>**DDR Generation: DDR4**<br>Condition: DDR Gen = DDR4<br>Action: Multiplier 1.0x<br><br>**DDR Generation: DDR5**<br>Condition: DDR Gen = DDR5<br>Action: Multiplier 1.3x |

### What Happens During Hydration?

The hydration process expands placeholder rules based on their type:

1. **Enum Multiplier Fields** (e.g., DDR Generation, Condition)
   - Creates one rule per enum value
   - Each rule gets a condition matching one specific value
   - Multiplier values are converted and preserved

2. **Formula Fields** (e.g., RAM Capacity calculation)
   - Creates a single rule with a formula action
   - Formula text is preserved from metadata
   - No conditions (applies to all listings)

3. **Fixed Value Fields** (e.g., Base depreciation)
   - Creates a single rule with a fixed value action
   - Value is populated from the default value
   - No conditions (applies to all listings)

**Technical Details:**
- Original placeholder rules are marked as inactive (not deleted)
- Expanded rules link back to the original via metadata (`hydration_source_rule_id`)
- You can see which rules came from hydration by checking rule metadata (if enabled in UI)

---

## Understanding Expanded Rules

After hydration, you'll notice your rule count has increased. This is expected behavior. Here's what to know:

### Rule Expansion Examples

#### Example 1: DDR Generation (Enum Multiplier)

**Original Placeholder Rule:**
- Name: DDR Generation
- Valuation buckets: `{ ddr3: 0.7, ddr4: 1.0, ddr5: 1.3 }`
- Conditions: None
- Actions: Multiplier (placeholder)

**Expanded Rules (3 rules):**

1. **DDR Generation: DDR3**
   - Condition: `ram_spec.ddr_generation equals ddr3`
   - Action: Multiplier 70.0% (0.7 × 100)

2. **DDR Generation: DDR4**
   - Condition: `ram_spec.ddr_generation equals ddr4`
   - Action: Multiplier 100.0% (1.0 × 100)

3. **DDR Generation: DDR5**
   - Condition: `ram_spec.ddr_generation equals ddr5`
   - Action: Multiplier 130.0% (1.3 × 100)

**Why expand?** Each rule is now independently editable. You can adjust the DDR4 multiplier without affecting DDR3 or DDR5.

#### Example 2: RAM Capacity (Formula Field)

**Original Placeholder Rule:**
- Name: Total RAM Capacity
- Formula: `ram_capacity_gb * base_price_per_gb`
- Conditions: None
- Actions: Formula (placeholder)

**Expanded Rule (1 rule):**
- **Total RAM Capacity**
  - Condition: None (always applies)
  - Action: Formula `ram_capacity_gb * base_price_per_gb`

**Why one rule?** Formulas already support complex logic, so no expansion is needed. The formula is now editable in the Advanced Mode formula builder.

#### Example 3: Base Depreciation (Fixed Value)

**Original Placeholder Rule:**
- Name: Base Depreciation
- Default value: -50.00
- Conditions: None
- Actions: Fixed value (placeholder)

**Expanded Rule (1 rule):**
- **Base Depreciation**
  - Condition: None (always applies)
  - Action: Fixed value -$50.00

**Why one rule?** Fixed values are simple and don't require expansion. The value is now directly editable.

### Metadata Linking

Each expanded rule maintains a link to its original placeholder:

- **Hydration source:** `hydration_source_rule_id` points to the original rule ID
- **Hydration timestamp:** `hydrated_at` records when expansion occurred
- **Hydration actor:** `hydrated_by` records who triggered hydration

This metadata enables:
- Audit trails for compliance
- Potential future "dehydration" (reverting to placeholders)
- Understanding rule provenance

### What Happens to Placeholder Rules?

After hydration:
- **Original placeholder rules are deactivated** (`is_active = false`)
- They remain in the database for audit purposes
- They are NOT visible in the Advanced Mode UI
- They are marked as `hydrated: true` to prevent re-expansion

**Note:** Placeholder rules are never deleted. This ensures you have a complete history of changes.

---

## Best Practices

Follow these recommendations for smooth mode switching and rule management:

### When to Hydrate Rules

**Hydrate when:**
- ✅ You need to make changes beyond Basic Mode capabilities
- ✅ You need to add complex conditions (AND/OR logic)
- ✅ You want to customize individual enum values (e.g., adjust DDR4 multiplier only)
- ✅ You need to create rules with multiple conditions
- ✅ You're ready to commit to Advanced Mode for this ruleset

**Don't hydrate if:**
- ❌ You're just exploring Advanced Mode and not ready to edit
- ❌ Basic Mode meets all your needs
- ❌ You're unsure about the changes you want to make

**Tip:** Hydration is a one-way process (without dehydration feature). Make sure you're ready before clicking "Prepare Rules."

### How to Verify Hydration Was Successful

After hydration, check:

1. **Rule Count Increased:**
   - Look at the "X rules" count in each Rule Group
   - Enum fields should show multiple rules (one per value)

2. **Conditions Are Populated:**
   - Click on a rule to expand it
   - Verify conditions show field paths and values (not empty)

3. **Action Values Are Non-Zero:**
   - Check that multipliers, fixed values, or formulas are displayed
   - Values should match what was configured in Basic Mode

4. **Valuations Unchanged:**
   - Go to Listings page
   - Verify adjusted prices haven't changed
   - Check valuation breakdown modal for consistency

5. **Success Notification Received:**
   - Look for the green toast: "Baseline Rules Prepared"
   - Note the count: "Created X rules from Y baseline fields"

### Managing Expanded Rules

**Organizing Rules:**
- Expanded rules are automatically grouped in their original Rule Group
- Use Rule Group names to stay organized (e.g., "RAM Adjustments", "Storage Adjustments")
- Consider adding rule descriptions to explain custom logic

**Editing Rules:**
- Click "Edit" on any rule to open the Rule Builder modal
- Changes are saved immediately (with version history)
- Use "Duplicate" to create variations of existing rules

**Monitoring Impact:**
- Use the "Preview Impact" feature (if available) to test rule changes
- Check valuation breakdowns on sample listings before publishing changes
- Monitor adjusted prices after rule changes

**Archiving Rules:**
- Instead of deleting, use the "Disable" toggle to deactivate rules
- Disabled rules are not evaluated but remain in the system
- You can re-enable rules at any time

### Switching Between Modes Safely

**Basic → Advanced:**
1. Make sure you're ready to hydrate (see "When to Hydrate Rules" above)
2. Save any unsaved changes in Basic Mode first
3. Switch to Advanced and hydrate when prompted
4. Verify rules appear correctly

**Advanced → Basic:**
1. If rules have been hydrated, Basic Mode will show one of:
   - **Read-only fields** with "Managed in Advanced Mode" label
   - **Warning banner** explaining that editing requires Advanced Mode
2. Non-hydrated fields (if any) remain editable in Basic Mode
3. To make changes, return to Advanced Mode

**Important:** Once hydrated, a ruleset is primarily managed in Advanced Mode. Basic Mode becomes view-only for those fields.

### Backup and Recovery

**Before making major changes:**
1. **Export your ruleset** (if export feature is available)
   - Go to Ruleset settings
   - Click "Export" to download a JSON package
   - Store the export file safely

2. **Document your changes** (recommended for compliance)
   - Note the date and reason for changes
   - Record original values before editing
   - Keep a changelog for audit purposes

3. **Test on a copy** (if possible)
   - Duplicate the ruleset
   - Make changes on the copy first
   - Verify impact before applying to production ruleset

**If something goes wrong:**
- Check the audit log (if available) to see recent changes
- Contact your system administrator for database-level recovery
- Re-import a previously exported ruleset package

---

## FAQ

### Can I undo hydration?

**Short answer:** Not yet. Hydration is currently a one-way process.

**Details:** Once rules are hydrated, they remain expanded in Advanced Mode. The original placeholder rules are deactivated but not deleted. A future "dehydration" feature (Phase 5 in the roadmap) may allow reverting to Basic Mode format.

**Workaround:** If you need to revert, you can:
1. Manually recreate the ruleset in Basic Mode
2. Import a previously exported ruleset package (if you have a backup)
3. Contact support for database-level restoration

### Will hydration affect my listing valuations?

**No.** Hydration is designed to be valuation-neutral. The adjusted prices for your listings should remain exactly the same before and after hydration.

**How we ensure this:**
- Hydration converts metadata into equivalent rule structures
- Multipliers are preserved (e.g., 0.7x becomes 70.0% in action value)
- Conditions match the original logic
- Formulas are copied verbatim
- All rules use the same evaluation order

**Verification:** After hydration, check a few sample listings to confirm adjusted prices are unchanged.

### How do I know if rules are already hydrated?

**Visual indicators:**
1. **No hydration banner** — If you don't see the "Baseline Rules Need Preparation" banner in Advanced Mode, rules are likely hydrated or not baseline rules
2. **Multiple rules for enum fields** — Hydrated enum fields show separate rules for each value (e.g., DDR3, DDR4, DDR5)
3. **Populated conditions** — Rules have conditions filled in (not empty)
4. **Non-zero action values** — Actions show actual values instead of 0.0

**Technical check:**
- Look at rule metadata (if exposed in UI)
- Check for `hydrated: true` flag
- Check for `hydration_source_rule_id` linking

### Can I edit individual enum values after hydration?

**Yes!** That's one of the main benefits of hydration.

**Example:**
After hydrating the "DDR Generation" field, you can:
- Edit the DDR4 multiplier from 1.0x to 1.05x
- Change the DDR3 condition to target a different field
- Add additional conditions (e.g., "DDR4 AND 16GB or more")

Each expanded rule is fully independent and editable.

### What happens to foreign key rules?

**Foreign key rules** (e.g., rules linked to RAM Spec or GPU catalog entries) are system-managed and cannot be edited directly in Advanced Mode.

**Behavior:**
- These rules are **hidden by default** in Advanced Mode
- They are marked with `is_foreign_key_rule: true` in metadata
- They are not included in hydration
- They continue to apply during valuation calculations

**Optional:** Some systems may offer a "Show System Rules" toggle to reveal foreign key rules for viewing (read-only).

### Can I hydrate only specific rules?

**Not currently.** The hydration process operates at the **ruleset level**, meaning all placeholder baseline rules in the ruleset are hydrated at once.

**Roadmap:** A future enhancement may allow selective rule hydration, but this is not currently supported.

**Workaround:** If you need granular control:
1. Create separate rulesets for different rule groups
2. Hydrate only the rulesets you need to edit
3. Use ruleset conditions to control which ruleset applies to which listings

### What if I need to add a new enum value after hydration?

**Scenario:** You hydrated "DDR Generation" (DDR3, DDR4, DDR5), and now DDR6 is released.

**Solution:**
1. **Manual approach:**
   - Go to Advanced Mode
   - Click "Add Rule" in the appropriate Rule Group
   - Create a new rule: "DDR Generation: DDR6"
   - Set condition: `ram_spec.ddr_generation equals ddr6`
   - Set action: Multiplier 1.5x (or appropriate value)

2. **Re-hydration approach (if supported):**
   - Update the baseline field metadata with the new enum value
   - Trigger re-hydration to create the new rule automatically
   - *(Note: Re-hydration feature may not be available in initial release)*

**Best practice:** Document new enum values and update relevant rules promptly.

### Can I switch rulesets after hydration?

**Yes.** Hydration is specific to a ruleset, not a global setting. You can:
- Hydrate Ruleset A and leave Ruleset B in placeholder mode
- Switch between rulesets using the dropdown selector
- Apply different rulesets to different listings

**Example use case:**
- Ruleset A (hydrated): Complex rules for high-end gaming PCs
- Ruleset B (placeholder): Simple rules for budget office PCs

### Will hydration slow down valuation calculations?

**No significant impact.** While hydration increases the number of rules, the performance impact is minimal:

**Factors:**
- Rule evaluation is optimized and fast (typically <100ms per listing)
- Increased rule count is offset by more specific conditions (fewer matches per listing)
- Evaluation order ensures rules are checked sequentially and short-circuit on matches

**Benchmark:** A typical ruleset with 50-100 rules processes listings with no noticeable delay.

---

## Troubleshooting

### Problem: Hydration Banner Doesn't Appear

**Symptoms:**
- You switch to Advanced Mode
- No "Baseline Rules Need Preparation" banner is visible
- You expected to see placeholder rules

**Possible Causes & Solutions:**

1. **Rules are already hydrated**
   - Check if rules have conditions and non-zero actions
   - Look for multiple rules per enum field (e.g., DDR3, DDR4, DDR5)
   - **Solution:** No action needed — your rules are ready for editing

2. **Ruleset was created in Advanced Mode**
   - If the ruleset was never managed in Basic Mode, it doesn't have placeholder rules
   - **Solution:** No action needed — you can edit rules directly

3. **No baseline rules in ruleset**
   - The ruleset may only contain custom Advanced Mode rules
   - **Solution:** Verify you selected the correct ruleset from the dropdown

4. **Browser cache issue**
   - Stale data may be cached
   - **Solution:** Refresh the page (Ctrl+R or Cmd+R)

### Problem: Hydration Button is Disabled

**Symptoms:**
- Hydration banner appears
- "Prepare Baseline Rules for Editing" button is greyed out
- You cannot click the button

**Possible Causes & Solutions:**

1. **Hydration is in progress**
   - The button automatically disables during processing
   - **Solution:** Wait for hydration to complete (1-3 seconds)

2. **Insufficient permissions**
   - You may not have permission to edit valuation rules
   - **Solution:** Contact your administrator to grant rule editing permissions

3. **Ruleset is inactive**
   - Inactive rulesets may not allow hydration
   - **Solution:** Activate the ruleset in Ruleset settings, then try again

4. **JavaScript error**
   - Check browser console (F12) for errors
   - **Solution:** Refresh the page; if error persists, report to support

### Problem: Error During Hydration

**Symptoms:**
- You click "Prepare Baseline Rules for Editing"
- Error toast appears: "Hydration Failed"
- Rules remain in placeholder state

**Possible Causes & Solutions:**

1. **Network connectivity issue**
   - Request to server failed
   - **Solution:** Check your internet connection and try again

2. **Invalid rule data**
   - Placeholder rules may have corrupted metadata
   - **Solution:** Check the error message for details; contact support if needed

3. **Database constraint violation**
   - Rare issue with rule naming or constraints
   - **Solution:** Contact support with the error message

4. **Server timeout**
   - Ruleset is very large and hydration takes too long
   - **Solution:** Contact support to increase timeout or optimize ruleset

**General troubleshooting steps:**
1. Refresh the page and try again
2. Check browser console (F12) for detailed error messages
3. Try hydrating a different (smaller) ruleset to isolate the issue
4. Contact support with:
   - Ruleset ID
   - Error message from toast
   - Browser console errors (screenshot)

### Problem: Rules Not Showing in Advanced Mode After Hydration

**Symptoms:**
- Hydration appears to succeed (success toast displayed)
- Banner disappears
- But rules list is empty or doesn't update

**Possible Causes & Solutions:**

1. **UI refresh issue**
   - React Query cache may not have invalidated
   - **Solution:** Refresh the page (Ctrl+R or Cmd+R)

2. **Filters applied**
   - Search or filter may be hiding rules
   - **Solution:** Clear search box and reset filters

3. **Rules in wrong Rule Group**
   - Rules may have been created in a different group
   - **Solution:** Check all Rule Groups (expand each one)

4. **Foreign key rules only**
   - If all rules are foreign key rules, they are hidden by default
   - **Solution:** Enable "Show System Rules" toggle (if available)

**Verification steps:**
1. Check rule count in Rule Group headers (should have increased)
2. Use search to find specific rule names (e.g., "DDR3")
3. Check API response directly (browser Network tab, look for `/valuation-rules` request)

### Problem: Valuations Changed After Hydration

**Symptoms:**
- After hydration, adjusted prices on listings are different
- Valuation breakdowns show different amounts

**This should NOT happen.** Hydration is designed to be valuation-neutral.

**Possible Causes:**

1. **Bug in hydration logic**
   - Multiplier conversion error
   - Condition logic mismatch
   - **Action:** Report to support immediately with:
     - Listing ID with changed valuation
     - Ruleset ID
     - Before/after screenshots of valuation breakdown

2. **Concurrent ruleset changes**
   - Someone else edited rules during hydration
   - **Action:** Check audit log for recent changes; revert if needed

3. **Unrelated rule activation**
   - Other rules may have been activated coincidentally
   - **Action:** Review recent rule changes in audit log

**Immediate steps:**
1. Document the discrepancy (screenshots, listing IDs, amounts)
2. Check if only specific listings are affected or all listings
3. Review recent audit log entries
4. Contact support urgently
5. Consider reverting to a backup if available

### Problem: Basic Mode Shows "Managed in Advanced Mode" for All Fields

**Symptoms:**
- You switch to Basic Mode after hydration
- All fields show "Managed in Advanced Mode" or are disabled
- You cannot make any edits in Basic Mode

**This is expected behavior after hydration.**

**Explanation:**
- Hydrated rules are managed at the Advanced Mode level
- Basic Mode is now read-only for hydrated fields
- This prevents conflicts between modes

**Solutions:**

1. **Edit in Advanced Mode:**
   - Switch back to Advanced Mode
   - Make changes to individual rules
   - This is the recommended approach

2. **Create a new ruleset:**
   - If you need Basic Mode functionality again, create a new ruleset
   - Configure it in Basic Mode (don't hydrate)
   - Switch listings to use the new ruleset

3. **Dehydrate rules (if available):**
   - Check for "Revert to Basic Mode" feature in future releases
   - This feature is not yet available but planned for Phase 5

### Problem: Too Many Rules After Hydration

**Symptoms:**
- Hydration creates dozens or hundreds of rules
- Advanced Mode UI becomes cluttered
- Difficult to find specific rules

**This can happen with many enum multiplier fields.**

**Solutions:**

1. **Use search and filters:**
   - Use the search box to find specific rules (e.g., search "DDR")
   - Filter by Rule Group to narrow down the list

2. **Collapse Rule Groups:**
   - Click the collapse arrow on Rule Group headers
   - Keep only relevant groups expanded

3. **Reorganize Rule Groups:**
   - Consider splitting large groups into smaller, focused groups
   - Use descriptive group names

4. **Review necessity:**
   - Do you really need all enum values to be separately editable?
   - If not, consider reverting to Basic Mode for simpler use cases

**Future enhancement:** Rule grouping by parent field will improve UI organization.

---

## Additional Resources

- **[Basic Valuation Mode Guide](basic-valuation-mode.md)** — Learn how to use Basic Mode effectively
- **[Valuation Rules Guide](valuation-rules.md)** — Deep dive into Advanced Mode features
- **[Architecture Documentation](../architecture/valuation-rules.md)** — Technical details for developers
- **[PRD: Basic to Advanced Transition](../project_plans/valuation-rules/basic-to-advanced-transition/basic-to-advanced-transition-prd.md)** — Product requirements and design decisions
- **[ADR-0003: Baseline Rule Hydration Strategy](../architecture/adr/0003-baseline-rule-hydration-strategy.md)** — Architectural decision record

---

## Feedback and Support

If you encounter issues not covered in this guide:

1. **Check the FAQ section** above
2. **Search the documentation** for related topics
3. **Contact support** with detailed information:
   - Ruleset ID and name
   - Steps to reproduce the issue
   - Screenshots of the problem
   - Browser console errors (if applicable)

**Documentation feedback:** Help us improve this guide by reporting:
- Unclear sections
- Missing information
- Errors or inaccuracies
- Suggestions for new examples

---

**Document Version:** 1.0
**Last Updated:** 2025-10-14
**Related Features:** Valuation Rules, Baseline Hydration, Mode Switching
