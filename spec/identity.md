# Agent Courses 1.0: pinned course identity

This page defines how a runner turns a course folder into one short identity string. The string pins the exact bytes a learner installed. Two runners given the same folder produce the same string, and a different folder produces a different one. The page fixes every choice that could make two implementations disagree: which entries count, how they are ordered, how text is read and how the bytes are framed before hashing. The record files that store the string are defined in [the record contract](records.md).

This is a pre-release specification. Identity proves which bytes were installed. It does not identify the publisher or establish safety, and it qualifies no runner.

## Snapshot identity <a id="candidate-identity"></a>

Identity computation is independent of course interpretation and does not select an interpreter.
[Trusted installation provenance](records.md#candidate-provenance) selects the interpretation before retained metadata is read.
Changing authored paths or frontmatter produces a different identity.
Preserve retained snapshots and published schema bytes exactly; never mutate or relabel them to repair a mismatch.
An explicit learner upgrade may select a separate snapshot under the [upgrade rules](records.md#upgrade-projection).
A matching digest or protected transition binding is insufficient to infer original installation provenance.

### Snapshot cases <a id="candidate-identity-cases"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-candidate-identity-retained-accepted"></a>Retained snapshot | Retain the exact trace tree with trusted installation provenance | Identity computation | Accepted | Its bytes reproduce its digest |
| <a id="case-candidate-identity-migration-accepted"></a>Changed course content | Make a separate copy and change its frontmatter | Identity computation | Accepted | Different included bytes produce a distinct digest |
| <a id="case-candidate-identity-rewrite-rejected"></a>Retained snapshot rewritten | Change a retained tree without a new snapshot | Pin check | Rejected | The existing pin refuses changed bytes |
| <a id="case-candidate-identity-inferred-rejected"></a>Digest used as provenance | A retained tree matches its digest but trusted installation provenance is missing | Retained interpretation | Rejected | `req-record-replay-data`; byte identity cannot establish interpretation |

## Reading this page <a id="reading"></a>

The words MUST, MUST NOT, SHOULD and MAY are used as in [the format contract](format.md#rules-and-advice). Cases are rows in tables built as [the format contract's case tables](format.md#case-tables) describe, with two extra subjects. *Identity computation* judges whether a folder gives a digest or is refused. *Pin check* judges what a runner does when it compares an identity with a lock entry.

Most computation cases are vectors in [the vector manifest](../examples/identity-vectors/manifest.json). A vector names a baseline tree, a short list of changes to it and the expected digest or refusal. [The vector manifest](#vectors) section describes the shape. An implementation that follows this page reproduces every digest in the manifest.

## What identity is for <a id="purpose"></a>

A course is code someone else wrote, and the learner's record points at one exact version of it. Identity lets a runner detect three things without a network: the installed folder was edited, a different payload claims the same name and version, and an upgrade really changed content. The [pinning rules](#pinning) say what a runner does in each case.

The identity string is `sha256:` followed by sixty-four lowercase hexadecimal digits. The prefix names the hash. A later layout or hash would use a new prefix, so a reader never guesses which rules produced a string.

## The folder that is hashed <a id="identity-root"></a>

The *root* is the course folder: the directory that holds `COURSE.md`. The runner opens the root as a directory. Operating-system links in the path that leads to the root are followed once, so a course installed through a link still has an identity. Everything below the root is examined without following links.

The root MUST hold a regular file named `COURSE.md`. A folder without one is not a course and has no identity. A link named `COURSE.md` does not count. Both outcomes are refused with `not-a-course`.

A local project folder named by a course's `project:` field is inside the course folder, so its files are part of the identity. A Git project reference is not inside the folder and is pinned by its own commit, which [the record contract](records.md#project-record) stores.

## Entries <a id="identity-entries"></a>

The runner walks the root and builds a list of *entries*. It looks at each name with the operating system's no-follow call, so a link is seen as a link. Each name is one of four things.

| Found | Entry type | What it carries |
| --- | --- | --- |
| A regular file | `f` | The file's bytes, after the [text rule](#identity-text) |
| A symbolic link | `l` | The link's target text, as [Links](#identity-links) describes |
| A directory with no entries inside it after [exclusions](#identity-exclusions) | `d` | Nothing |
| A directory with entries inside it | none | It has no entry of its own; its contents carry it |
| Anything else, such as a named pipe, socket or device | none | The whole computation is refused with `special-file` |

An empty directory is an entry because a valid course can depend on one: an empty failing fixture folder is accepted by [the execution contract](execution.md#example-fixtures). A directory that holds only excluded names counts as empty. A course distributed through Git cannot carry an empty directory, so its author places a file in it, and that file becomes part of the identity.

A name that cannot be read, or a directory that cannot be listed, is refused with `unreadable`. A runner MUST NOT skip it. File modes, owners, times and extended attributes are not part of identity. A course therefore cannot rely on an executable bit being pinned, and its checks name an interpreter in their `run` command.

## Exclusions <a id="identity-exclusions"></a>

Four exact rules remove names from the walk. Nothing else is excluded, and an excluded name is not examined, so it cannot cause a refusal.

1. Any name equal to `.git`, at any depth, with everything under it.
2. Any name equal to `.DS_Store`, at any depth.
3. The name `.agents` directly under the root, with everything under it. It holds runner state: learner records, the course lock and installed courses.
4. The name `_site` directly under the root, with everything under it. It is the folder generated pages are written to.

Rules 3 and 4 apply only at the root. A folder with the same name deeper in the tree is course content. A course MUST NOT use `_site` or `.agents` at its root for content, because that content would never be pinned.

## Paths <a id="identity-paths"></a>

Each included entry has a *path*: the names from the root down to it, joined by `/`, with no leading or trailing separator. Every name (component) in a path MUST pass these tests, or the whole computation is refused with `invalid-path`.

- It is valid UTF-8 as defined in RFC 3629.
- It is not empty, `.` or `..`.
- It holds no code point from U+0000 to U+001F, no U+007F and no backslash.
- It is in Unicode Normalization Form C.
- It is at most 255 bytes long, and the whole path is at most 1024 bytes.

No path is normalised or repaired. A folder listing that offers a parent component, such as one read from an archive, is refused, and nothing outside the root is read.

Case collisions are judged over *every* path, not only entries. Take each included entry's path and every directory prefix of it, so `Docs/a.md` contributes `Docs` and `Docs/a.md`. Collect the distinct paths. If two different paths in that set are equal after Unicode full case folding and then Normalization Form C, the computation is refused with `case-collision`. A case-insensitive file system would merge `Docs/a.md` and `docs/b.md` into one folder, and it cannot hold a file `README` beside a folder `readme/x`, so the same checkout would give another identity there.

## Links <a id="identity-links"></a>

A symbolic link is an entry of type `l`. Its payload is the link's target text exactly as the operating system reports it, with no resolution, no separator change and no check that the target exists. A link is never followed. A link to a file outside the root, to nothing, or to its own parent therefore has an identity, and the target is never read.

The target text MUST be non-empty, valid UTF-8, at most 4096 bytes and free of zero bytes, or the computation is refused with `invalid-link`. A source that cannot hold a link, such as an archive format without them, cannot give an identity for a course that has one, and the runner MUST fail rather than approximate.

Links that matter to learners are judged elsewhere. [The format contract](format.md#local-projects) refuses a project link that escapes its source before copying. Identity only records what the folder holds.

## Text and bytes <a id="identity-text"></a>

A file is *text* when its bytes are valid UTF-8 and contain no zero byte. Otherwise it is *binary*. A binary file is hashed exactly as stored.

A text file is hashed after one change: each two-byte pair carriage return then line feed (`0D 0A`) is replaced by the single byte line feed (`0A`), scanning from the start, once. A lone carriage return is kept. The bytes `0D 0D 0A` therefore become `0D 0A`. A byte order mark is content and is kept. Unicode normalisation is not applied to contents, so a word written with a combined accent and the same word written with a combining accent are different.

Reading CRLF as LF lets Git on a platform that converts line endings produce the same identity as another platform, so a team's lock does not break on a checkout. The cost is that a course cannot pin a deliberate CRLF-only difference in a text file. A checkout filter that rewrites other bytes, such as a content filter, gives a different identity, and the runner refuses it as a mismatch instead of repairing it.

## Ordering <a id="identity-ordering"></a>

Entries are sorted by comparing the unsigned bytes of their whole UTF-8 paths, from the first byte, with the shorter path first when one is a prefix of the other. This is the same as ordering by code point. It is not a locale order, not a case-insensitive order, not UTF-16 order and not directories-first. The path `a.md` therefore sorts before `a/x.md`, because `.` is `2E` and `/` is `2F`, and a path starting with an uppercase letter sorts before every lowercase one.

## Framing and digest <a id="identity-digest"></a>

The hashed byte string is built in this order.

1. The header: the ASCII text `agent-courses-identity-1` followed by a line feed (25 bytes).
2. For each entry in order: the one-byte type (`f`, `l` or `d`, as ASCII), the path length as an unsigned 64-bit big-endian integer, the path bytes, the payload length as an unsigned 64-bit big-endian integer, then the payload bytes.

The identity is `sha256:` followed by the SHA-256 digest of that byte string in lowercase hexadecimal. Every length is written, so a boundary between two files, or between a path and its content, can never be moved without changing the digest.

### A worked example <a id="identity-worked-example"></a>

The root holds `COURSE.md` with the three bytes `hi` and a line feed, an empty directory `fail`, and a link `go` whose target text is `COURSE.md`. Sorted by bytes, the order is `COURSE.md`, `fail`, `go`. The byte string, in hexadecimal and split by part, is:

```text
6167656e742d636f75727365732d6964656e746974792d310a            header
660000000000000009434f555253452e6d64000000000000000368690a    COURSE.md
6400000000000000046661696c0000000000000000                    fail
6c0000000000000002676f0000000000000009434f555253452e6d64      go
```

Its SHA-256 is `70dc1a84f335a8118e54c7d38a2088551bf13add821f0c5f6666e1593a446a75`, so the identity is `sha256:70dc1a84f335a8118e54c7d38a2088551bf13add821f0c5f6666e1593a446a75`. Anyone can check it with any tool that hashes bytes. This tree is explanatory; the shared vectors use the baseline tree in the manifest.

## Refusals <a id="identity-errors"></a>

A computation either returns an identity or is refused with one of these identifiers. A tree with several faults is refused, and which identifier is reported is not defined; every vector holds exactly one fault.

| Identifier | Meaning |
| --- | --- |
| `not-a-course` | The root has no regular file `COURSE.md` |
| `special-file` | An included name is a pipe, socket, device or other special file |
| `unreadable` | An included file cannot be read or an included directory cannot be listed |
| `invalid-path` | A path component fails the path tests |
| `case-collision` | Two different included paths, or directory prefixes of them, collide after case folding |
| `invalid-link` | A link target fails the link tests |

## Pinning <a id="pinning"></a>

The identity is stored in the course lock, whose fields [the record contract](records.md#lock-file) defines. Five duties follow.

1. **Install.** A runner computes the identity of the course it fetched before it writes anything. If the lock already holds the same name and version with a different identity, it MUST refuse the payload and change nothing. It MUST NOT replace the installed folder or the lock entry.
2. **Resume.** Before teaching from an installed course, the runner MUST recompute the identity of the installed folder and compare it with the lock. A difference means the installed folder was edited or damaged. The runner MUST refuse to teach from it, tell the learner, and write no record event. It MUST NOT silently re-lock or fetch a newer copy.
3. **Upgrade.** A new version, or new bytes under the same version, replaces the pinned course only when the learner explicitly asks for an upgrade. The runner never substitutes the latest version on its own. [The record contract](records.md#upgrades) says what an upgrade writes.
4. **Sources.** A Git reference also records the commit it resolved, and the commit is the pin the runner resolves again. The identity is the second check, computed over the installed folder. Recovery uses the committed transition before teaching; it never treats a torn install as a new pin. A local-folder install has no commit, and a runner MUST NOT invent one. A mismatch between commit and identity on a later install is a refusal under duty one.

5. **Retention.** Before committing a start or upgrade, retain the complete identity-included authored tree under `.agents/course-snapshots/<digits>/<course>/`. Preserve bytes, link text and empty directories. Recompute its identity and validate the course from stable protected bytes whenever replay requires it. Folder labels and cached metadata are not proof. Keep every applied snapshot for its history's lifetime. [Retained sources](records.md#replay-data) fixes safe lookup, structural checks and stop outcomes; [durable transitions](records.md#transition-durability) fixes publication and recovery order. Authored folders stay outside personal record payloads and are locally excluded from Git.

Identity is not authenticity. It proves the bytes are the ones first installed, not that a publisher approved them. A runner MUST NOT describe an identity as a signature or a verified publisher.

## The vector manifest <a id="vectors"></a>

[The manifest](../examples/identity-vectors/manifest.json) is a JSON object with the layout token `identity` (`agent-courses-identity-1`), the hash `algorithm`, a `roots` table and a list of `vectors`. Each root names a folder under the manifest's directory and an `input_path` to its `COURSE.md`, which the repository's document check requires to exist.

Each vector holds:

- `case`: a unique kebab name, used in the cases below.
- `root`: the key of a root. The baseline root is a small tree of three files, not a course to teach, so its `COURSE.md` has no frontmatter.
- `changes`: operations applied, in order, to a copy of the root. `write` sets a file from `text` (UTF-8) or `bytes_hex`. `mkdir` makes a directory. `symlink` makes a link from `target` or `target_hex`. `fifo` makes a named pipe. `chmod` with mode `000` makes an entry unreadable. `remove` deletes a path and everything under it. All paths are relative to the root.
- `requires`: what the harness needs. `listing` means the input cannot be stored portably and is tested as a list of paths and contents. `symlinks`, `fifo` and `unprivileged-reads` need those abilities. A harness that lacks one reports the vector as not run, never as passed.
- `expected_digest` or `expected_error`: exactly one of them.
- `rule`: the anchor of the rule it exercises, on this page.
- `explanation`: a plain sentence saying why.

Expected digests were calculated by two programs in different languages, Python and Node, each written from this page, and the worked example was also checked with `shasum`. One author wrote both programs, so reproduction by a later implementation is still required. A later proof calculates the digests again and never copies them from the function under test.

## Identity cases <a id="example-identity"></a>

Every case starts from the baseline tree in the manifest and applies the change in the second column. The outcome *Accepted* means an identity is produced; *Rejected* means the computation is refused with the stated identifier.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-id-baseline-accepted"></a>Baseline | Vector `baseline` | Identity computation | Accepted | Three included files give one fixed digest |
| <a id="case-id-byte-change-accepted"></a>One byte changes | Vector `byte-change`: one character of a lesson | Identity computation | Accepted | The digest differs from the baseline, so a content change is detected |
| <a id="case-id-rename-accepted"></a>Renamed file | Vector `rename-changes-digest`: the same bytes under another path | Identity computation | Accepted | The path is part of each entry, so the digest differs |
| <a id="case-id-empty-directory-accepted"></a>Empty directory | Vector `empty-directory-counts` | Identity computation | Accepted | An empty directory is an entry of type `d` |
| <a id="case-id-ignored-empty-accepted"></a>Only an excluded file inside | Vector `ignored-file-leaves-directory-empty` | Identity computation | Accepted | The directory is empty after exclusions, so the digest equals the empty-directory vector |
| <a id="case-id-ordering-accepted"></a>Bytewise ordering | Vector `ordering-bytewise` | Identity computation | Accepted | Paths sort by unsigned UTF-8 bytes; case-insensitive, directory-first and per-segment orders give other digests |
| <a id="case-id-utf16-accepted"></a>Code point order | Vector `ordering-code-point-not-utf16` | Identity computation | Accepted | A three-byte name sorts before a four-byte name, which UTF-16 order would reverse |
| <a id="case-id-locale-order-rejected"></a>Locale order | A runner sorts paths with a locale-aware, case-insensitive comparison | Identity computation | Rejected | Entries sort by bytes, so the digest of `ordering-bytewise` would differ |
| <a id="case-id-unframed-rejected"></a>Lengths left out | A runner joins path and content bytes without their lengths | Identity computation | Rejected | The two `framing-boundary` vectors would give the same digest, and they must differ |
| <a id="case-id-framing-accepted"></a>Path and content boundary | Vectors `framing-boundary-a` and `framing-boundary-b` | Identity computation | Accepted | Joined path and content bytes are equal in both, yet the digests differ, because lengths are framed |
| <a id="case-id-content-split-accepted"></a>Content boundary between files | Vectors `content-split-a` and `content-split-b` | Identity computation | Accepted | Joined contents are equal in both, yet the digests differ |
| <a id="case-id-crlf-accepted"></a>CRLF read as LF | Vector `line-endings-crlf`: the lesson rewritten with CRLF | Identity computation | Accepted | Text files hash with CRLF read as LF, so the digest equals the baseline |
| <a id="case-id-crlf-kept-rejected"></a>CRLF hashed as written | A runner hashes the CRLF lesson of `line-endings-crlf` as written | Identity computation | Rejected | Text files hash with CRLF read as LF, so its digest must equal the baseline |
| <a id="case-id-lone-cr-accepted"></a>Lone carriage return | Vector `line-endings-lone-cr` | Identity computation | Accepted | Only the CRLF pair is rewritten, so the digest differs |
| <a id="case-id-double-cr-accepted"></a>Repeated carriage return | Vector `line-endings-double-cr`: `0D 0D 0A` | Identity computation | Accepted | One pass turns it into `0D 0A`, which is not rewritten again, so the digest differs from the baseline |
| <a id="case-id-binary-accepted"></a>Binary keeps CRLF | Vectors `binary-keeps-crlf` and `binary-lf` | Identity computation | Accepted | A file with a zero byte is hashed as stored, so the two digests differ |
| <a id="case-id-invalid-utf8-accepted"></a>Invalid UTF-8 is binary | Vector `invalid-utf8-is-binary` | Identity computation | Accepted | Bytes that are not UTF-8 are hashed as stored |
| <a id="case-id-bom-accepted"></a>Byte order mark | Vector `bom-is-content` | Identity computation | Accepted | A mark is content, so the digest differs |
| <a id="case-id-nfc-nfd-accepted"></a>Contents are not normalised | Vectors `content-nfc` and `content-nfd` | Identity computation | Accepted | Only line endings are normalised, so the two spellings differ |
| <a id="case-id-path-nfc-accepted"></a>Normal-form name | Vector `path-nfc-accepted` | Identity computation | Accepted | A name in form C passes the path tests |
| <a id="case-id-path-nfd-rejected"></a>Decomposed name | Vector `path-nfd-rejected` | Identity computation | Rejected | `invalid-path`: a name not in form C is refused |
| <a id="case-id-case-collision-rejected"></a>Case collision | Vector `path-case-collision` | Identity computation | Rejected | `case-collision`: names equal after case folding are refused |
| <a id="case-id-case-collision-directory-rejected"></a>Directory names collide | Vector `path-case-collision-directory`: `Docs/a.md` and `docs/b.md` | Identity computation | Rejected | `case-collision`: the folders `Docs` and `docs` are two paths equal after folding, though neither is an entry |
| <a id="case-id-case-collision-file-folder-rejected"></a>File beside a folder | Vector `path-case-collision-file-and-directory`: a file `README` and `readme/x.md` | Identity computation | Rejected | `case-collision`: the file `README` and the folder prefix `readme` fold together |
| <a id="case-id-case-distinct-directories-accepted"></a>Different folders, no collision | Vector `path-case-distinct-directories`: `Docs/a.md` and `notes/b.md` | Identity computation | Accepted | No two paths in the set fold together, so a digest exists |
| <a id="case-id-control-rejected"></a>Control character | Vector `path-control-character` | Identity computation | Rejected | `invalid-path`: a control code point is refused |
| <a id="case-id-backslash-rejected"></a>Backslash | Vector `path-backslash` | Identity computation | Rejected | `invalid-path`: a backslash is refused |
| <a id="case-id-dot-dot-rejected"></a>Traversing name | Vector `path-dot-dot-component` | Identity computation | Rejected | `invalid-path`: a parent component is refused and nothing outside the root is read |
| <a id="case-id-name-255-accepted"></a>Longest name | Vector `path-component-255-bytes` | Identity computation | Accepted | 255 bytes is within the limit |
| <a id="case-id-name-256-rejected"></a>Name one byte too long | Vector `path-component-256-bytes` | Identity computation | Rejected | `invalid-path`: 256 bytes is over the limit |
| <a id="case-id-link-inside-accepted"></a>Link inside the course | Vector `symlink-inside` | Identity computation | Accepted | The link is an entry holding its target text and is not followed |
| <a id="case-id-link-escape-accepted"></a>Link out of the course | Vector `symlink-escape` | Identity computation | Accepted | The target text is hashed and the outside file is never read, so it cannot change the digest |
| <a id="case-id-link-followed-rejected"></a>Link followed | A runner follows the link in `symlink-escape` and hashes the outside file | Identity computation | Rejected | A link is never followed, so a change outside the course must not change the digest |
| <a id="case-id-link-dangling-accepted"></a>Link to nothing | Vector `symlink-dangling` | Identity computation | Accepted | A missing target is not an error |
| <a id="case-id-link-loop-accepted"></a>Link to its parent | Vector `symlink-loop` | Identity computation | Accepted | A link is not followed, so no loop can arise |
| <a id="case-id-link-invalid-rejected"></a>Link target not UTF-8 | Vector `symlink-invalid-target` | Identity computation | Rejected | `invalid-link`: the target cannot be written down exactly |
| <a id="case-id-special-file-rejected"></a>Named pipe | Vector `special-file-refused` | Identity computation | Rejected | `special-file`: only files, directories and links are entries |
| <a id="case-id-unreadable-rejected"></a>Unreadable file | Vector `unreadable-file-refused` | Identity computation | Rejected | `unreadable`: a name that cannot be read is never skipped |
| <a id="case-id-git-excluded-accepted"></a>Git metadata | Vector `git-metadata-excluded` | Identity computation | Accepted | Names equal to `.git` are excluded at any depth, so the digest equals the baseline |
| <a id="case-id-platform-excluded-accepted"></a>Platform file | Vector `platform-file-excluded` | Identity computation | Accepted | `.DS_Store` is excluded at any depth |
| <a id="case-id-runner-state-accepted"></a>Runner state | Vector `runner-state-excluded` | Identity computation | Accepted | `.agents` at the root is excluded with everything under it, so learner records never change the identity |
| <a id="case-id-extra-exclusion-rejected"></a>Extra exclusion | A runner also leaves out `assets/` because it looks generated | Identity computation | Rejected | Exactly four exclusions apply, so the digest would differ from the baseline vectors that hold such a folder |
| <a id="case-id-records-hashed-rejected"></a>Learner records hashed | A runner includes `.agents/records/` in a course that holds one, so progress changes the identity | Identity computation | Rejected | The root `.agents` folder is excluded; the digest of `runner-state-excluded` equals the baseline |
| <a id="case-id-site-excluded-accepted"></a>Generated pages | Vector `generated-site-excluded` | Identity computation | Accepted | `_site` at the root is excluded |
| <a id="case-id-root-only-accepted"></a>Exclusions only at the root | Vector `exclusions-apply-only-at-root` | Identity computation | Accepted | `.agents` and `_site` one level down are content, so the digest differs |
| <a id="case-id-missing-entry-rejected"></a>No entry file | Vector `missing-entry-file` | Identity computation | Rejected | `not-a-course`: the root has no `COURSE.md` |
| <a id="case-id-entry-link-rejected"></a>Entry file is a link | Vector `entry-file-is-link` | Identity computation | Rejected | `not-a-course`: only a regular file counts |

## Pin cases <a id="example-pinning"></a>

These cases use the lock entry for `sample-course` version `1.0.0` with the baseline identity. The runner holds the installed folder and the lock.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-pin-resume-accepted"></a>Resume verifies first | The runner recomputes the installed folder's identity, finds the lock's value and teaches | Pin check | Accepted | The identity is verified before teaching |
| <a id="case-pin-edited-refused-accepted"></a>Installed folder edited | A learner edits `lessons/intro.md` in the installed folder; at resume the identity differs; the runner refuses to teach, tells the learner and writes no event | Pin check | Accepted | A difference means the installed folder changed, and the runner refuses |
| <a id="case-pin-edited-taught-rejected"></a>Edited folder is taught | The same edit; the runner teaches from the edited folder | Pin check | Rejected | A runner MUST refuse to teach from a folder whose identity differs from the lock |
| <a id="case-pin-relock-rejected"></a>Silent re-lock | The same edit; the runner writes the new identity into the lock and carries on | Pin check | Rejected | A runner MUST NOT re-lock silently |
| <a id="case-pin-same-name-version-accepted"></a>Different payload refused | A fetch of `sample-course` `1.0.0` has another identity; the runner refuses it and changes nothing | Pin check | Accepted | The same name and version with a different identity is refused |
| <a id="case-pin-replaced-rejected"></a>Payload replaced | The same fetch; the runner replaces the installed folder and the lock entry | Pin check | Rejected | A runner MUST NOT replace a pinned payload on its own |
| <a id="case-pin-same-identity-accepted"></a>Same payload again | A second install of the same bytes has the lock's identity; the runner keeps the existing folder | Pin check | Accepted | An equal identity is not a conflict |
| <a id="case-pin-upgrade-accepted"></a>Explicit upgrade | The learner asks to upgrade to `1.1.0`; the runner takes the new identity into the lock after the learner's request | Pin check | Accepted | A replacement happens only on an explicit request |
| <a id="case-pin-latest-rejected"></a>Latest substituted | The runner finds `1.1.0` online and installs it at resume without being asked | Pin check | Rejected | A runner MUST NOT substitute the latest version on its own |
| <a id="case-pin-git-commit-accepted"></a>Git commit and identity | A Git install records its resolved commit and the identity of the checked-out folder | Pin check | Accepted | A Git reference records both |
| <a id="case-pin-local-no-commit-accepted"></a>Local folder has no commit | A local install records an identity and no commit | Pin check | Accepted | A runner records no commit it did not resolve |
| <a id="case-pin-local-commit-rejected"></a>Invented commit | A local install records a made-up commit beside its identity | Pin check | Rejected | A runner MUST NOT invent a commit |
| <a id="case-pin-line-endings-accepted"></a>Checkout converts line endings | A checkout on a platform that writes CRLF gives the lock's identity | Pin check | Accepted | CRLF is read as LF, so the identity is unchanged |
| <a id="case-pin-filter-refused-accepted"></a>Checkout filter rewrites bytes | A content filter rewrites a lesson on checkout; the identity differs; the runner refuses it as a mismatch | Pin check | Accepted | Bytes other than CRLF that differ change the identity and are refused, not repaired |
| <a id="case-pin-authentic-accepted"></a>Identity is not authenticity | The runner reports the installed bytes match the lock and says nothing about the publisher | Pin check | Accepted | Identity proves the bytes, not the publisher |
| <a id="case-pin-signature-rejected"></a>Identity called a signature | The runner tells the learner the identity is a verified publisher signature | Pin check | Rejected | A runner MUST NOT describe an identity as a signature or a verified publisher |

### Retention cases <a id="retention-cases"></a>

Identity computation and safe source use are distinct judgements. A literal link may hash successfully yet fail when required metadata escapes the retained tree. These cases use complete authored trace trees, because the identity-vector baseline is deliberately not teachable.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-retained-verified"></a>Verified retained folder | [Valid authored source](records.md#case-retained-valid) | Pin check | Accepted | Retained identity and structure both verify before metadata use |
| <a id="case-retained-tamper"></a>Label unchanged, bytes changed | [Tampered call](records.md#case-retained-tamper-call) | Pin check | Rejected | Rehashing refuses changed source before settlement |
| <a id="case-retained-structure"></a>Correct digest, invalid course | [Duplicate call](records.md#case-structure-call) | Pin check | Rejected | A digest cannot establish course validity |
| <a id="case-retained-link"></a>Escaping metadata link | [Metadata link escape](records.md#case-metadata-link-escape) | Pin check | Rejected | Link text hashes, but source use cannot leave included authored content |
| <a id="case-retained-restored"></a>Exact local restoration | [Exact restoration](records.md#case-retained-restore) | Pin check | Accepted | Verify restored bytes and structure; never substitute latest content |
