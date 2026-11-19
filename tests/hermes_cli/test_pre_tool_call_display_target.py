"""``pre_tool_call`` approve directive carries ``display_target``.

The approval card's command slot used to be filled with the synthetic
``<tool> (plugin approval rule)`` label, so a hook that knew the exact command
could only put it in the reason field, which is capped and truncates long
kubectl/helm lines.
"""

from __future__ import annotations

import hermes_cli.lifecycle as lifecycle
import hermes_cli.plugins as plugins

CMD = "kubectl apply -f k8s/deploy.yaml"


def _directive(monkeypatch, result):
    monkeypatch.setattr(lifecycle, "invoke_hook", lambda *a, **k: [result])
    return plugins._get_pre_tool_call_directive_details("terminal", {"command": CMD})


def test_display_target_is_carried_and_stripped(monkeypatch):
    directive = _directive(
        monkeypatch, {"action": "approve", "message": "why", "rule_key": "kubectl",
                      "display_target": f"  {CMD}\n"},
    )
    assert directive.action == "approve"
    assert directive.display_target == CMD
    assert directive.rule_key == "kubectl"


def test_absent_display_target_stays_none(monkeypatch):
    directive = _directive(monkeypatch, {"action": "approve", "message": "why"})
    assert directive.display_target is None


def test_non_string_or_blank_display_target_is_ignored(monkeypatch):
    for value in (42, "   ", None):
        directive = _directive(monkeypatch, {"action": "approve", "message": "why", "display_target": value})
        assert directive.display_target is None, value


def test_block_directive_never_carries_a_display_target(monkeypatch):
    """A veto needs no card, and its message is the tool result: no display field."""
    directive = _directive(
        monkeypatch, {"action": "block", "message": "no", "display_target": "kubectl delete ns prod"},
    )
    assert directive.action == "block"
    assert directive.display_target is None
