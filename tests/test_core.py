"""Comprehensive tests for ShareClaw Brain class."""

import json
import pytest
from shareclaw.core import Brain


# ── 1. Initialization ────────────────────────────────────────────────

class TestBrainInit:
    def test_creates_directories_and_files(self, tmp_path):
        brain = Brain("test-project", path=str(tmp_path / ".shareclaw"))
        assert brain.path.exists()
        assert brain.skills_dir.exists()
        assert brain.handoffs_dir.exists()

    def test_default_state(self, tmp_path):
        brain = Brain("test-project", path=str(tmp_path / ".shareclaw"))
        assert brain.state["project"] == "test-project"
        assert brain.state["cycle"] == 0
        assert brain.state["current_target"] is None
        assert brain.state["works"] == []
        assert brain.state["fails"] == []
        assert brain.state["history"] == []
        assert brain.state["cycles"] == []
        assert brain.state["skills"] == []
        assert brain.state["milestones"] == []
        assert brain.state["agents"] == {}
        assert "created_at" in brain.state


# ── 2. set_target ────────────────────────────────────────────────────

class TestSetTarget:
    def test_sets_target_and_increments_cycle(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("Get 1000 views")
        assert brain.state["cycle"] == 1
        assert brain.state["current_target"]["target"] == "Get 1000 views"
        assert brain.state["current_target"]["status"] == "active"
        assert brain.state["current_target"]["cycle"] == 1

    def test_set_target_with_deadline(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("Ship v1", deadline="2026-04-01")
        assert brain.state["current_target"]["deadline"] == "2026-04-01"

    def test_successive_targets_increment_cycle(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("Target A")
        brain.set_target("Target B")
        assert brain.state["cycle"] == 2
        assert brain.state["current_target"]["target"] == "Target B"


# ── 3. hit_target / miss_target ──────────────────────────────────────

class TestHitMissTarget:
    def test_hit_target(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("Get 1000 views")
        brain.hit_target()
        assert brain.state["current_target"]["status"] == "hit"
        assert "hit_at" in brain.state["current_target"]
        assert len(brain.state["milestones"]) == 1
        assert brain.state["milestones"][0]["target"] == "Get 1000 views"

    def test_miss_target(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("Get 1000 views")
        brain.miss_target("Only got 200")
        assert brain.state["current_target"]["status"] == "missed"
        assert brain.state["current_target"]["reason"] == "Only got 200"

    def test_hit_target_no_target_set(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.hit_target()  # should not crash
        assert brain.state["current_target"] is None

    def test_miss_target_no_target_set(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.miss_target("reason")  # should not crash
        assert brain.state["current_target"] is None


# ── 4. learn ─────────────────────────────────────────────────────────

class TestLearn:
    def test_appends_to_works(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.learn("Ragebait hooks work", evidence="2x more views")
        assert len(brain.state["works"]) == 1
        entry = brain.state["works"][0]
        assert entry["what"] == "Ragebait hooks work"
        assert entry["evidence"] == "2x more views"
        assert entry["cycle"] == 1
        assert "learned_at" in entry

    def test_multiple_learnings(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.learn("A", evidence="e1")
        brain.learn("B", evidence="e2")
        assert len(brain.state["works"]) == 2


# ── 5. fail ──────────────────────────────────────────────────────────

class TestFail:
    def test_appends_to_fails(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.fail("Long text", reason="no engagement")
        assert len(brain.state["fails"]) == 1
        entry = brain.state["fails"][0]
        assert entry["what"] == "Long text"
        assert entry["reason"] == "no engagement"
        assert entry["cycle"] == 1

    def test_fails_never_deleted(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.fail("A", reason="r1")
        brain.fail("B", reason="r2")
        brain.fail("C", reason="r3")
        assert len(brain.state["fails"]) == 3
        # Reload and verify persistence
        brain2 = Brain("tp", path=str(tmp_path / ".sc"))
        assert len(brain2.state["fails"]) == 3


# ── 6. log_cycle ─────────────────────────────────────────────────────

class TestLogCycle:
    def test_advance_and_discard(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.log_cycle("hook_style", "ragebait", 200, 450, "advance")
        brain.log_cycle("cta_type", "soft", 450, 300, "discard")
        assert len(brain.state["cycles"]) == 2
        assert brain.state["cycles"][0]["status"] == "advance"
        assert brain.state["cycles"][1]["status"] == "discard"

    def test_delta_calculation(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.log_cycle("x", "v", 200, 450, "advance")
        c = brain.state["cycles"][0]
        assert c["delta"] == 250.0
        assert c["delta_pct"] == 125.0

    def test_writes_tsv(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.log_cycle("x", "v", 100, 200, "advance", description="test desc")
        assert brain.log_file.exists()
        lines = brain.log_file.read_text().strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        assert lines[0].startswith("cycle\t")
        assert "test desc" in lines[1]

    def test_history_appended(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.log_cycle("x", "v", 100, 200, "advance")
        assert len(brain.state["history"]) == 1
        assert brain.state["history"][0]["metric"] == 200


# ── 7. introspect ────────────────────────────────────────────────────

class TestIntrospect:
    def test_saves_five_questions(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.log_cycle("x", "v", 100, 200, "advance")
        brain.introspect(
            expected="300 views",
            actual="200 views",
            why="Hook was weak",
            next_action="Try emotional hook",
            next_target="Get 400 views",
        )
        intro = brain.state["cycles"][-1]["introspection"]
        assert intro["expected"] == "300 views"
        assert intro["actual"] == "200 views"
        assert intro["why"] == "Hook was weak"
        assert intro["next_action"] == "Try emotional hook"
        assert intro["next_target"] == "Get 400 views"

    def test_introspect_no_cycles(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        # Should not crash even with no cycles
        brain.introspect("a", "b", "c", "d", "e")
        assert len(brain.state["cycles"]) == 0


# ── 8. Skills ────────────────────────────────────────────────────────

class TestSkills:
    def test_add_and_get_skill(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.add_skill("ragebait", description="Ragebait hooks", formula="F1",
                        examples_good=["ex1"], examples_bad=["bad1"],
                        code="print('hi')", created_by="agent-a")
        skill = brain.get_skill("ragebait")
        assert skill["name"] == "ragebait"
        assert skill["description"] == "Ragebait hooks"
        assert skill["formula"] == "F1"
        assert skill["examples_good"] == ["ex1"]
        assert skill["examples_bad"] == ["bad1"]
        assert skill["code"] == "print('hi')"
        assert skill["created_by"] == "agent-a"
        assert skill["uses"] == 1

    def test_get_skill_increments_uses(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.add_skill("s1", description="d1")
        brain.get_skill("s1")
        brain.get_skill("s1")
        skill = brain.get_skill("s1")
        assert skill["uses"] == 3

    def test_get_nonexistent_skill(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        assert brain.get_skill("nope") == {}

    def test_list_skills(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.add_skill("s1", description="d1")
        brain.add_skill("s2", description="d2")
        skills = brain.list_skills()
        names = {s["name"] for s in skills}
        assert names == {"s1", "s2"}

    def test_list_skills_empty(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        assert brain.list_skills() == []

    def test_skill_added_to_state(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.add_skill("s1", description="d1")
        assert "s1" in brain.state["skills"]


# ── 9. Handoffs ──────────────────────────────────────────────────────

class TestHandoffs:
    def test_handoff_create_and_pickup(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        hid = brain.handoff("agent-b", task="Post videos", context="ctx",
                            files=["v1.mp4"], from_agent="agent-a")
        assert hid.startswith("handoff_")

        h = brain.pickup_handoff("agent-b")
        assert h["task"] == "Post videos"
        assert h["status"] == "picked_up"
        assert h["from"] == "agent-a"
        assert h["files"] == ["v1.mp4"]

    def test_pickup_no_handoffs(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        assert brain.pickup_handoff("agent-x") == {}

    def test_pickup_only_for_correct_agent(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.handoff("agent-b", task="Task 1")
        assert brain.pickup_handoff("agent-c") == {}

    def test_complete_handoff(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        hid = brain.handoff("agent-b", task="Post videos")
        brain.pickup_handoff("agent-b")
        brain.complete_handoff(hid, result="Done, posted 3 videos")

        hf = brain.handoffs_dir / f"{hid}.json"
        with open(hf) as f:
            h = json.load(f)
        assert h["status"] == "completed"
        assert h["result"] == "Done, posted 3 videos"
        assert "completed_at" in h

    def test_complete_nonexistent_handoff(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.complete_handoff("handoff_999999", result="x")  # should not crash

    def test_picked_up_handoff_not_picked_again(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.handoff("agent-b", task="T1")
        brain.pickup_handoff("agent-b")
        # Second pickup should return empty since it's already picked up
        assert brain.pickup_handoff("agent-b") == {}


# ── 10. Events ───────────────────────────────────────────────────────

class TestEvents:
    def test_emit_and_get(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.emit("video_generated", data={"file": "v1.mp4"}, agent="gen")
        events = brain.get_events()
        assert len(events) == 1
        assert events[0]["type"] == "video_generated"
        assert events[0]["data"]["file"] == "v1.mp4"
        assert events[0]["agent"] == "gen"

    def test_get_events_filtered(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.emit("type_a", data={"x": 1})
        brain.emit("type_b", data={"x": 2})
        brain.emit("type_a", data={"x": 3})
        assert len(brain.get_events(event_type="type_a")) == 2
        assert len(brain.get_events(event_type="type_b")) == 1

    def test_get_events_limit(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        for i in range(20):
            brain.emit("tick", data={"i": i})
        assert len(brain.get_events(limit=5)) == 5

    def test_get_events_empty(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        assert brain.get_events() == []

    def test_events_capped_at_100(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        for i in range(120):
            brain.emit("tick", data={"i": i})
        with open(brain.events_file) as f:
            all_events = json.load(f)
        assert len(all_events) == 100


# ── 11. report ───────────────────────────────────────────────────────

class TestReport:
    def test_report_returns_string(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        result = brain.report()
        assert isinstance(result, str)
        assert "tp" in result

    def test_report_with_data(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.learn("L1", evidence="e1")
        brain.fail("F1", reason="r1")
        brain.log_cycle("x", "v", 100, 200, "advance")
        brain.add_skill("s1", description="d1")
        brain.hit_target()
        result = brain.report()
        assert "T1" in result
        assert "L1" in result
        assert "F1" in result
        assert "s1" in result

    def test_report_empty_brain(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        result = brain.report()
        assert isinstance(result, str)
        assert len(result) > 0


# ── 12. context ──────────────────────────────────────────────────────

class TestContext:
    def test_returns_llm_string(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        ctx = brain.context()
        assert isinstance(ctx, str)
        assert "ShareClaw Context" in ctx
        assert "tp" in ctx

    def test_context_includes_all_sections(self, tmp_path):
        brain = Brain("tp", path=str(tmp_path / ".sc"))
        brain.set_target("T1")
        brain.learn("L1", evidence="e1")
        brain.fail("F1", reason="r1")
        brain.log_cycle("x", "v", 100, 200, "advance")
        brain.add_skill("s1", description="d1")
        ctx = brain.context()
        assert "Current Target" in ctx
        assert "What Works" in ctx
        assert "What Doesn't Work" in ctx
        assert "Last 3 Cycles" in ctx
        assert "Available Skills" in ctx


# ── 13. State persists across reloads ────────────────────────────────

class TestPersistence:
    def test_state_persists_across_reloads(self, tmp_path):
        sc_path = str(tmp_path / ".sc")
        brain1 = Brain("tp", path=sc_path)
        brain1.set_target("T1")
        brain1.learn("L1", evidence="e1")
        brain1.fail("F1", reason="r1")
        brain1.log_cycle("x", "v", 100, 200, "advance")
        brain1.add_skill("s1", description="d1")
        brain1.emit("ev1", data={"k": "v"})
        brain1.hit_target()

        # Reload from same path
        brain2 = Brain("tp", path=sc_path)
        assert brain2.state["cycle"] == 1
        assert brain2.state["current_target"]["status"] == "hit"
        assert len(brain2.state["works"]) == 1
        assert len(brain2.state["fails"]) == 1
        assert len(brain2.state["cycles"]) == 1
        assert len(brain2.state["milestones"]) == 1
        assert "s1" in brain2.state["skills"]
        assert len(brain2.get_events()) == 1

    def test_multiple_cycles_persist(self, tmp_path):
        sc_path = str(tmp_path / ".sc")
        brain = Brain("tp", path=sc_path)
        for i in range(5):
            brain.set_target(f"Target {i}")
            brain.log_cycle("var", f"v{i}", i * 10, (i + 1) * 10, "advance")
            brain.learn(f"L{i}", evidence=f"e{i}")

        brain2 = Brain("tp", path=sc_path)
        assert brain2.state["cycle"] == 5
        assert len(brain2.state["cycles"]) == 5
        assert len(brain2.state["works"]) == 5


# ── 14. Concurrent usage ────────────────────────────────────────────

class TestConcurrent:
    def test_two_instances_same_path(self, tmp_path):
        sc_path = str(tmp_path / ".sc")
        a = Brain("tp", path=sc_path)
        b = Brain("tp", path=sc_path)

        a.set_target("T1")
        # b won't see a's changes until reload
        assert b.state["cycle"] == 0

        # But b can reload by creating a new instance
        b = Brain("tp", path=sc_path)
        assert b.state["cycle"] == 1
        assert b.state["current_target"]["target"] == "T1"

    def test_both_write_skills(self, tmp_path):
        sc_path = str(tmp_path / ".sc")
        a = Brain("tp", path=sc_path)
        b = Brain("tp", path=sc_path)

        a.add_skill("skill-a", description="from a")
        b.add_skill("skill-b", description="from b")

        # Both skill files should exist on disk
        c = Brain("tp", path=sc_path)
        skills = c.list_skills()
        names = {s["name"] for s in skills}
        assert "skill-a" in names
        assert "skill-b" in names

    def test_both_emit_events(self, tmp_path):
        sc_path = str(tmp_path / ".sc")
        a = Brain("tp", path=sc_path)
        b = Brain("tp", path=sc_path)

        a.emit("from_a")
        b.emit("from_b")

        c = Brain("tp", path=sc_path)
        events = c.get_events(limit=10)
        types = {e["type"] for e in events}
        # Note: b.emit reads the file fresh, so both should be present
        assert "from_a" in types
        assert "from_b" in types
