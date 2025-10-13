# Basic Valuation Mode - User Guide

## Table of Contents

1. [Overview](#overview)
2. [Understanding Valuation Modes](#understanding-valuation-modes)
3. [Viewing Baseline Recommendations](#viewing-baseline-recommendations)
4. [Working with Overrides](#working-with-overrides)
5. [Preview Impact](#preview-impact)
6. [Reset to Baseline](#reset-to-baseline)
7. [Diff & Adopt (Admin)](#diff--adopt-admin)
8. [FAQs](#faqs)
9. [Troubleshooting](#troubleshooting)

## Overview

Basic Valuation Mode provides a simplified, curated approach to PC valuation using system-defined baseline rules. This mode is designed for users who want reliable valuations without the complexity of creating custom rules.

### Key Benefits

- **Curated Rules**: Professionally-designed valuation rules based on market analysis
- **Consistent Results**: Standardized valuations across all listings
- **Simple Overrides**: Easy adjustments without rule creation
- **Transparent Pricing**: Clear breakdown of all adjustments
- **Quick Setup**: Works immediately without configuration

## Understanding Valuation Modes

Deal Brain offers two valuation modes:

### Basic Mode (Recommended for Most Users)

- Uses system baseline rules
- Allows field-level overrides
- Simplified interface
- No rule creation required
- Automatic updates when baselines change

### Advanced Mode (Power Users)

- Full rule creation and editing
- Complex condition logic
- Custom formulas
- Group management
- Complete control over valuation logic

### Switching Modes

You can switch between Basic and Advanced modes at any time:

1. Navigate to **Settings** → **Valuation**
2. Select your preferred mode
3. Click **Save Changes**

**Note**: Switching modes does not delete any data. Advanced rules remain available when switching back.

## Viewing Baseline Recommendations

### Accessing Baseline Values

1. Navigate to **Rules** → **Basic Adjustments**
2. The interface displays entities in tabs:
   - **CPU**: Processor-specific adjustments
   - **GPU**: Graphics card adjustments
   - **RAM**: Memory configuration adjustments
   - **Storage**: Drive type and capacity adjustments
   - **Condition**: Quality-based adjustments
   - **Form Factor**: Size-based adjustments
   - **Peripherals**: Included accessories

### Understanding Field Types

Each entity contains different field types:

#### Scalar Fields ($)
Direct dollar amount adjustments:
- Example: `Intel Core i7-12700: -$50`
- Applied as-is to the listing price

#### Presence Fields (✓/✗)
Boolean checks for feature presence:
- Example: `Has Dedicated GPU: ✓`
- When checked, applies associated adjustment

#### Multiplier Fields (×)
Percentage-based adjustments:
- Example: `Premium Brand: 1.15×`
- Multiplies the base price (1.0 = no change, 1.15 = +15%)

#### Formula Fields (fx)
Complex calculations based on metrics:
- Example: `=(cpu_mark - 10000) * 0.01`
- Evaluated using listing properties

### Field Indicators

- **🔵 Baseline**: System-recommended value
- **🟢 Override**: Custom value you've set
- **🔴 Changed**: Recent modification pending save
- **⚠️ Warning**: Potential issue with value

## Working with Overrides

### Creating an Override

1. **Locate the Field**:
   - Select the appropriate entity tab
   - Find the field you want to override

2. **Enter Override Value**:
   - Click the field's input box
   - Enter your custom value
   - The field highlights to show override status

3. **Save Changes**:
   - Click **Save Overrides** at the bottom
   - Confirmation message appears
   - Changes apply immediately to evaluations

### Override Examples

#### Adjusting CPU Values
```
Baseline: Intel i5-11400 = -$75
Override: Intel i5-11400 = -$50
Result: All i5-11400 listings get $25 less discount
```

#### Modifying Condition Multipliers
```
Baseline: Fair Condition = 0.85×
Override: Fair Condition = 0.80×
Result: Fair condition items get additional 5% discount
```

#### Adding Storage Premiums
```
Baseline: 2TB NVMe = +$100
Override: 2TB NVMe = +$150
Result: 2TB NVMe drives add $50 more value
```

### Bulk Override Operations

For multiple overrides:

1. Make all desired changes across tabs
2. Review changes in the summary panel
3. Click **Save All** to apply simultaneously

### Override Validation

The system validates overrides to prevent errors:

- **Dollar amounts**: Must be valid numbers
- **Multipliers**: Must be between 0.0 and 2.0
- **Formulas**: Must use valid syntax and variables
- **Presence**: Must be true/false

## Preview Impact

### Understanding Impact Preview

Before saving overrides, preview their effect:

1. **Impact Summary Panel** (right sidebar):
   - Shows affected listings count
   - Displays price adjustment range
   - Lists specific changes

2. **Live Calculation**:
   - Updates as you type
   - Shows immediate feedback
   - No need to save first

### Impact Metrics

The preview displays:

- **Affected Listings**: Number of listings that will change
- **Average Adjustment**: Mean price change across listings
- **Min/Max Range**: Smallest and largest adjustments
- **Total Portfolio Impact**: Sum of all adjustments

### Example Impact Preview

```
Override: Intel i7-12700 from -$50 to -$75

Impact Preview:
- Affected Listings: 23
- Average Adjustment: -$25.00
- Range: -$25 to -$25
- Total Impact: -$575.00
```

### Testing Changes Safely

1. Enter override values
2. Review impact preview
3. If undesirable, click **Cancel**
4. No changes applied until **Save**

## Reset to Baseline

### Individual Field Reset

To reset a single field:

1. Click the **Reset** icon (↻) next to the field
2. Field returns to baseline value
3. Override indicator disappears
4. Save to apply reset

### Entity-Level Reset

To reset all fields in an entity:

1. Click **Reset Entity** in the tab header
2. Confirm in dialog
3. All overrides in that entity cleared
4. Baseline values restored

### Global Reset

To reset all overrides:

1. Click **Reset All to Baseline** (top toolbar)
2. Review affected fields in confirmation dialog
3. Click **Confirm Reset**
4. All overrides removed system-wide

### Reset Safety

- Reset operations can be undone before saving
- Recent values preserved in history
- Audit log tracks all reset operations

## Diff & Adopt (Admin)

### Overview

Administrators can update baseline rules using the Diff & Adopt workflow:

1. **Diff**: Compare current baseline with new version
2. **Review**: Examine all changes
3. **Adopt**: Selectively apply updates

### Generating a Diff

1. Navigate to **Admin** → **Baseline Management**
2. Click **Compare with New Baseline**
3. Select or upload new baseline file
4. System generates comprehensive diff

### Understanding the Diff View

The diff interface shows:

#### Change Categories
- **Added**: New fields in the baseline
- **Modified**: Changed values
- **Removed**: Deprecated fields

#### Change Visualization
```diff
CPU > Intel i5-11400:
- Baseline: -$75.00
+ Proposed: -$85.00
  Change: -$10.00 (13.3% increase)
```

### Selective Adoption

1. **Review Each Change**:
   - Check/uncheck individual changes
   - Use filters to focus on specific entities
   - Sort by impact magnitude

2. **Preview Combined Impact**:
   - See aggregate effect of selected changes
   - Review affected listing distribution
   - Analyze price shift patterns

3. **Apply Changes**:
   - Click **Adopt Selected Changes**
   - Confirm in dialog
   - System updates baseline atomically

### Adoption Best Practices

- Review high-impact changes carefully
- Consider market timing
- Document adoption rationale
- Notify team of baseline updates
- Monitor post-adoption metrics

## FAQs

### General Questions

**Q: Can I use both Basic and Advanced modes?**
A: Yes, you can switch between modes anytime. Your data persists across modes.

**Q: Do overrides affect all users?**
A: Yes, overrides are system-wide and affect all valuations immediately.

**Q: How often are baselines updated?**
A: Baselines are updated quarterly or as market conditions change.

**Q: Can I export my overrides?**
A: Yes, use **Export Overrides** to download as JSON for backup or sharing.

### Override Questions

**Q: What happens to overrides when baseline updates?**
A: Overrides persist through baseline updates. They continue to replace baseline values.

**Q: Can I see override history?**
A: Yes, navigate to **Audit Log** to see all override changes with timestamps.

**Q: Is there a limit to overrides?**
A: No hard limit, but performance may degrade with 1000+ overrides.

**Q: Can I override formulas?**
A: Yes, but ensure formula syntax is valid or evaluation will fail.

### Impact Questions

**Q: Why doesn't impact preview match actual results?**
A: Preview uses current data. If listings change between preview and save, results differ.

**Q: Can I undo after saving?**
A: Not directly, but you can reset to baseline or manually revert using audit log.

**Q: How fast do overrides apply?**
A: Immediately after save. Re-evaluation happens within seconds.

## Troubleshooting

### Common Issues

#### Override Not Applying

**Symptoms**: Override saved but listings unchanged

**Solutions**:
1. Check listing has the overridden component
2. Verify override syntax (especially formulas)
3. Ensure valuation is enabled for listing
4. Check for conflicting advanced rules

#### Impact Preview Not Loading

**Symptoms**: Preview panel shows loading indefinitely

**Solutions**:
1. Refresh the page
2. Check browser console for errors
3. Verify network connectivity
4. Try smaller override batches

#### Cannot Save Overrides

**Symptoms**: Save button disabled or errors

**Solutions**:
1. Check validation errors (red fields)
2. Verify you have edit permissions
3. Ensure all required fields have values
4. Check for concurrent editor conflicts

#### Baseline Not Visible

**Symptoms**: Entity tabs show no fields

**Solutions**:
1. Verify baseline is instantiated
2. Check Basic mode is enabled
3. Confirm baseline ruleset is active
4. Contact admin to verify setup

### Performance Issues

#### Slow Field Updates

**Solutions**:
1. Reduce number of open tabs
2. Clear browser cache
3. Disable browser extensions
4. Use Chrome/Edge for best performance

#### Laggy Impact Calculations

**Solutions**:
1. Wait for current calculation to complete
2. Make changes in smaller batches
3. Avoid complex formulas in many fields
4. Consider scheduling bulk updates off-hours

### Data Integrity

#### Unexpected Values

**Checks**:
1. Verify baseline hasn't changed
2. Check for active advanced rules
3. Review recent audit log entries
4. Confirm no concurrent editors

#### Missing Overrides

**Recovery**:
1. Check audit log for reset operations
2. Verify correct entity tab selected
3. Use export backup if available
4. Contact support with timestamp

### Getting Help

If issues persist:

1. **Document the Issue**:
   - Screenshot error messages
   - Note exact steps to reproduce
   - Record timestamp of occurrence

2. **Check Resources**:
   - Review this guide
   - Search knowledge base
   - Check system status page

3. **Contact Support**:
   - Use in-app support chat
   - Email: support@dealbrain.com
   - Include audit log excerpt

## Advanced Tips

### Keyboard Shortcuts

- `Tab`: Navigate between fields
- `Enter`: Save current field
- `Esc`: Cancel current edit
- `Ctrl+S`: Save all overrides
- `Ctrl+Z`: Undo last change (before save)

### Workflow Optimization

1. **Batch Similar Changes**:
   - Group related overrides
   - Apply systematic adjustments
   - Use patterns for consistency

2. **Document Rationale**:
   - Add notes to significant overrides
   - Track market research sources
   - Maintain decision log

3. **Monitor Metrics**:
   - Track override effectiveness
   - Review impact reports weekly
   - Adjust based on outcomes

### Integration Points

Basic mode integrates with:

- **Reporting**: Override impact in analytics
- **Alerts**: Notifications for baseline updates
- **API**: Programmatic override management
- **Exports**: Include override data

---

*Last Updated: January 2025*
*Version: 1.0.0*