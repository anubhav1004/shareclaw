# Integrations

ShareClaw works with any AI agent framework. Here's how to plug it in.

---

## CrewAI

Use `Brain` in CrewAI's task callbacks to read shared context before each task and write learnings after.

```python
from crewai import Agent, Task, Crew
from shareclaw import Brain

brain = Brain("my-crew-project")

def before_task(task):
    """Inject shared brain context into the task."""
    task.description = brain.context() + "\n\n" + task.description

def after_task(task, output):
    """Log results back to the shared brain."""
    brain.emit("task_completed", {
        "task": task.description[:100],
        "result": str(output)[:500],
    }, agent=task.agent.role)

researcher = Agent(
    role="Researcher",
    goal="Find what content performs best",
    backstory=brain.context(),  # shared brain as backstory
)

writer = Agent(
    role="Writer",
    goal="Create content using what we've learned",
    backstory=brain.context(),
)

research_task = Task(
    description="Analyze top-performing content this week",
    agent=researcher,
    callback=after_task,
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task],
    before_task=before_task,
)

crew.kickoff()
```

After the crew runs, log what worked:

```python
brain.learn("Short-form video outperforms carousels", evidence="crew research: 3x engagement")
brain.log_cycle(variable="format", variant="short-video", before=200, after=600, status="advance")
```

---

## AutoGen

Use `Brain` in the agent's system message so every conversation starts with shared context. Add brain methods as callable tools.

```python
from autogen import ConversableAgent
from shareclaw import Brain

brain = Brain("autogen-project")

# System message includes shared brain context
system_message = f"""You are a content optimization agent.

SHARED BRAIN (read this first, it's what the team has learned so far):
{brain.context()}

After completing any task, report what you learned by calling the learn() or fail() tools.
"""

# Register brain methods as tools
def learn_tool(what: str, evidence: str) -> str:
    brain.learn(what, evidence)
    return f"Learned: {what}"

def fail_tool(what: str, reason: str) -> str:
    brain.fail(what, reason)
    return f"Recorded failure: {what}"

def get_context_tool() -> str:
    return brain.context()

agent = ConversableAgent(
    name="optimizer",
    system_message=system_message,
    llm_config={"model": "gpt-4o"},
)

# Register tools
agent.register_for_llm(name="learn", description="Record a learning")(learn_tool)
agent.register_for_llm(name="fail", description="Record a failure")(fail_tool)
agent.register_for_llm(name="get_context", description="Read the shared brain")(get_context_tool)
```

For multi-agent AutoGen setups, both agents share the same `Brain` instance:

```python
brain = Brain("shared-project")

agent_a = ConversableAgent(name="creator", system_message=f"...\n{brain.context()}")
agent_b = ConversableAgent(name="analyst", system_message=f"...\n{brain.context()}")

# Both read and write to the same brain
# Agent A creates content, Agent B analyzes it
# Learnings from B are available to A on next cycle
```

---

## LangGraph

Use `Brain` as part of the graph state. Nodes read from it at the start and write to it at the end.

```python
from langgraph.graph import StateGraph, END
from shareclaw import Brain
from typing import TypedDict

brain = Brain("langgraph-project")

class AgentState(TypedDict):
    brain_context: str
    task: str
    result: str
    metric: float

def read_brain(state: AgentState) -> AgentState:
    """First node: read shared brain context."""
    state["brain_context"] = brain.context()
    return state

def execute_task(state: AgentState) -> AgentState:
    """Middle node: do the work, informed by brain context."""
    # Your LLM call here, with state["brain_context"] in the prompt
    state["result"] = "executed task with brain context"
    state["metric"] = 450.0
    return state

def write_brain(state: AgentState) -> AgentState:
    """Final node: write learnings back to shared brain."""
    if state["metric"] > 400:
        brain.learn(f"Task succeeded with metric {state['metric']}", evidence=state["result"])
    else:
        brain.fail(f"Task underperformed", reason=f"metric was {state['metric']}")
    return state

def should_continue(state: AgentState) -> str:
    """Route: continue optimizing or stop."""
    if state["metric"] >= 1000:
        return "done"
    return "continue"

# Build the graph
graph = StateGraph(AgentState)
graph.add_node("read_brain", read_brain)
graph.add_node("execute", execute_task)
graph.add_node("write_brain", write_brain)

graph.set_entry_point("read_brain")
graph.add_edge("read_brain", "execute")
graph.add_edge("execute", "write_brain")
graph.add_conditional_edges("write_brain", should_continue, {
    "continue": "read_brain",  # loop back
    "done": END,
})

app = graph.compile()
app.invoke({"task": "optimize content", "brain_context": "", "result": "", "metric": 0})
```

