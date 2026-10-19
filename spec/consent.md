# Agent Courses 1.0: consent contract

This page defines the optional feedback a course may ask for and what must happen when a learner refuses. A course can ask; only the learner can agree. Refusing is always safe: the course carries on unchanged, and no account is needed at any point. The feedback fields below are a privacy-reviewed proposal and wait for the owner's review. Where the data goes, and the screen a platform shows, are outside this specification. The files that store consent are defined by a later record contract. Each rule is listed in [the requirement register](requirements.md); folder rules are in [the format contract](format.md) and teaching rules in [the execution contract](execution.md).

The words MUST, MUST NOT, SHOULD and MAY are used as in [the format contract](format.md#rules-and-advice). Examples are cases, built as [the format contract's case tables](format.md#case-tables) describe. Every case below starts from [the baseline course](format.md#baseline-course), plus the `feedback.yaml` shown under hooks, unless it says otherwise.

## No feedback unless declared <a id="declared-only"></a>

Feedback hooks live in an optional `feedback.yaml` at the course root, not in `COURSE.md`, so a privacy reviewer reads one short file. A course without `feedback.yaml` declares no collection. A runner MUST NOT ask a feedback question for such a course and MUST NOT send anything about it. Unknown keys in `feedback.yaml` are ignored, as [unknown keys](format.md#unknown-keys) describes.

## Hooks <a id="feedback-hooks"></a>

There are three hooks. Each collects a closed set of fields and nothing else.

```yaml
# feedback.yaml
rating: per-lesson
stuck: { after_failures: 3 }
questions:
  - id: provider
    ask: Which model provider do you use most?
    options: [Anthropic, OpenAI, Google, Other]
```

| Hook | Declaration | Collects | Never collects |
| --- | --- | --- | --- |
| `rating` | `per-lesson` or `at-end` | One integer from 1 to 5, chosen by the learner, with the lesson id for `per-lesson` | Free text, a note, anything the learner did not choose from the prompt |
| `stuck` | `after_failures`: a whole number from 2 to 10, default 3 | The lesson id, the check id and how many times in a row the check failed | Code, error output, file contents, paths, conversation |
| `questions` | A list of 1 to 5 entries, each with `id` (a kebab id, unique among the entries), `ask` (1 to 200 characters) and `options` (2 to 8 strings of 1 to 80 characters) | The id of the question and the position of the chosen option | Free text of any length |

The `stuck` count includes only results of `fail`. An `error` result is the course's own fault and never counts. A failing run is counted only while no pass has intervened.

### Fields for every hook <a id="payload-fields"></a>

A payload holds only the course name and version, the hook name and the fields in the table above. It MUST NOT contain code, file contents, file or project paths, a conversation, a free-text answer or a hash of one, an answer to a call, a learner identifier from the learner's record, or any machine identifier.

### Why free text is not allowed <a id="free-text"></a>

An earlier proposal allowed free text up to 280 characters. A short limit does not make text private: 280 characters can hold a name, a secret or a pasted line of code. This version collects only numbers and closed choices, so nothing the learner types freely is ever sent, and the length cap is no longer needed. Free text may return later only after a privacy review of exactly what it would hold.

### Hook cases <a id="example-hooks"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-hooks-valid-accepted"></a>Valid declaration | The `feedback.yaml` above, unchanged | Course syntax | Accepted | `rating` is a known declaration, `after_failures` is 3, and one question has an id, an ask and four options |
| <a id="case-hooks-boundaries-accepted"></a>Declaration boundary values | The `feedback.yaml` above with `rating: at-end`; `after_failures: 2` and, separately, `10`; and `stuck: {}`, whose omitted count means 3 | Course syntax | Accepted | `at-end` is a known declaration, and the stuck count is a whole number from 2 to 10 or omitted |
| <a id="case-hooks-questions-bounds-accepted"></a>Question count and option count boundaries | The `feedback.yaml` above with exactly one question and, separately, five questions with distinct kebab ids; a question with 2 options and, separately, 8 options | Course syntax | Accepted | The list has 1 to 5 entries and each has 2 to 8 options |
| <a id="case-hooks-text-bounds-accepted"></a>Text length boundaries | The `feedback.yaml` above with an `ask` of 1 character and, separately, 200 characters; an option of 1 character and, separately, 80 characters | Course syntax | Accepted | `ask` is 1 to 200 characters and each option is 1 to 80 |
| <a id="case-hooks-questions-zero-rejected"></a>No questions | `questions: []` with everything else as above | Course syntax | Rejected | The list has 0 entries, below 1 |
| <a id="case-hooks-questions-six-rejected"></a>Six questions | Six questions with distinct kebab ids | Course syntax | Rejected | The list has 6 entries, above 5 |
| <a id="case-hooks-ask-empty-rejected"></a>Empty ask | The question `provider` with `ask: ""` | Course syntax | Rejected | Length 0 is below 1 |
| <a id="case-hooks-ask-long-rejected"></a>Over-long ask | The question `provider` with a 201-character `ask` | Course syntax | Rejected | Length 201 exceeds 200 |
| <a id="case-hooks-option-empty-rejected"></a>Empty option text | The question `provider` with `options: [Anthropic, ""]` | Course syntax | Rejected | An option of length 0 is below 1 |
| <a id="case-hooks-option-long-rejected"></a>Over-long option text | The question `provider` with one 81-character option | Course syntax | Rejected | Length 81 exceeds 80 |
| <a id="case-hooks-options-many-rejected"></a>Nine options | The question `provider` with 9 options | Course syntax | Rejected | More than 8 options |
| <a id="case-hooks-question-id-form-rejected"></a>Question id not kebab | The question `provider` with `id: Provider` | Course syntax | Rejected | A question id is a kebab id |
| <a id="case-hooks-stuck-fraction-rejected"></a>Fractional or text stuck count | `stuck: { after_failures: 2.5 }` and, separately, `after_failures: "3"` | Course syntax | Rejected | The count must be a whole number |
| <a id="case-hooks-rating-rejected"></a>Unknown rating declaration | `rating: per-lesson-with-note` | Course syntax | Rejected | Not `per-lesson` or `at-end` |
| <a id="case-hooks-stuck-low-rejected"></a>Stuck count below range | `stuck: { after_failures: 1 }` | Course syntax | Rejected | Below 2 |
| <a id="case-hooks-stuck-high-rejected"></a>Stuck count above range | `stuck: { after_failures: 11 }` | Course syntax | Rejected | Above 10 |
| <a id="case-hooks-options-rejected"></a>Single option | A `questions` entry with `options: [Only one]` | Course syntax | Rejected | Fewer than two options |
| <a id="case-hooks-question-id-rejected"></a>Repeated question id | Two `questions` entries with `id: provider` | Course syntax | Rejected | Question ids are unique |
| <a id="case-hooks-payload-accepted"></a>Allowed payload | The learner's rating of lesson `make` is 4; the runner builds a payload of course `sample-course`, version `1.0.0`, hook `rating`, lesson `make` and the number 4 | Runner behaviour | Accepted | It holds only the course name and version, the hook name and the declared fields |
| <a id="case-hooks-rating-bounds-accepted"></a>Rating boundaries | The learner rates lesson `make` 1 and, separately, 5; the payload holds that integer | Runner behaviour | Accepted | The rating is an integer from 1 to 5 |
| <a id="case-hooks-rating-range-rejected"></a>Rating outside the range | The payload for lesson `make` holds a rating of 0 and, separately, 6 | Runner behaviour | Rejected | A rating above 5 or below 1 is not collected |
| <a id="case-hooks-rating-type-rejected"></a>Rating not an integer | The payload holds a rating of 3.5 and, separately, the word "four" | Runner behaviour | Rejected | The rating is one whole number |
| <a id="case-hooks-payload-path-rejected"></a>Payload holds a path | The rating payload of the first payload case (a payload of course `sample-course`, version `1.0.0`, hook `rating`, lesson `make` and the number 4) with `agent.py` added | Runner behaviour | Rejected | A payload MUST NOT contain a file or project path |
| <a id="case-hooks-payload-hash-rejected"></a>Payload holds an answer hash | The rating payload of the first payload case (a payload of course `sample-course`, version `1.0.0`, hook `rating`, lesson `make` and the number 4) with a hash of the learner's answer to `choose-tool` added | Runner behaviour | Rejected | A payload MUST NOT contain a hash of an answer or an answer to a call |
| <a id="case-hooks-payload-machine-rejected"></a>Payload holds a machine identifier | The rating payload of the first payload case (a payload of course `sample-course`, version `1.0.0`, hook `rating`, lesson `make` and the number 4) with the machine's host name added | Runner behaviour | Rejected | A payload MUST NOT contain any machine identifier |
| <a id="case-hooks-stuck-count-accepted"></a>Only failures count | `after_failures: 3`; `final-check` returns `fail`, `fail`, `error`, `fail` with no pass between | Runner behaviour | Accepted | The `error` is not counted, so the counts after each result are 1, 2, 2, 3 and the stuck hook may fire only after the fourth result |
| <a id="case-hooks-stuck-reset-accepted"></a>A pass resets the count | `after_failures: 3`; `final-check` returns `fail`, `fail`, `pass`, `fail`, `fail`, then `fail` | Runner behaviour | Accepted | The pass resets the run to 0. After the fifth result the count is 2, so nothing fires; the sixth result makes 3 consecutive failures, and only then may the stuck hook fire |
| <a id="case-hooks-stuck-reset-early-rejected"></a>A pass does not reset | `after_failures: 3`; `final-check` returns `fail`, `fail`, `pass`, `fail`, `fail`, `fail`; the runner counts failures cumulatively instead of resetting at the pass, so its counts are 1, 2, 2, 3 and it fires after the fourth result (3 failures in all) | Runner behaviour | Rejected | A failing run is counted only while no pass has intervened, so the fourth result is the first failure of a new run |
| <a id="case-hooks-stuck-error-counted-rejected"></a>An error counted | `after_failures: 3`; `final-check` returns `fail`, `fail`, `error`, `fail` with no pass; the runner counts the `error` as a failure, so its counts are 1, 2, 3 and it fires after the third result, when only two failures have occurred | Runner behaviour | Rejected | An `error` result is the course's own fault and never counts |
| <a id="case-hooks-feedback-key-warning"></a>Unknown key in the file | `feedback.yaml` with an extra top-level `theme: dark` | Course syntax | Accepted with a warning | Unknown keys in `feedback.yaml` are ignored and warned about |

#### Free-text cases <a id="example-free-text"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-free-text-warning"></a>Unknown `free_text` key | A `questions` entry with an extra `free_text: true` key | Course syntax | Accepted with a warning | The key is unknown, so it is ignored and no free text is ever collected |
| <a id="case-free-text-sent-rejected"></a>Typed text sent | The same entry; the runner asks for a typed answer and sends it because of that key | Runner behaviour | Rejected | Free text is not collected in 1.0, and an unknown key cannot turn it on |

#### Payload category cases <a id="example-payload-categories"></a>

These cases use a `questions` payload: course `sample-course`, version `1.0.0`, hook `questions`, question id `provider` and chosen position `1`. All values are illustrative.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-payload-question-accepted"></a>Question id and position only | The payload holds exactly the five fields above | Runner behaviour | Accepted | It holds only the course name and version, the hook name and the id and chosen position the hook collects |
| <a id="case-payload-code-rejected"></a>Code added | The same payload with the text `def tool(): return 1` added | Runner behaviour | Rejected | A payload MUST NOT contain code |
| <a id="case-payload-contents-rejected"></a>File contents added | The same payload with the contents of `agent.py` added | Runner behaviour | Rejected | A payload MUST NOT contain file contents |
| <a id="case-payload-conversation-rejected"></a>Conversation added | The same payload with the tutor's last message added | Runner behaviour | Rejected | A payload MUST NOT contain a conversation |
| <a id="case-payload-answer-rejected"></a>Raw call answer added | The same payload with the learner's typed answer to `choose-tool` added | Runner behaviour | Rejected | A payload MUST NOT contain an answer to a call |
| <a id="case-payload-learner-id-rejected"></a>Learner identifier added | The same payload with an identifier taken from the learner's record added | Runner behaviour | Rejected | A payload MUST NOT contain a learner identifier from the learner's record |

## Consent <a id="consent-rules"></a>

- **Skippable.** Every hook is skippable with one key press or one word.
- **Asked at most once per lesson.** After a refusal or a skip, a runner MUST NOT ask the same hook again in that lesson.
- **Seen first.** The runner shows each question, and the exact payload it would send, before it asks.
- **Per destination.** Nothing leaves the machine without the learner's explicit yes for that named destination. A yes for one destination is not a yes for another, and there is no blanket yes.
- **Silence is a no.** No answer, a skip, an unreadable answer and a timeout all mean no.
- **No coercion.** A runner MUST NOT make starting, continuing or completing a course depend on feedback. Evidence and settlement are never changed by it.
- **Withdrawal.** The learner can withdraw at any time. Sending stops at once. The runner MUST NOT keep unsent payloads after a refusal or a withdrawal, and MUST discard any it holds. The change is recorded as a consent change.
- **No account.** A feedback destination MUST NOT require the learner to sign up in order to start or finish a course. An account may be offered only after the learner has had value, and never required.

Whether and where the learner's consent is stored is defined by the record contract, which is pending. Until it lands, a runner keeps consent only for the current session unless the record contract says otherwise.

### Refusal and consent cases <a id="example-refusal"></a>

These cases use the `feedback.yaml` above, with two named destinations, `A` and `B`.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-declared-none-accepted"></a>No declaration | The course has no `feedback.yaml`; nothing is asked and nothing is sent | Runner behaviour | Accepted | A course without `feedback.yaml` declares no collection |
| <a id="case-declared-asked-rejected"></a>Asks without a declaration | The same course; the runner asks for a rating after a lesson | Runner behaviour | Rejected | A runner MUST NOT ask a feedback question for such a course |
| <a id="case-declared-sent-rejected"></a>Sends without a declaration | The same course; the runner sends a rating without asking | Runner behaviour | Rejected | A runner MUST NOT send anything about such a course |
| <a id="case-consent-shown-accepted"></a>Payload shown first | The runner shows the question and the exact payload it would send to `A`, then asks | Runner behaviour | Accepted | The runner shows the question and exact payload before asking |
| <a id="case-consent-yes-one-accepted"></a>Yes to one destination | The learner says yes to `A`; the payload goes to `A` only and `B` is asked separately | Runner behaviour | Accepted | A yes for one destination is not a yes for another |
| <a id="case-consent-yes-other-rejected"></a>One yes used for two | The learner says yes to `A`; the runner also sends to `B` | Runner behaviour | Rejected | Nothing leaves without an explicit yes for that named destination |
| <a id="case-consent-silence-rejected"></a>Silence sends | The learner never answers; the runner sends | Runner behaviour | Rejected | Silence is a no |
| <a id="case-consent-silence-accepted"></a>Silence is a no | The learner never answers; nothing is sent | Runner behaviour | Accepted | No answer, a skip, an unreadable answer and a timeout all mean no |
| <a id="case-consent-skip-accepted"></a>Skip is final for the lesson | The learner skips the rating prompt; nothing is sent and it is not asked again in that lesson | Runner behaviour | Accepted | After a refusal or a skip, the same hook is not asked again that lesson |
| <a id="case-consent-repeat-rejected"></a>Asked again after a refusal | The same skip; the runner asks the rating again in the same lesson | Runner behaviour | Rejected | A runner MUST NOT ask the same hook again in that lesson |
| <a id="case-consent-withdraw-accepted"></a>Withdrawal clears the queue | The learner says yes, then withdraws before the next lesson; sending stops and every payload still held is discarded | Runner behaviour | Accepted | Withdrawal stops sending and discards unsent payloads |
| <a id="case-consent-queue-rejected"></a>Queue sent after withdrawal | The same withdrawal; the runner sends a payload it queued earlier | Runner behaviour | Rejected | A runner MUST NOT keep or send unsent payloads after a refusal or withdrawal |
| <a id="case-refusal-continues-accepted"></a>Refusal changes nothing else | The learner declines every hook; the lesson `finish` runs with the same checks, evidence and settlement as for a learner who agreed, and no account is made | Runner behaviour | Accepted | Refusal never changes learning, evidence or settlement, and no account is required |
| <a id="case-refusal-signup-rejected"></a>Sign-up required | A destination requires a sign-up before the course continues | Runner behaviour | Rejected | A feedback destination MUST NOT require an account to start or finish |
| <a id="case-refusal-settlement-rejected"></a>Refusal changes settlement | The learner declines; the runner leaves `agent-passes` unsettled although `final-check` passed and every call was verified | Runner behaviour | Rejected | Evidence and settlement are never changed by feedback |

#### Coercion cases <a id="example-no-coercion"></a>

In each case the learner declines every feedback hook of the baseline `feedback.yaml`. The runner's other behaviour is unchanged.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-coercion-start-accepted"></a>Starting does not wait | The learner declines the rating prompt; the runner starts lesson `intro` at once | Runner behaviour | Accepted | Starting does not depend on feedback |
| <a id="case-coercion-start-rejected"></a>Starting waits for feedback | The runner will not start lesson `intro` until the learner answers the rating prompt | Runner behaviour | Rejected | A runner MUST NOT make starting depend on feedback |
| <a id="case-coercion-continue-accepted"></a>Continuing does not wait | The learner declines the rating prompt after `make`; the runner continues to the next lesson | Runner behaviour | Accepted | Continuing does not depend on feedback |
| <a id="case-coercion-continue-rejected"></a>Continuing waits for feedback | The runner will not continue past `make` until the learner answers the rating prompt | Runner behaviour | Rejected | A runner MUST NOT make continuing depend on feedback |
| <a id="case-coercion-complete-accepted"></a>Completing does not wait | The learner declines the final rating; the runner records the course as complete | Runner behaviour | Accepted | Completing does not depend on feedback |
| <a id="case-coercion-complete-rejected"></a>Completing waits for feedback | The runner will not record the course as complete until the learner answers the final rating | Runner behaviour | Rejected | A runner MUST NOT make completing depend on feedback |

#### Unsent payload cases <a id="example-unsent-payload"></a>

These cases use one unsent rating payload for destination `A` (course `sample-course`, hook `rating`, lesson `make`, rating 4) held in the queue before the learner decides. A runner that holds nothing has nothing to discard.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-retain-refusal-accepted"></a>Queue emptied on refusal | The learner skips the rating prompt; the runner discards the payload and the queue is empty | Runner behaviour | Accepted | A runner MUST discard unsent payloads after a refusal |
| <a id="case-retain-refusal-rejected"></a>Payload kept after refusal | The learner skips the rating prompt; the runner sends nothing but keeps the payload in the queue | Runner behaviour | Rejected | A runner MUST NOT keep unsent payloads after a refusal, even when it never sends them |
| <a id="case-retain-withdrawal-accepted"></a>Queue emptied on withdrawal | The learner withdraws; the runner stops sending, discards the payload and the queue is empty | Runner behaviour | Accepted | A runner MUST discard unsent payloads after a withdrawal |
| <a id="case-retain-withdrawal-rejected"></a>Payload kept after withdrawal | The learner withdraws; the runner sends nothing but keeps the payload in the queue | Runner behaviour | Rejected | A runner MUST NOT keep unsent payloads after a withdrawal, even when it never sends them |
| <a id="case-retain-empty-accepted"></a>Nothing to discard | The learner skips the rating prompt when no payload was ever queued; the queue is empty and stays empty | Runner behaviour | Accepted | An empty queue is the required end state |
