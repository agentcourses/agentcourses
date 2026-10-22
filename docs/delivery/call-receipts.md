# Learner-decision receipt experiment

A receipt should distinguish a learner's decision from a tutor's assertion.
This offline experiment exposes the authority needed to make that distinction.
No inspected host signal alone establishes learner ownership against a tutor with tools and filesystem access.
On 19 October 2026, hnrly approved the capability contract; actual hosts require separate qualification.

## Host evidence

Evidence was inspected on 19 October 2026, without model turns, credentials or private transcripts.
The sources and reproduction commands below identify exactly what was read.
“Inspected” means documentation, source or schema inspection; “demonstrated” requires an exercised provenance boundary.
No actual host has demonstrated that boundary here.
“Simulated” identifies the synthetic authority model only.

Claude's [hook reference](https://code.claude.com/docs/en/hooks#userpromptsubmit) describes non-human prompt triggers as well as submitted text.
Its [configuration reference](https://code.claude.com/docs/en/hooks#hook-locations) places hooks in user, project and managed settings.
The local version command identifies the installed binary; it does not bind the mutable documentation to that binary.
The recorded HTML digest identifies the inspected snapshot; a later download can differ.

Codex's [pinned app-server source](https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/app-server/README.md) describes client-submitted input.
The installed binary exported schemas containing text inputs and answer arrays.
The client remains the authority; the names “user input” and “answers” provide no independent human authentication.
Exporting a schema demonstrates export availability, not a trustworthy receipt.

Pydantic AI's [pinned message source](https://github.com/pydantic/pydantic-ai/blob/54a31abfb7bb2a4354528ba4693ec2618afabf6e/pydantic_ai_slim/pydantic_ai/messages.py) permits application-constructed prompt content.
Its [agent source](https://github.com/pydantic/pydantic-ai/blob/54a31abfb7bb2a4354528ba4693ec2618afabf6e/pydantic_ai_slim/pydantic_ai/agent/__init__.py) accepts supplied prompt and history parameters.
Its release API identified v2.57.0 at that commit during inspection.
No inference was invoked, and no embedded application was tested.

The audit block is evidence metadata, not a normative record schema.
Commands write public source definitions to temporary files only.
A reviewer repeats them and inspects the named fields, rather than trusting the digest alone.

```receipt-audit
{
  "inspected_at": "2026-10-19",
  "hosts": [
    {
      "host": "claude-code",
      "version": "Installed Claude Code 2.1.303; unversioned official docs snapshot, 2026-10-19",
      "source": "https://code.claude.com/docs/en/hooks#userpromptsubmit",
      "source_digest": "0c076da787f31be27a0bafa5f97e41cc15ed3621e6edab77b3f3556d7da08df2",
      "commands": [
        "claude --version",
        "curl -fLsS -A \"AgentCourses offline interface inspection\" https://code.claude.com/docs/en/hooks -o /tmp/ac-claude-hooks.html",
        "shasum -a 256 /tmp/ac-claude-hooks.html"
      ],
      "input_origin": "UserPromptSubmit includes prompt text; also scheduled, background and other-session input.",
      "authority": "Project/user hooks are configuration files. A tutor with write/tool access can alter or invoke ordinary hook scripts; managed policy needs independent administration.",
      "privacy": "Prompt and transcript_path can reach a local hook. Do not read transcripts or log prompt payloads.",
      "limitations": "Docs inspection only. No hook execution, installed-binary behaviour proof, or host provenance guarantee.",
      "evidence_class": "inspected"
    },
    {
      "host": "codex",
      "version": "Installed codex-cli 0.163.0; locally generated stable app-server JSON schemas",
      "source": "https://github.com/openai/codex/blob/rust-v0.163.0/codex-rs/app-server/README.md",
      "source_digest": "835e0d4ca1a0ddc4fb6db1e2b3249dd67f07c50ac2506092ba81543efc92829b",
      "commands": [
        "codex --version",
        "codex app-server generate-json-schema --out /tmp/ac-codex-0.163.0",
        "python3 -c 'import json; from pathlib import Path; p=Path(\"/tmp/ac-codex-0.163.0\"); print(json.loads((p/\"v2/TurnStartParams.json\").read_text())[\"properties\"][\"input\"]); print(json.loads((p/\"ToolRequestUserInputResponse.json\").read_text())[\"properties\"][\"answers\"])'",
        "shasum -a 256 /tmp/ac-codex-0.163.0/v2/TurnStartParams.json"
      ],
      "input_origin": "Client supplies turn/start input text and user-input response answer arrays.",
      "authority": "The app-server client controls submitted strings. Tutor access to client code, tools, configuration or its transport defeats role-based attribution.",
      "privacy": "Input/answer payloads are free text. Exported schemas contain definitions only; no thread or message history was read.",
      "limitations": "Schema export exercised; provenance behaviour only inspected. No server session, model turn, or human-authenticated client was demonstrated.",
      "evidence_class": "inspected"
    },
    {
      "host": "embedded",
      "version": "Pydantic AI v2.57.0; immutable release commit 54a31abfb7bb2a4354528ba4693ec2618afabf6e",
      "source": "https://github.com/pydantic/pydantic-ai/blob/54a31abfb7bb2a4354528ba4693ec2618afabf6e/pydantic_ai_slim/pydantic_ai/messages.py",
      "source_digest": "2784856cdca0104859c8e8a44ebd06e5c17f2bbe6db9c6e433595b36f33c24b3",
      "commands": [
        "curl -fLsS https://raw.githubusercontent.com/pydantic/pydantic-ai/54a31abfb7bb2a4354528ba4693ec2618afabf6e/pydantic_ai_slim/pydantic_ai/messages.py -o /tmp/ac-pydantic-messages.py",
        "curl -fLsS https://raw.githubusercontent.com/pydantic/pydantic-ai/54a31abfb7bb2a4354528ba4693ec2618afabf6e/pydantic_ai_slim/pydantic_ai/agent/__init__.py -o /tmp/ac-pydantic-agent.py",
        "rg -n \"class UserPromptPart|user_prompt:|message_history:\" /tmp/ac-pydantic-messages.py /tmp/ac-pydantic-agent.py",
        "shasum -a 256 /tmp/ac-pydantic-messages.py /tmp/ac-pydantic-agent.py"
      ],
      "input_origin": "Application supplies user_prompt and message_history; UserPromptPart content is application-constructible.",
      "authority": "Application operator controls request handling and history. A separate learner input controller could qualify only if tutor tools cannot call or replace it.",
      "privacy": "Application may keep history at its chosen location. This experiment installs nothing, sends nothing to a model, and retains no learner text.",
      "limitations": "Pinned source inspection only; no embedded application, authenticated UI or deployed separation was demonstrated.",
      "evidence_class": "inspected"
    }
  ],
  "decision": {
    "status": "approved",
    "date": "2026-10-19",
    "owner": "hnrly (repository owner)",
    "choice": "isolated-confirmation",
    "owner_input_reference": "Owner hnrly, current implementation session, 19 October 2026: \u201cApprove the capability contract; qualify hosts separately (Recommended)\u201d. This answered the explicit question requiring learner-controlled confirmation outside tutor authority, a protected verifier and replay protection, no answers or answer hashes, separate host qualification, and unverified unsupported hosts that cannot settle objectives.",
    "evidence_references": [
      "#host-evidence",
      "#adversarial-results"
    ],
    "verifier_trust": "A learner-controlled confirmation path that tutor tools cannot alter or invoke; protected verifier, configuration, transport and durable replay protection. Qualification must establish that authority separately for each host.",
    "unsupported_policy": "unverified",
    "scope": "Required receipt capability only. Actual hosts qualify separately; no inspected host is qualified by this experiment. Unsupported provenance stays unverified and cannot settle objectives.",
    "limitations": "The owner approves the capability boundary, not a concrete mechanism, production fields, signing scheme or demonstrated host support. Synthetic eligibility remains simulated. Actual verifier isolation and durable replay protection require separate host qualification.",
    "stores_answer_text": false,
    "stores_conversations": false,
    "hashes_free_text": false,
    "tutor_can_invoke_verifier": false
  }
}
```

The companion pinned agent source had SHA-256 `70863339252f37faf8a0f30bb3503210e99725f5721a2932f3c14bcc359b57fa`.
The Codex answer-response schema had SHA-256 `5073b245f741fa8ce62ec52e4dd1809b7831f9c4284c279a78abc9b171f8e3f2`.
The pinned Codex app-server README had SHA-256 `d8e489c92adeb9d33bcbbcc5ff78431e839fdb2d6cefccb16812316bc22f5573`.

## Threat boundary

A cooperative tutor can label an input honestly; a tutor with tool access can manufacture the same public fields.
A role string, input callback, local file or signature from a reachable signer cannot distinguish those cases.
These are deductions from the inspected interfaces and synthetic model, not demonstrated attacks on those hosts.

The isolated-confirmation candidate assumes a learner-controlled input path outside tutor authority.
Its controller, configuration, transport, replay ledger and any signer must resist tutor reads, writes and invocations.
A confirmation binds a course snapshot, lesson, call, input occurrence and fresh challenge.
These names are experiment labels; no production fields, secret format or signing algorithm are selected.
Merely putting a secret in another file under the same tutor's authority supplies no boundary.

## Adversarial results

Run the [experiment](../../experiments/call-receipts/probe.py) with its [synthetic cases](../../experiments/call-receipts/cases/boundary.json):

```bash
uv run --locked python experiments/call-receipts/probe.py --cases experiments/call-receipts/cases
uv run --locked pytest tests/receipts/test_boundary.py -q
```

Candidate eligibility tests the assumed authority model, not learner provenance in a real host.
All success-shaped inputs stay unverified because simulated authority does not qualify an actual host.
Known tutor input and binding failures reject; missing or unsupported provenance stays unverified.

| Case | Host | Expected | Actual | Candidate eligible | Binding failures | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| changed-call | embedded | rejected | rejected | false | call | simulated |
| changed-occurrence | embedded | rejected | rejected | false | occurrence | simulated |
| changed-challenge | embedded | rejected | rejected | false | challenge | simulated |
| automated-hook | claude-code | rejected | rejected | false | none | simulated |
| unknown-host | unsupported | unverified | unverified | false | none | simulated |
| genuine-isolated | embedded | unverified | unverified | true | none | simulated |
| tutor-authored | embedded | rejected | rejected | false | none | simulated |
| missing | embedded | unverified | unverified | false | none | simulated |
| repeated | embedded | rejected | rejected | false | replay | simulated |
| changed-snapshot | embedded | rejected | rejected | false | snapshot | simulated |
| cross-lesson | embedded | rejected | rejected | false | lesson | simulated |
| claude-code-filesystem | claude-code | unverified | unverified | false | none | simulated |
| claude-code-tools | claude-code | unverified | unverified | false | none | simulated |
| claude-code-configuration | claude-code | unverified | unverified | false | none | simulated |
| claude-code-signer | claude-code | unverified | unverified | false | none | simulated |
| claude-code-public-envelope | claude-code | unverified | unverified | false | none | simulated |
| claude-code-tutor-controller | claude-code | unverified | unverified | false | none | simulated |
| codex-filesystem | codex | unverified | unverified | false | none | simulated |
| codex-tools | codex | unverified | unverified | false | none | simulated |
| codex-configuration | codex | unverified | unverified | false | none | simulated |
| codex-signer | codex | unverified | unverified | false | none | simulated |
| codex-public-envelope | codex | unverified | unverified | false | none | simulated |
| codex-tutor-controller | codex | unverified | unverified | false | none | simulated |
| embedded-filesystem | embedded | unverified | unverified | false | none | simulated |
| embedded-tools | embedded | unverified | unverified | false | none | simulated |
| embedded-configuration | embedded | unverified | unverified | false | none | simulated |
| embedded-signer | embedded | unverified | unverified | false | none | simulated |
| embedded-public-envelope | embedded | unverified | unverified | false | none | simulated |
| embedded-tutor-controller | embedded | unverified | unverified | false | none | simulated |

## Privacy

The output allowlist is case, host, outcome, binding failures, evidence class and candidate eligibility.
No answer, transcript, conversation, path to a private transcript, or free-text answer hash enters durable outputs.
Synthetic answers used by tests exist only in memory or temporary input files and never in checked-in cases.
A hash of a short private answer would remain guessable; it is not a privacy substitute.
Snapshot and binding labels in this experiment are synthetic identifiers, not hashes of learner text.

An isolated confirmation would retain only binding identifiers, an input occurrence, a challenge and a verifier result.
Even those identifiers can correlate activity, so access and retention still need a reviewed runner policy.
A public-envelope design costs less integration work but cannot establish learner ownership.
Host-local prompt histories may already exist; the experiment neither reads nor erases them.
Learner-record minimisation cannot promise removal from a learner's chosen host.

## Limitations

The model trusts its fixture authority declarations because it is a simulation.
Passing it cannot qualify a host or prove a learner was human, attentive or unaided.
No actual controller isolation, anti-replay durability, UI intent display, restart recovery or production verifier was demonstrated.
A production design must independently prove those properties, including tutor tool and configuration reachability.
Deleting an in-memory used-occurrence list resets this model; persistent anti-replay is an explicit unproved dependency.

No inspected stock host currently has a demonstrated receipt boundary from this work.
Unknown hosts, missing input, ordinary callbacks and reachable signers must preserve unverified status.
Unverified calls cannot support objective settlement; skipped work must never become passed work.
No production runner, adapter or learner record was created.

## Owner decision

<details>
<summary>Initial pending report and choices — 19 October 2026, before owner approval</summary>

The text below preserves the earlier pending state and the options presented to the owner.
Its gate instructions describe that earlier state.

**Pending.** No dated owner approval or receipt mechanism has been supplied.
The report audit can pass independently, but `--require-decision` and final `make check` must fail.
Record drafting and theme completion remain blocked.

The concrete choices are:

| Option | What a verifier would trust | Privacy cost | Consequence |
| --- | --- | --- | --- |
| Approve an isolated-confirmation capability contract | A separately controlled learner input path, protected verifier and durable replay ledger; each host needs independent qualification | Binding identifiers and minimal verification metadata, no answer text or answer hashes | No current host qualifies from this experiment; unsupported hosts retain unverified calls |
| Retain unverified provenance and require a demonstrated host before selecting a contract | No current host signal counts as learner proof | No new receipt persistence | Records and candidate settlement remain blocked until a qualifying demonstration |

Recommendation: accept the isolated boundary only as a required capability, if the owner accepts unsupported-host limits.
This recommendation does not approve a mechanism or imply stock Claude Code or Codex support.
If a usable stock-host receipt is required now, the evidence supports stopping for a new proof rather than weaker attribution.

After a choice, append a dated entry naming the owner, exact choice, evidence references, verifier trust, scope and limitations.
Name the unsupported-host policy and forbid answer text, conversations and free-text hashes.
A fresh reviewer must compare the attribution against the owner's actual input.
Then implement the chosen decision validation, rerun the decision gate and full checks, and resume dependent work.

</details>

### Approved capability contract — 19 October 2026

Owner **hnrly** approved the required capability boundary in the current implementation session on 19 October 2026.
The exact selected option was: **“Approve the capability contract; qualify hosts separately (Recommended)”**.
This answered the explicit question requiring protected learner confirmation, verifier authority and replay protection.
The evidence is the inspected [host interfaces](#host-evidence) and synthetic [adversarial results](#adversarial-results).
This approval replaces the pending gate state above; it does not qualify any host.

A verifier must trust a learner-controlled confirmation path that tutor tools cannot alter or invoke.
The verifier, its configuration, transport and replay protection must remain outside tutor authority.
Each actual host must establish that separation independently before its receipt can establish learner ownership.
A confirmation must resist replay and bind the relevant course snapshot, lesson, call and input occurrence.
The experiment's challenge is a binding illustration; no production field or signing scheme is selected here.

No answer text, conversations or answer hashes may enter receipt records.
Unsupported hosts, missing provenance and unqualified boundaries remain **unverified** and **cannot settle objectives**.
Known tutor-made decisions cannot count as learner decisions.
A separately qualified host still needs the other required objective evidence; a receipt alone cannot settle an objective.

The approved scope is the capability contract, with actual host qualification performed separately.
Claude Code, Codex and the embedded boundary remain inspected only in this report.
Synthetic candidate eligibility remains simulated; no actual host or concrete receipt mechanism is approved by this experiment.
Isolation and durable replay protection remain qualification requirements, not demonstrated implementation claims.

The owner-choice gate can now be checked against this attributable approval.
Next, run report audit, required-decision validation and the full repository gate, then obtain fresh final review.
Dependent contract drafting consumes this capability boundary and must retain its unsupported-host limits.
