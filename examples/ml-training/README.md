# Example: ML Model Training Optimization

ShareClaw used to optimize model training — like autoresearch but with shared state across agents.

```python
from shareclaw import Brain

brain = Brain("llm-training",
    objective="Minimize validation loss",
    metric="val_loss",
    variables=["learning_rate", "batch_size", "architecture", "regularization"],
    wait_time="5 minutes",
    step_size=0.9,  # lower is better for loss, so target = current * 0.9
)

brain.set_target("val_loss ≤ 2.5 (current: 3.1)")
brain.auto_advance("learning_rate", "3e-4", before=3.1, after=2.8)  # auto decides: advance ✅
brain.auto_advance("batch_size", "64", before=2.8, after=2.9)      # auto decides: discard ❌
brain.report()
```
