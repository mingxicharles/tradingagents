# Documentation

**Essential documentation for the Trading Agents system**

---

## Documents

### 1. [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) - Complete System Reference
**Start here for understanding the system.**

**Contents:**
- System overview and architecture
- Both workflows (Orchestrator + Controller)
- Key data models with examples
- Visual diagrams and quick reference
- Usage examples and troubleshooting
- Performance metrics and costs

**When to read:** First-time users, developers integrating the system, anyone needing a complete reference

---

### 2. [ARCHITECTURE_RECOMMENDATIONS.md](./ARCHITECTURE_RECOMMENDATIONS.md) - Industry Best Practices
**Answers critical architecture questions based on production research.**

**Contents:**
- Is Orchestrator redundant? (No - keep both, use strategically)
- Dynamic prompts vs templates? (Templates = 90% cost savings)
- Runtime LLM evaluation? (No - use rules, LLM offline only)
- Complete cost analysis and implementation plan
- Research from Microsoft, Google, OpenAI, Anthropic, Netflix, Uber

**When to read:** Making architecture decisions, optimizing costs, preparing for production

---

### 3. [CODEBASE_ANALYSIS.md](./CODEBASE_ANALYSIS.md) - Bug Fixes & Code Review
**Documents all bugs found and fixed during comprehensive code review.**

**Contents:**
- 5 critical bugs identified and fixed
- Missing model definitions (DebateTranscript, PositionChange)
- Model field mismatches (AgentProposal, DecisionDTO)
- Code quality assessment (7.5/10)
- Recommendations for future improvements

**When to read:** Understanding what was broken, reviewing code changes, preventing similar issues

---

## Quick Navigation

**I want to...**

- **Understand the system** → [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md)
- **Use the system** → [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) → Usage Examples
- **Optimize for production** → [ARCHITECTURE_RECOMMENDATIONS.md](./ARCHITECTURE_RECOMMENDATIONS.md)
- **Know what was fixed** → [CODEBASE_ANALYSIS.md](./CODEBASE_ANALYSIS.md)
- **Make architecture decisions** → [ARCHITECTURE_RECOMMENDATIONS.md](./ARCHITECTURE_RECOMMENDATIONS.md)

---

## Key Takeaways

### System Architecture
- **Two orchestration modes:** Orchestrator (production, 90%) + Controller (research, 10%)
- **Three specialized agents:** News, Technical, Fundamental
- **Debate mechanism:** Resolves conflicts through multi-round deliberation
- **Dual LLM support:** Local models (HuggingFace) + API (OpenAI/OpenRouter)

### Production Recommendations
1. **Use Orchestrator as primary** (rule-based, fast, cheap)
2. **Use templates, not dynamic prompts** (90% cost savings)
3. **Use rules for runtime coordination** (LLM evaluation offline only)
4. **Expected savings:** 71% cost reduction with hybrid approach

### Bug Fixes Applied
- ✅ Added missing `DebateTranscript` and `PositionChange` classes
- ✅ Fixed `AgentProposal` missing `caveats` and `raw_response` fields
- ✅ Created proper `DecisionDTO` class (was alias causing errors)
- ✅ All imports now work correctly
- ✅ System is functional and ready for use

---

## Document Sizes

```
SYSTEM_GUIDE.md                    19KB  (Complete reference)
ARCHITECTURE_RECOMMENDATIONS.md    30KB  (Industry best practices)
CODEBASE_ANALYSIS.md               14KB  (Bug fixes report)
─────────────────────────────────────
Total:                             63KB
```

**Previous total:** 162KB (detailed docs)
**Consolidation:** 61% reduction, kept essential information

---

## Changelog

**2025-11-13**
- Consolidated 6 detailed docs into 1 comprehensive SYSTEM_GUIDE.md
- Moved all documentation to `docs/` directory
- Added ARCHITECTURE_RECOMMENDATIONS.md (industry research)
- Added CODEBASE_ANALYSIS.md (bug fixes)
- Removed redundant detailed workflow and schema docs
- 61% size reduction while preserving essential information

---

**Start with [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) for complete system documentation.**
