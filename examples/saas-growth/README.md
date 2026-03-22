# Example: SaaS Growth Optimization

ShareClaw used to optimize user activation for a SaaS product.

```python
from shareclaw import Brain

brain = Brain("saas-activation",
    objective="Maximize trial-to-paid conversion rate",
    metric="conversion_%",
    variables=["onboarding_flow", "email_sequence", "pricing_page", "free_trial_length"],
    wait_time="1 week",
    step_size=1.2,
)

brain.set_target("conversion_% ≥ 8% (current: 5.2%)")
brain.auto_advance("onboarding_flow", "3-step-wizard", before=5.2, after=7.1)
brain.learn("3-step wizard converts better than video tour", evidence="7.1% vs 5.2%")
brain.fail("10-step onboarding", reason="Users drop off at step 4, conversion 3.8%")
```
