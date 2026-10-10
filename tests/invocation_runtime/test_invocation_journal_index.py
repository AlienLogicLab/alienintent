"""BOUNDED-ROUTINE-LAUNCH: the invocation journal's per-work-item read. The journal stays canonical; the index is
disposable acceleration state: its crash, omission, corruption or absence never makes a valid journal record disappear
from a read. Identities and fields are TEST DATA."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from alienintent.invocation_runtime.adapters import invocation_journal
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal


def journal(tmp_path) -> JsonlInvocationJournal:
    return JsonlInvocationJournal(tmp_path / "invocation-journal.jsonl", lambda: 1.0)


def test_a_work_read_answers_that_items_records_in_order_and_sequences_follow_the_journal(tmp_path):
    log = journal(tmp_path)
    for number in range(6):
        log.append({"event": "invocation-started", "work_identity": "AB"[number % 2], "n": number})
    log.append({"event": "process-cancel", "invocation_id": "x"})  # names no work item: the full read only
    log.append({"event": "x", "work_identity": "A", "big": "y" * 20_000})  # longer than one tail read

    assert [r["sequence"] for r in log.records()] == list(range(8))
    assert [r["n"] for r in log.records(work="A")[:3]] == [0, 2, 4]
    assert [r["sequence"] for r in log.records(work="A")] == [0, 2, 4, 7]
    assert log.records(work="A")[-1]["big"] == "y" * 20_000
    assert [r["sequence"] for r in log.records(work="B")] == [1, 3, 5]
    assert log.records(work="C") == ()
    assert log.append({"event": "x", "work_identity": "B"})["sequence"] == 8


def test_a_line_whose_copy_was_lost_or_doubled_by_a_crash_is_read_exactly_once(tmp_path):
    """A crash after the journal line and before its copy: the next work read copies the lines past `covered`. A crash
    after copying and before `covered` moved: the doubled copy (the identical line) is read once."""
    log = journal(tmp_path)
    log.append({"event": "a", "work_identity": "A"})
    line = json.dumps({"event": "b", "work_identity": "A", "sequence": 1, "at": 1.0}, sort_keys=True) + "\n"
    with log.path.open("a") as sink:
        sink.write(line)  # the journal line, never copied
    work_file = next(index_of(log).glob("*.jsonl"))
    with work_file.open("a") as sink:
        sink.write(line)  # copied, but `covered` not moved
    assert [r["event"] for r in log.records(work="A")] == ["a", "b"]
    assert work_file.read_text().count(line) == 2  # the doubled copy is still there, read once


def test_two_records_with_the_same_sequence_are_both_read(tmp_path):
    """A journal written by two unlocked appenders may hold two different records with one sequence: both are real."""
    log = journal(tmp_path)
    log.path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in (
        {"event": "a", "work_identity": "A", "sequence": 0, "at": 1.0},
        {"event": "b", "work_identity": "A", "sequence": 0, "at": 1.0})))
    assert [r["event"] for r in log.records(work="A")] == ["a", "b"]


def test_concurrent_appends_from_two_processes_take_distinct_sequences(tmp_path):
    import multiprocessing
    path = tmp_path / "invocation-journal.jsonl"
    context = multiprocessing.get_context("fork")
    workers = [context.Process(target=_append_many, args=(path, name)) for name in ("A", "B")]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(60)
    records = JsonlInvocationJournal(path, lambda: 1.0).records()
    assert sorted(r["sequence"] for r in records) == list(range(40))
    assert len(JsonlInvocationJournal(path, lambda: 1.0).records(work="A")) == 20


def _append_many(path, name):
    log = JsonlInvocationJournal(path, lambda: 1.0)
    for _ in range(20):
        log.append({"event": "x", "work_identity": name})


def test_an_index_failure_after_the_line_is_durable_does_not_fail_the_append(tmp_path, monkeypatch):
    log = journal(tmp_path)

    def broken(path, rebuild=False):
        raise OSError("index disk full")
    monkeypatch.setattr(invocation_journal, "_sync_index", broken)
    assert log.append({"event": "a", "work_identity": "A"})["sequence"] == 0
    monkeypatch.undo()
    assert [r["event"] for r in log.records(work="A")] == ["a"]


def test_a_rebuild_interrupted_after_removing_copies_is_finished_by_the_next_read(tmp_path, monkeypatch):
    """`covered` goes first, so a crash part way through clearing never leaves a `covered` that vouches for removed
    copies."""
    log = journal(tmp_path)
    for name in ("A", "B"):
        log.append({"event": "a", "work_identity": name})
    unlink = Path.unlink
    removed = []

    def dies(self, *args, **kwargs):
        unlink(self, *args, **kwargs)
        removed.append(self.name)
        if self.suffix == ".jsonl":
            raise KeyboardInterrupt("the process died")
    monkeypatch.setattr(Path, "unlink", dies)
    with pytest.raises(KeyboardInterrupt):
        invocation_journal._clear(index_of(log))
    monkeypatch.undo()
    assert removed[0] == "covered"
    assert [r["work_identity"] for r in log.records(work="A") + log.records(work="B")] == ["A", "B"]


def test_a_work_read_reads_the_journal_only_past_what_is_covered(tmp_path, monkeypatch):
    """Whatever the history, a routine read reads that item's file and no journal byte already copied."""
    log = journal(tmp_path)
    for number in range(1000):
        log.append({"event": "invocation-started", "work_identity": f"history-{number}"})
    log.append({"event": "invocation-started", "work_identity": "NOW"})
    size = log.path.stat().st_size
    reads = []
    opened = invocation_journal.Path.open

    def watching(self, mode="r", *args, **kwargs):
        handle = opened(self, mode, *args, **kwargs)
        if self == log.path and "b" in mode:
            seek = handle.seek

            def recorded(offset, whence=0):
                position = seek(offset, whence)
                reads.append(position)
                return position
            handle.seek = recorded
        return handle
    read_text = invocation_journal.Path.read_text

    def whole(self, *args, **kwargs):
        assert self != log.path, "the whole journal was read"
        return read_text(self, *args, **kwargs)
    monkeypatch.setattr(invocation_journal.Path, "open", watching)
    monkeypatch.setattr(invocation_journal.Path, "read_text", whole)

    assert [r["work_identity"] for r in log.records(work="NOW")] == ["NOW"]
    log.append({"event": "invocation-outcome", "work_identity": "NOW"})
    assert len(log.records(work="NOW")) == 2
    assert reads and min(reads) >= size - 8192  # the end of the journal only: its last line, nothing before