---

## OpenClaw

Add ShareClaw to each agent's identity theme in your `openclaw.json`. Both agents read and write to the same `shared_brain.md` file on disk.

```json
{
  "agents": {
    "list": [
      {
        "id": "heisenberg",
        "identity": {
          "theme": "You are a content creator. CRITICAL: Read /home/node/.openclaw/workspace/shared_brain.md BEFORE every task. Write results AFTER every task. Follow the introspection protocol. Log what works, what fails, and set numeric targets."
        }
      },
      {
        "id": "rutherford",
        "identity": {
          "theme": "You are an analytics agent. CRITICAL: Read /home/node/.openclaw/workspace/shared_brain.md BEFORE every task. Write your analysis AFTER every measurement. Update what works and what doesn't. Set the next cycle's target."
        }
      }
    ]
  }
}
```

Or use the Python API inside an OpenClaw tool:

```python
from shareclaw import Brain

brain = Brain("openclaw-project", path="/home/node/.openclaw/workspace/.shareclaw")

# In your tool's execute function
context = brain.context()  # read before acting
# ... do work ...
brain.learn("Ragebait hooks get 2x views", evidence="cycle 3 data")  # write after acting
```

---

## Claude Code

Use ShareClaw through Claude Code's project memory system. Put `shared_brain.md` where Claude Code can read it.

**Option 1: Project memory (recommended)**

```bash
# Copy the shared brain template into Claude Code's memory
cp templates/shared_brain.md .claude/projects/your-project/memory/shared_brain.md
```

Claude Code automatically reads files in the memory directory. Your shared brain becomes part of every conversation.

**Option 2: Repo root**

Just keep `shared_brain.md` in your repo root. Claude Code reads files in the working directory.

**Option 3: Python API in Claude Code sessions**

Tell Claude Code to use the Python API:

```
Use ShareClaw to track our progress:

from shareclaw import Brain
brain = Brain("my-project")

Before each task, read: brain.context()
After each task, log: brain.learn() or brain.fail()
After experiments: brain.log_cycle()
```

Claude Code will call these methods during the session, and the state persists in `.shareclaw/brain.json`.

---

## GPT Agents (OpenAI Assistants / Custom GPTs)

Use `brain.context()` to inject shared knowledge into the system prompt.

```python
from openai import OpenAI
from shareclaw import Brain

client = OpenAI()
brain = Brain("gpt-project")

# Build system prompt with shared brain context
system_prompt = f"""You are a content optimization assistant.

Here is what the team has learned so far:

{brain.context()}

When you complete a task, tell me what worked and what didn't so I can update the shared brain.
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Create 3 video hooks for our education app"},
    ],
)

# After getting results, update the brain
brain.learn("Question-based hooks get more clicks", evidence="GPT analysis of top 50 competitors")
```

For OpenAI Assistants with function calling, register brain methods as tools:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "learn",
            "description": "Record something that works, with evidence",
            "parameters": {
                "type": "object",
                "properties": {
                    "what": {"type": "string", "description": "What works"},
                    "evidence": {"type": "string", "description": "Why we know it works"},
                },
                "required": ["what", "evidence"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fail",
            "description": "Record something that does not work",
            "parameters": {
                "type": "object",
                "properties": {
                    "what": {"type": "string", "description": "What failed"},
                    "reason": {"type": "string", "description": "Why it failed"},
                },
                "required": ["what", "reason"],
            },
        },
    },
]
```

---

## Any LLM (raw markdown approach)

ShareClaw is just files. If your agent can read and write files, it can use ShareClaw. No Python package needed.

```python
# Read the shared brain before acting
with open("shared_brain.md") as f:
    context = f.read()

# Include it in your LLM prompt
prompt = f"""
SHARED BRAIN (team knowledge -- read this first):
{context}

Now do your task: ...
"""

# Call any LLM
response = call_llm(prompt)

# Write results back
with open("shared_brain.md", "a") as f:
    f.write(f"\n### Cycle {n} Result\n")
    f.write(f"Variable: {variable}\n")
    f.write(f"Result: {result}\n")
    f.write(f"Status: {'advance' if improved else 'discard'}\n")

# Log to TSV
with open("execution_log.tsv", "a") as f:
    f.write(f"{cycle}\t{timestamp}\t{variable}\t{variant}\t{before}\t{after}\t{status}\n")
```

This works with:
- Anthropic Claude (API or Claude Code)
- OpenAI GPT-4o
- Google Gemini
- Llama / Mistral / any open-source model
- Any agent framework that supports file I/O

The pattern is always the same: **read before acting, write after acting, never delete failures**.
