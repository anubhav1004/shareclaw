# Example: Code Review Quality

Two agents: one writes code, one reviews. Both share learnings about what passes review.

```python
from shareclaw import Brain

brain = Brain("code-quality",
    objective="Maximize PR approval rate on first review",
    metric="first_pass_approval_%",
    variables=["test_coverage", "naming_conventions", "doc_style", "error_handling"],
    wait_time="1 day",
    step_size=1.1,
)

# Agent A writes code
brain.add_skill("error-handling-patterns",
    description="Patterns that always pass code review",
    examples_good=["try/except with specific exceptions", "custom error classes"],
    examples_bad=["bare except:", "silencing errors"],
    created_by="reviewer-agent")

# Agent B reads the skill before writing code
skill = brain.get_skill("error-handling-patterns")
# Uses the patterns → PR passes on first review
brain.auto_advance("error_handling", "specific_exceptions", before=60, after=78)
```
