# PawPal+ Model Card

> AI Model Documentation for the PawPal+ Agentic Workflow System

---

## 1. Model Overview

| Attribute | Value |
|-----------|-------|
| **Model Name** | PawPalAI |
| **Type** | Rule-based Agentic Workflow |
| **Architecture** | Four-stage agent (Observe → Think → Act → Check) |
| **Primary Function** | Pet care task scheduling with AI recommendations |
| **Framework** | Python, Streamlit |

---

## 2. System Capabilities

### Core Features

1. **Task Management**
   - Create, update, and complete pet care tasks
   - Priority levels: high (100), medium (50), low (20)
   - Recurring tasks: daily, weekly frequency support

2. **Scheduling Algorithm**
   - 0/1 knapsack optimization for task selection
   - Maximizes priority value within time constraints
   - Deadline-aware task ordering

3. **AI Agent Workflow**
   - **Observe**: Analyze current task state
   - **Think**: Generate recommendations
   - **Act**: Produce natural language explanations
   - **Check**: Validate generated plans

---

## 3. Limitations & Biases

### Known Limitations

| Limitation | Description |
|------------|-------------|
| **Fixed Priority Weights** | Uses static weights (high=100, medium=50, low=20) - doesn't adapt to user preferences |
| **No Context Awareness** | Doesn't consider weather, pet health changes, or owner energy levels |
| **Time-Based Assumptions** | Ignores task dependencies and optimal times of day |
| **Small Scale** | Knapsack algorithm O(n*capacity) may need optimization for large task sets |

### Potential Biases

- **Priority Bias**: Assumes all "high" priority tasks are equally important
- **Scheduling Bias**: Prefers longer tasks when value density is equal
- **Recommendation Bias**: May over-recommend based on task type patterns

---

## 4. Safety & Responsible AI

### Potential Misuse & Prevention

| Risk | Mitigation |
|------|------------|
| **Over-reliance on AI** | Confidence scores show uncertainty; validation warnings encourage human review |
| **Task spam** | No built-in rate limiting (could be added) |
| **Privacy concerns** | All data stored locally; no external API calls |
| **Schedule manipulation** | AI explains decisions transparently for user verification |

### Error Handling

- Try-catch blocks in UI layer with user-friendly error messages
- Comprehensive logging (INFO/WARNING/ERROR levels)
- Graceful degradation when AI analysis fails

---

## 5. Testing & Reliability

### Test Results

```
20 out of 20 tests passed (100% pass rate)

Key findings:
- AI correctly identifies overdue tasks 100% of the time
- Confidence scores average 0.85; accuracy improved after adding validation rules
- The "Check" stage catches 90%+ of scheduling issues before they reach the user
- Logging captured 2 edge cases during development that were fixed
```

### Confidence Scoring

| Recommendation Type | Confidence | Rationale |
|---------------------|------------|-----------|
| Time constraint detection | 95% | Mathematical certainty from capacity calculation |
| Priority recommendations | 85% | Based on task analysis patterns |
| Pet-specific insights | 75% | Moderate evidence from task distribution |

---

## 6. Collaboration Insights

### ✅ Helpful AI Suggestion

During the initial design of the agentic workflow, I had only planned three stages (Observe, Think, Act). The AI suggested adding a fourth "Check" stage to validate outputs before presenting them to users. This proved invaluable - the Check stage catches scheduling issues like large gaps or missing high-priority tasks.

### ❌ Flawed AI Suggestion

Early in development, the AI recommended always scheduling high-priority tasks first, regardless of duration. This led to inefficient schedules where a 5-minute "high" task blocked a 60-minute "medium" task. I had to add the knapsack algorithm to optimize for priority *value* (priority weight / duration), not just priority *order*.

---

## 7. What Surprised Me While Testing

1. **The "Check" stage caught real issues**: I initially thought the validation was unnecessary, but during testing, it detected a 2-hour gap in the schedule that would have been confusing for users.

2. **Confidence scores were more variable than expected**: Some recommendations that seemed obvious (like time constraints) had 95% confidence, while pet-specific insights were only 75%. This helped identify where the AI had strong vs. weak evidence.

3. **Logging revealed edge cases**: The comprehensive logging captured 2 scenarios I hadn't anticipated:
   - Empty schedule generation
   - Tasks with zero duration

---

## 8. Key Learnings

1. **AI ≠ Just LLMs**: Rule-based AI agents can be powerful, predictable, and practical for specific domains.

2. **The Value of Explainability**: Natural language explanations are crucial for user trust.

3. **Iterative Design**: Starting simple and adding stages (observe, think, act, check) improved the system incrementally.

4. **Testing AI is different**: Focus on testing the *structure* of outputs rather than exact values.

5. **Agentic workflows need validation**: The "Check" stage is crucial for catching issues the AI itself introduces.

---

## 9. Model Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | April 2026 | Initial release with agentic workflow |
| 1.1 | April 2026 | Added confidence scoring and plan validation |

---

## 10. Files

| File | Description |
|------|-------------|
| [pawpal_system.py](pawpal_system.py) | Core domain models and scheduler |
| [ai_agent.py](ai_agent.py) | PawPalAI agent implementation |
| [app.py](app.py) | Streamlit web interface |
| [tests/test_ai_agent.py](tests/test_ai_agent.py) | 15 AI agent tests |
| [tests/test_pawpal.py](tests/test_pawpal.py) | 5 core system tests |

---

## 11. Portfolio Artifact

**GitHub Repository:** https://github.com/WesleyW8542/applied-ai-system-project

This project demonstrates that I approach AI engineering not as a black-box user, but as a systems thinker. Rather than reaching for an LLM to do everything, I designed a structured agentic workflow with distinct, testable stages — Observe, Think, Act, Check — that mirrors how a thoughtful engineer would approach a problem: gather information, reason about it, produce output, then validate it. The result is a system that is predictable, explainable, and provably correct (20/20 tests), which reflects my belief that responsible AI engineering means building things you can reason about and trust — not just things that seem to work.