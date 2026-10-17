The [investigation report](C:/Users/Abdelrahman/Downloads/ITRU_Core_UI_Boundary_Investigation.txt) has now been read and compared with current source and the proposed design. **No substantive change to the ownership decision or the two queries is required.**

The following addendum supersedes the previous design’s statements that the investigation was unavailable.

## UNAPPROVED DESIGN — reconciliation addendum

The investigation is now the primary design input. It supports:

- Reads through an established Core owner, without independently opening lifecycle storage or triggering recovery.
- Exactly `InspectRun` and `ReadRunJournal` for the first slice.
- Complete Binding and ledger identity matching.
- Core-owned scheduler decisions over the complete scheduling domain.
- Stable Journal high-water traversal with explicit coverage.
- Separate lifecycle and Journal observations, preserving disagreement.
- Content-free recorded summaries without live Result reconstruction or payload recovery.

The report’s proposed roadmap remains evidence for future planning; it provides no implementation authorization.

The UI mapping specification gains these explicit requirements:

| Area                 | Required clarification                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Binding presentation | `configuredRoute` is not canonical Binding data. Omit it or mark it unavailable unless separately supplied by an approved mapping.          |
| Run ordering         | ID-ordered pages must not imply recency. Selecting the final listed Run does not establish “latest Run.”                                    |
| Continuation         | Interrupted or ambiguous history must never appear eligible or available. First-slice eligibility remains unassessed and controls disabled. |
| Integrity badges     | Journal validation does not establish signatures, cryptographic authenticity, or rollback protection.                                       |
| Approval badge       | An unsupported or unavailable approval source must display unavailable, rather than a fabricated zero count.                                |

`ReadRunJournal` retains the proposed full traversal through H before claiming complete absence or subject uniqueness. The investigation permits direct physical-subject lookup; the design’s traversal requirement is a deliberate stricter completeness policy, not a contradiction.

## Updated review and prerequisite status

Separate architecture and safety reviewers approved report-to-design conformance. Their review covered the design packet, supplied final-text excerpts, the complete investigation, and targeted source checks—not executable integration.

**The missing-investigation prerequisite is resolved.** Formal Quality Gate PASS and runtime acceptance are still not claimed.

Remaining prerequisites are:

- Approved source, existing dataset, and metadata audience.
- Human acceptance of unavailable reads when no suitable owner session exists.
- Complete lifecycle mutation and shutdown coordination.
- Journal resource handling and exact operational budgets.
- Future implementation validation and scoped authorization.

Both repository HEADs and the parked branch remain at their supplied baselines. Existing untracked UI work was preserved. No files were changed, operational stores opened, or tests/runtime processes launched.

**The design remains UNAPPROVED. STOP AT HUMAN CONTROL.**
