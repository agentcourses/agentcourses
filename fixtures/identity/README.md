# Independent identity expectations

The 45 expected outcomes in `examples/identity-vectors/manifest.json` are unchanged.
Their derivation is recorded in `spec/identity.md#vectors`: separate Python and Node implementations, written by one author.
The harness reproduces those fixed values and never updates them from `course_digest`.

`worked.json` copies the public framed bytes and independently checked digest from `spec/identity.md#identity-worked-example`.
The test hashes those literal bytes with `hashlib`, independently of tree enumeration and framing.
Portable listing vectors exercise names that the local filesystem cannot represent faithfully.
Physical vectors exercise links, pipes and permissions. An unavailable facility is reported as `not-run`, never passed.

These are content-identity proofs. They establish neither publisher authenticity nor evidence provenance.
