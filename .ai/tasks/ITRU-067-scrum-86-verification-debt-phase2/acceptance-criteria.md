# ITRU-067 Phase 2 acceptance criteria

- [x] A01 Verify branch, HEAD, clean entry and unused ITRU-067; preserve ITRU-066.
- [x] A02 Create schema-valid canonical Task records with approved governance.
- [x] A03 Freeze relevant source and historical receipt hashes before test edits.
- [x] A04 Review import/setup safety and reproduce only the selected unchanged
  test failure with exact command, output, exit code and source identity.
- [x] A05 Make exactly the three approved method-local expectation corrections;
  retain equality/order/include-package-data and shared PACKAGED_SCHEMAS.
- [x] A06 Execute exactly the four approved after methods with isolated checkout
  imports; retain interpreter details, commands, raw output and actual results.
- [x] A07 Scoped Task/schema/reference/documentation checks pass and both
  independent test-integrity/security and contract/documentation reviews approve.
- [x] A08 Both documentation_consistency and independent_review Gates pass for
  this implementation handoff without reclassifying historical debt or Option D.
- [x] A09 Report exact changed paths, scope, results and checkpoint readiness;
  leave Task in_progress, unstaged and uncommitted at Human Control.
- [x] H01 Obtain separate Human checkpoint approval before any stage or commit.
- [x] H02 Obtain final Human acceptance and satisfy closure requirements before
  marking the Task completed.

H01 is reconciled from Human authorization #10770 and verified checkpoint
`4db4785916ce721c6769bb43ac9dcfd0519af861`, parent
`4775d649e13639504a8007e57890f80c699bb1be`. A09 records the earlier fulfilled
unstaged/uncommitted handoff; the later authorized checkpoint preserves that
chronology rather than invalidating A09.

Final Human acceptance is APPROVE - October 21, 2026, SCRUM-86 comment #10778.
Fresh closure validation passed and both independent actual-change reviews
APPROVE, with closure documentation_consistency and independent_review PASS.
All 11/11 criteria are now checked after final acceptance and satisfaction of the
closure requirements. Final content/schema and reviewer applicability checks
must bind this completed candidate before the one authorized closure commit.
