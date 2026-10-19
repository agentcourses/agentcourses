"""Offline authority model, never a host adapter or a provenance verifier."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import date
import json
from pathlib import Path
import re
import sys

HOSTS = {"claude-code", "codex", "embedded", "unsupported"}
BINDING = ("snapshot", "lesson", "call", "occurrence", "challenge")
FAILURES = {*BINDING, "replay"}
FIELDS = {"case", "host", "origin", "mechanism", "authority", "context", "confirmation", "used_occurrences", "expected_outcome", "expected_binding_failures", "expected_candidate_eligible"}
RESULT_FIELDS = {"case", "host", "outcome", "binding_failures", "evidence_class", "candidate_eligible"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def label(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value) is not None


def binding(value: object) -> bool:
    return isinstance(value, Mapping) and set(value) == set(BINDING) and all(label(v) for v in value.values())


def validate_case(case: Mapping[str, object]) -> None:
    require(isinstance(case, Mapping) and FIELDS <= set(case) <= FIELDS | {"answer"}, "invalid fixture fields")
    require(label(case["case"]) and case["host"] in HOSTS, "invalid case or host")
    require(case["origin"] in {"learner", "tutor", "automated", "missing"}, "invalid origin")
    require(case["mechanism"] in {"public-envelope", "isolated-confirmation"}, "invalid mechanism")
    authority = case["authority"]
    require(isinstance(authority, Mapping) and set(authority) == {"controller", "tutor_access"}, "invalid authority fields")
    require(authority["controller"] in {"learner", "tutor", "unknown"}, "invalid controller")
    require(isinstance(authority["tutor_access"], list) and all(a in {"filesystem", "tools", "configuration", "signer"} for a in authority["tutor_access"]), "invalid tutor access")
    require(binding(case["context"]) and (case["confirmation"] is None or binding(case["confirmation"])), "invalid binding fields")
    require(isinstance(case["used_occurrences"], list) and all(label(v) for v in case["used_occurrences"]), "invalid occurrence ledger")
    require(case["expected_outcome"] in {"verified", "unverified", "rejected"}, "invalid expected outcome")
    require(isinstance(case["expected_binding_failures"], list) and all(f in FAILURES for f in case["expected_binding_failures"]), "invalid expected failures")
    require(type(case["expected_candidate_eligible"]) is bool, "invalid expected eligibility")
    require("answer" not in case or isinstance(case["answer"], str), "invalid ephemeral answer")


def evaluate_case(case: Mapping[str, object]) -> Mapping[str, object]:
    validate_case(case)
    context, confirmation = case["context"], case["confirmation"]
    failures = []
    if confirmation is not None:
        failures = [key for key in BINDING if context[key] != confirmation[key]]
        if confirmation["occurrence"] in case["used_occurrences"]:
            failures.append("replay")
    eligible = (confirmation is not None and not failures and case["origin"] == "learner"
                and case["mechanism"] == "isolated-confirmation" and case["host"] != "unsupported"
                and case["authority"]["controller"] == "learner"
                and not case["authority"]["tutor_access"])
    # A synthetic success cannot authorise a real receipt while the contract is pending.
    outcome = "rejected" if failures or case["origin"] in {"tutor", "automated"} else "unverified"
    return dict(case=case["case"], host=case["host"], outcome=outcome,
                binding_failures=failures, evidence_class="simulated", candidate_eligible=eligible)


def load_cases(path: Path) -> list[Mapping[str, object]]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    cases = []
    for file in files:
        data = json.loads(file.read_text())
        require(isinstance(data, list), "cases must be an array")
        cases.extend(data)
    require(bool(cases), "empty cases")
    for case in cases:
        validate_case(case)
    require(len({case["case"] for case in cases}) == len(cases), "duplicate case")
    return cases


def run_cases(path: Path) -> list[Mapping[str, object]]:
    results = []
    for case in load_cases(path):
        result = evaluate_case(case)
        require(result["outcome"] == case["expected_outcome"]
                and result["binding_failures"] == case["expected_binding_failures"]
                and result["candidate_eligible"] == case["expected_candidate_eligible"], "case assertion failed")
        results.append(result)
    return results


SECTIONS = ("Host evidence", "Threat boundary", "Adversarial results", "Privacy", "Limitations", "Owner decision")
HOST_FIELDS = {"host", "version", "source", "source_digest", "commands", "input_origin", "authority", "privacy", "limitations", "evidence_class"}


def case_matrix() -> str:
    rows = ["| Case | Host | Expected | Actual | Candidate eligible | Binding failures | Evidence |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for case in load_cases(Path(__file__).parent / "cases"):
        result = evaluate_case(case)
        rows.append("| " + " | ".join([case["case"], case["host"], case["expected_outcome"], result["outcome"],
                    str(result["candidate_eligible"]).lower(), ", ".join(result["binding_failures"]) or "none", "simulated"]) + " |")
    return "\n".join(rows)


def validate_decision(decision: Mapping[str, object]) -> None:
    fields = {"status", "date", "owner", "choice", "owner_input_reference", "evidence_references",
              "verifier_trust", "unsupported_policy", "scope", "limitations", "stores_answer_text",
              "stores_conversations", "hashes_free_text", "tutor_can_invoke_verifier"}
    require(isinstance(decision, Mapping) and set(decision) == fields, "owner decision fields missing or unknown")
    require(decision["status"] == "approved", "owner-decision-pending: owner receipt contract choice is required")
    require(isinstance(decision["date"], str), "owner decision date invalid")
    try:
        date.fromisoformat(decision["date"])
    except ValueError:
        raise ValueError("owner decision date invalid") from None
    for key in ("owner", "owner_input_reference", "verifier_trust", "scope", "limitations"):
        require(isinstance(decision[key], str) and len(decision[key].strip()) >= 12, "owner decision attribution, trust or scope missing")
    require(decision["choice"] in {"isolated-confirmation", "defer-unverified"}, "owner decision mechanism unsupported")
    require(isinstance(decision["evidence_references"], list)
            and all(isinstance(ref, str) for ref in decision["evidence_references"])
            and set(decision["evidence_references"]) == {"#host-evidence", "#adversarial-results"}, "owner decision evidence references missing")
    require(decision["unsupported_policy"] == "unverified", "owner decision cannot verify unsupported provenance")
    for key in ("stores_answer_text", "stores_conversations", "hashes_free_text", "tutor_can_invoke_verifier"):
        require(decision[key] is False, "owner decision violates privacy or independent authority")


def audit_report(path: Path, require_decision: bool = False) -> Mapping[str, object]:
    text = path.read_text()
    require(all(f"## {section}\n" in text for section in SECTIONS), "report sections missing")
    blocks = re.findall(r"^```receipt-audit\n(.*?)\n```$", text, re.M | re.S)
    require(len(blocks) == 1, "report needs one audit block")
    report = json.loads(blocks[0])
    require(isinstance(report, dict) and set(report) == {"inspected_at", "hosts", "decision"}, "invalid report fields")
    require(isinstance(report["inspected_at"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", report["inspected_at"]) is not None, "inspection date missing")
    hosts = report["hosts"]
    require(isinstance(hosts, list) and len(hosts) == 3, "host evidence missing")
    for row in hosts:
        require(isinstance(row, dict) and set(row) == HOST_FIELDS, "host evidence fields missing or unknown")
        require(all(isinstance(row[key], str) and len(row[key].strip()) >= 12 for key in HOST_FIELDS - {"host", "commands", "evidence_class", "source_digest"}), "host evidence description missing")
        require(isinstance(row["commands"], list) and bool(row["commands"]) and all(isinstance(c, str) and len(c) >= 12 for c in row["commands"]), "host evidence commands missing")
        require(isinstance(row["source_digest"], str) and re.fullmatch(r"[0-9a-f]{64}", row["source_digest"]) is not None, "host evidence digest missing")
        require(row["evidence_class"] == "inspected", "host evidence must remain inspected; no host protocol was exercised")
        require(row["source"].startswith("https://"), "host evidence source missing")
    require({h["host"] for h in hosts} == HOSTS - {"unsupported"}, "host evidence set incomplete")
    require(case_matrix() in text, "adversarial results differ from experiment")
    decision = report["decision"]
    require(isinstance(decision, dict) and decision.get("status") in {"pending", "approved"}, "invalid owner decision")
    if decision["status"] == "approved":
        validate_decision(decision)
    else:
        require(set(decision) == {"status"}, "pending decision must not imply approval")
    if require_decision:
        require(decision["status"] == "approved", "owner-decision-pending: owner receipt contract choice is required")
        require(decision["choice"] != "defer-unverified", "owner-decision-deferred: records and settlement remain blocked")
    return report


def encode_results(results: list[Mapping[str, object]]) -> str:
    # Keep future internal diagnostics from expanding durable experiment output.
    return json.dumps([{key: result[key] for key in sorted(RESULT_FIELDS)} for result in results], sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cases", type=Path)
    group.add_argument("--audit-report", type=Path)
    group.add_argument("--require-decision", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cases is not None:
            print(encode_results(run_cases(args.cases)))
        else:
            audit_report(args.audit_report or args.require_decision, args.require_decision is not None)
            print("Receipt report complete; owner decision " + ("approved" if args.require_decision else "checked separately"))
    except ValueError as error:
        # JSON parse errors may contain input fragments; only our fixed diagnostics are safe.
        message = "invalid JSON" if isinstance(error, json.JSONDecodeError) else str(error)
        print("receipt assertion failed: " + message, file=sys.stderr)
        return 1
    except (OSError, TypeError, KeyError):
        print("receipt assertion failed: invalid input or unreadable source", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
