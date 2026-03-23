"""CLI smoke tests for ShareClaw."""

import sys

from shareclaw.cli import main


def run_cli(args, monkeypatch, capsys, cwd):
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "argv", ["shareclaw", *args])
    main()
    return capsys.readouterr().out


def test_init_and_files_commands(tmp_path, monkeypatch, capsys):
    output = run_cli(
        ["init", "demo", "--objective", "Grow signups", "--metric", "signups"],
        monkeypatch,
        capsys,
        tmp_path,
    )
    assert "ShareClaw initialized: demo" in output
    assert "shared_brain_md" in output

    files_output = run_cli(["files"], monkeypatch, capsys, tmp_path)
    assert "task_queue_md" in files_output
    assert "decisions_md" in files_output


def test_task_and_consensus_flows(tmp_path, monkeypatch, capsys):
    run_cli(["init", "demo"], monkeypatch, capsys, tmp_path)

    task_output = run_cli(
        ["task", "add", "Ship demo", "--priority", "HIGH", "--by", "lead"],
        monkeypatch,
        capsys,
        tmp_path,
    )
    assert "Task created: Ship demo" in task_output

    pickup_output = run_cli(["task", "pickup", "builder"], monkeypatch, capsys, tmp_path)
    assert "Ship demo" in pickup_output
    assert '"status": "in_progress"' in pickup_output

    start_output = run_cli(
        ["consensus", "start", "Switch hooks?", "--option", "YES", "--option", "NO", "--by", "lead"],
        monkeypatch,
        capsys,
        tmp_path,
    )
    assert "Consensus started" in start_output

    list_output = run_cli(["consensus", "list"], monkeypatch, capsys, tmp_path)
    assert "Switch hooks?" in list_output
