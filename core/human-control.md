# AI Engineering Orchestra — Human Control Model

Version: 0.1.0

This document defines how Human authority interacts with AI Agents, Workflows, Quality Gates, approvals, and exceptions.

---

## 1. Purpose

AI Engineering Orchestra is designed to increase engineering autonomy without removing Human control.

The Orchestra may automate:

- analysis
- planning
- implementation
- testing
- review
- documentation
- validation

However, some decisions may remain explicitly protected by Human approval.

---

## 2. Core Principle

Human authority is explicit.

An Agent must never assume that automation implies unlimited permission.

---

## 3. Human Roles

A Human may act as:

- Project Owner
- Technical Lead
- Reviewer
- Approver
- Security Approver
- Release Approver
- Architecture Approver

A project may use one person for multiple Human roles.

---

## 4. Approval Levels

The initial approval levels are:

- none
- review
- explicit
- protected

---

## 5. None

No Human approval is required.

The Agent may continue automatically if all applicable Rules, Policies, and Quality Gates pass.

Example:

- formatting documentation
- updating generated metadata
- running read-only validation

---

## 6. Review

The Agent may complete the work automatically, but a Human review is expected before final integration.

Typical examples:

- normal feature implementation
- medium-impact refactoring
- non-critical UI changes

---

## 7. Explicit

The Workflow must stop until a Human explicitly approves the protected action.

Examples may include:

- merging a high-risk change
- applying a production database migration
- changing authentication behavior
- deploying to production

---

## 8. Protected

A protected action requires an explicitly defined Human approval path and cannot be bypassed by lower-precedence configuration.

Examples may include:

- destructive database operations
- production credential changes
- security Policy exceptions
- irreversible infrastructure operations
- protected Git history rewriting

Full command-level enforcement is introduced in Orchestra v0.2.

---

## 9. Human Approval Is Action-Specific

Approval of one action does not imply approval of all future actions.

Example:

Approving:

"Create the migration."

does not automatically mean:

"Apply the migration to production."

These are separate actions.

---

## 10. Approval Scope

A Human approval should have a defined scope.

Where relevant, approval should identify:

- Task
- action
- environment
- branch
- system
- migration
- exception
- change set

Broad or ambiguous approval should not be silently interpreted as unlimited permission.

---

## 11. Approval Expiration

Approvals should be treated as valid only for the context in which they were given.

If the Task changes materially after approval, the Orchestra may require renewed approval.

Examples:

- implementation scope changes
- migration becomes destructive
- new security impact is discovered
- additional production systems become affected

---

## 12. Human Override

A Human may override normal Orchestra defaults where permitted.

Examples:

- require deeper review
- require additional tests
- force a Task into Deep mode
- reduce Agent parallelism

Protected safety or security constraints cannot be silently weakened unless the applicable Policy explicitly allows such an exception.

---

## 13. Human Escalation

An Agent should escalate when:

- requirements conflict
- a protected action is required
- a critical Quality Gate fails
- applicable Policies conflict
- Risk increases materially
- architecture direction is unclear
- destructive action may be required
- available evidence is insufficient for a safe decision

---

## 14. Avoid Unnecessary Human Interruption

Human control must not become unnecessary friction.

Agents should not request approval for routine work when:

- the action is already permitted,
- the Task scope authorizes it,
- applicable Policies allow it,
- required Quality Gates are satisfied.

The Orchestra should distinguish:

routine autonomy

from

protected decisions.

---

## 15. Human Approval Does Not Replace Validation

Human approval does not automatically override required Quality Gates.

Example:

A Human saying:

"Looks fine."

does not mean:

"Ignore failing tests."

If a Quality Gate is intentionally waived, that waiver must be explicit and permitted by Policy.

---

## 16. Quality Gate Exceptions

A required Quality Gate may only be bypassed when:

1. the applicable Policy permits exceptions,
2. the reason is documented,
3. the required Human approval is obtained.

The Agent must report the Task as completed with an exception rather than pretending the Gate passed.

---

## 17. Architecture Decisions

Material architecture changes should normally require Human approval when configured by the Project.

Examples:

- introducing a new architectural layer
- changing persistence strategy
- changing service boundaries
- adopting a major framework
- replacing a core dependency
- changing public contracts

Minor implementation decisions do not automatically require architecture approval.

---

## 18. Critical Risk

Critical-Risk Tasks should normally require stronger Human involvement.

Possible requirements include:

- architecture approval
- security approval
- independent review
- release approval
- deployment approval

Exact requirements are defined by Project Policy and Workflow.

---

## 19. Human and Reviewer Independence

A Human may serve as the final Reviewer even when AI Reviewers are used.

For high-risk work, the Orchestra may require:

AI implementation
+
independent AI review
+
Human approval

These controls are complementary.

---

## 20. Agent Confidence Is Not Approval

Statements such as:

- "I am confident"
- "This should be safe"
- "The change is straightforward"
- "No issue is expected"

do not replace required Human approval.

---

## 21. Protected Actions

The Orchestra architecture reserves support for protected actions such as:

- Git push
- Git history rewriting
- package publishing
- production deployment
- database migration execution
- infrastructure mutation
- destructive filesystem operations

Full command permission enforcement is planned for Orchestra v0.2.

---

## 22. Approval Records

Important approvals should eventually be traceable.

Future Orchestra versions may record:

- approver
- Task
- action
- timestamp
- reason
- result

The exact audit mechanism is not implemented in v0.1.

---

## 23. Human Control Must Scale

The Orchestra should not require identical Human involvement for every Task.

Example:

Low Risk:
Agent
→ validation
→ completion

Standard Risk:
Agent
→ independent review
→ Human review before merge

Critical Risk:
analysis
→ implementation
→ tests
→ independent review
→ specialist review
→ explicit Human approval

---

## 24. No Silent Escalation of Authority

An Agent must not gain additional authority simply because:

- another Agent assigned the Task,
- a Provider supports autonomous mode,
- a subagent spawned it,
- the Task is taking longer than expected,
- the Agent believes approval would be inconvenient.

Authority comes from applicable Policies and explicit approvals.

---

## 25. Final Authority

The Orchestra coordinates engineering work.

It does not replace Human ownership of the software system.

Where the Project defines Human approval as required, the Human remains the final authority.