def index_of(log: JsonlInvocationJournal):
    return log.path.with_name(log.path.name + ".by-work")


def lines(*records: dict) -> str:
    return "".join(json.dumps(record | {"sequence": number, "at": 1.0}, sort_keys=True) + "\n"
                   for number, record in enumerate(records))


def test_a_journal_written_before_the_index_existed_is_caught_up_from_its_start(tmp_path):
    log = journal(tmp_path)
    log.path.write_text(lines({"event": "a", "work_identity": "A"}, {"event": "b", "work_identity": "B"},
                              {"event": "c", "work_identity": "A"}))
    assert not index_of(log).exists()
    assert [r["event"] for r in log.records(work="A")] == ["a", "c"]
    assert log.append({"event": "d", "work_identity": "A"})["sequence"] == 3
    assert [r["event"] for r in log.records(work="A")] == ["a", "c", "d"]


def test_a_crash_after_the_journal_line_and_before_the_index_loses_nothing(tmp_path, monkeypatch):
    log = journal(tmp_path)
    log.append({"event": "a", "work_identity": "A"})
    sync = invocation_journal._sync_index

    def crash(path, rebuild=False):
        if '"event": "b"' in path.read_text():  # only once the journal line is durable
            raise KeyboardInterrupt("the process died")
        return sync(path, rebuild)
    monkeypatch.setattr(invocation_journal, "_sync_index", crash)
    with pytest.raises(KeyboardInterrupt):
        log.append({"event": "b", "work_identity": "A"})
    monkeypatch.setattr(invocation_journal, "_sync_index", sync)
    assert [r["event"] for r in journal(tmp_path).records(work="A")] == ["a", "b"]  # a fresh process


@pytest.mark.parametrize("then_append", [False, True], ids=["read next", "append then read"])
@pytest.mark.parametrize("damage", ["covered past the end", "covered unreadable", "index removed",
                                    "work file unreadable", "rewritten at the same size", "rewritten shorter",
                                    "rewritten longer", "replaced"])
def test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start(tmp_path, damage, then_append):
    """Each damage to the index, or a journal changed other than by an append, is detected on the next read, which
    rebuilds the index from position 0 and answers exactly the journal's records."""
    log = journal(tmp_path)
    for event in ("a", "b", "c"):
        log.append({"event": event, "work_identity": "A", "role": "PRODUCER"})
    assert len(log.records(work="A")) == 3
    index, text = index_of(log), log.path.read_text()
    if damage == "covered past the end":
        state = json.loads((index / "covered").read_text())
        (index / "covered").write_text(json.dumps(state | {"offset": state["offset"] + 10}))
    elif damage == "covered unreadable":
        (index / "covered").write_text("not json")
    elif damage == "work file unreadable":
        next(index.glob("*.jsonl")).write_text("not json\n")
    elif damage == "index removed":
        for path in index.iterdir():
            path.unlink()
        index.rmdir()
    elif damage == "rewritten at the same size":
        log.path.write_text(text.replace('"role": "PRODUCER"', '"role": "VERIFIER"', 1))
    elif damage == "rewritten shorter":
        log.path.write_text(text.replace('"role": "PRODUCER"', '"role": "P"', 1))
    elif damage == "rewritten longer":
        log.path.write_text(text.replace('"role": "PRODUCER"', '"role": "PRODUCER-AND-MORE"', 1))
    else:
        replacement = log.path.with_name("replacement.jsonl")
        replacement.write_text(text.replace('"role": "PRODUCER"', '"role": "VERIFIER"', 1))
        replacement.replace(log.path)
    if then_append:  # an append before the next read must notice the change too
        log.append({"event": "d", "work_identity": "A", "role": "PRODUCER"})
    expected = [record for record in log.records() if record.get("work_identity") == "A"]
    assert list(log.records(work="A")) == expected


def test_the_append_lock_lives_outside_the_disposable_index(tmp_path):
    """Removing the index never removes the lock that keeps sequences distinct."""
    log = journal(tmp_path)
    log.append({"event": "a", "work_identity": "A"})
    assert log.path.with_name(log.path.name + ".lock").exists()
    assert not (index_of(log) / "lock").exists()
