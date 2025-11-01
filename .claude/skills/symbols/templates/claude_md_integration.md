# Agent Delegation Strategy

## Before Implementing: Explore First

**Always explore the codebase before building new features:**

```markdown
Task("codebase-explorer", "Find all existing [pattern] implementations to understand current conventions")
```

### Symbols vs Explore: Decision Framework

Based on validation testing (see `docs/testing/symbols_vs_explore_validation_report.md`):

**Use codebase-explorer (80% of tasks - 0.1s):**

- Quick "what and where" discovery (symbols-based)
- Finding specific functions/classes/components
- Getting file:line references
- Cost/speed critical tasks
- **Performance**: ~100+ symbols from multiple files in 0.1 seconds
- **Cost**: ~$0.001 per query

**Use explore subagent (20% of tasks - 2-3 min):**

- Understanding "how and why" with full context
- Generating implementation plans or ADRs
- Complex architectural analysis
- Test coverage and pattern analysis
- **Performance**: 300+ files analyzed in 2-3 minutes
- **Cost**: ~$0.01-0.02 per query

**Optimal Workflow (Phase 1 → Phase 2):**

```markdown
# Phase 1: Quick Discovery (0.1s) - ALWAYS START HERE
Task("codebase-explorer", "Find all [pattern] implementations")
→ Get instant symbol inventory
→ Identify key files

# Phase 2: Deep Analysis (2-3 min) - ONLY IF NEEDED
Task("explore", "Analyze [pattern] in [specific files from Phase 1]")
→ Get full context and patterns
```

### Symbol System for Token Efficiency

The codebase-explorer uses the {{PROJECT_NAME}} symbols system for **95-99% token reduction**:

- **Symbols**: Pre-generated metadata about all functions, classes, components, and types
- **Domain Chunking**: Separated by domain for targeted loading
- **Precise References**: Get exact file:line locations for navigation
- **Architectural Awareness**: Symbols tagged by layer for intelligent filtering
- **Test Separation**: Load test context only when debugging

**Performance Comparison:**

| Metric | Symbols (codebase-explorer) | Explore Subagent |
|--------|----------------------------|------------------|
| Duration | 0.1 seconds | 2-3 minutes |
| Best For | "What and where" | "How and why" |
| Token Efficiency | 95-99% reduction | Full context |
| Cost | ~$0.001 | ~$0.01-0.02 |

**Token Efficiency Example:**

```text
Traditional Approach:
- Read 5-10 similar files: ~200KB context
- Load related utilities: ~50KB context
Total: ~250KB

Symbol-Based Approach (via codebase-explorer):
- Query 20 relevant symbols: ~5KB context (0.1s)
- Load supporting context (15 symbols): ~3KB context
- On-demand lookups (10 symbols): ~2KB context
Total: ~10KB context (96% reduction)

Deep Analysis Approach (via explore):
- Analyze 300+ files: ~10,000+ LOC (2-3 min)
- Full patterns with code snippets: Complete context
```

**How it works:**

1. You delegate to codebase-explorer: `Task("codebase-explorer", "Find Button patterns")`
2. Codebase-explorer queries symbol files (token-efficient metadata)
3. You receive curated results with file:line references
4. You read only the specific files you need
5. If you need deeper understanding, delegate to explore with specific targets

**Key Insight**: Use symbols for 80% of quick lookups, reserve explore for 20% requiring deep understanding.

### Symbol Files

{{SYMBOL_FILES_SECTION}}

**All symbols include architectural layer tags** for intelligent filtering:
{{LAYER_TAGS}}

**See**: `/docs/development/symbols-best-practices.md` for comprehensive guidance.
