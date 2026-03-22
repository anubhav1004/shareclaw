# Example: Multi-Agent Content Pipeline

ShareClaw used for a content creation pipeline where:
- Agent A generates drafts
- Agent B reviews and improves quality
- Both share state on what content performs best

## The Loop
1. Agent A generates 5 content pieces
2. Agent B scores them (1-10) and explains why
3. Best-scoring patterns get logged in shared_brain.md
4. Next cycle, Agent A uses learnings to generate better content
5. Quality score improves each cycle
