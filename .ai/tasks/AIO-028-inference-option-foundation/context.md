# AIO-028 Context

## Current limitation

AIO has a Provider-neutral Task Execution Mode and can resolve logical Actor
responsibility through Actor Selection and Assignment. It cannot yet represent
the concrete caller/environment-supplied inference access identities available
for later consideration.

External research completed after AIO-026 found that a bare model identifier is
not an adequate operational unit. Provider and hosting surfaces can alter model
locators, access, lifecycle authority, tool surfaces, and runtime behavior. The
stable portable minimum is opaque option, Provider, and Provider-scoped model
identity; volatile availability must remain separate.

## Design lock

The Architect locked two distinct canonical values:

```yaml
option_id: primary-engineer-inference
provider_id: provider-a
model_id: model-x
```

and:

```yaml
option_id: primary-engineer-inference
state: available
```

The Definition is relatively stable identity. The Availability Observation is
ephemeral evidence for one caller-supplied evaluation snapshot. The states are
exactly `available`, `unavailable`, and `unknown`; unknown is not unavailable.

`option_id` is the sole identity within one supplied inventory. Duplicate IDs
invalidate the inventory. A repeated `(provider_id, model_id)` pair is valid
when option IDs differ. All IDs remain opaque, exact, and case-sensitive;
`model_id` is meaningful only within `provider_id`.

Missing observations normalize to `unknown`. Unknown-option observations and
identical or conflicting duplicate observations invalidate the whole snapshot
without partial normalized output. Valid definitions and observations are
sorted by exact option ID only for deterministic canonicalization, never for
preference or ranking.

## Architectural boundaries

Inference Option is distinct from Model, Runtime Option, and Agent Service. It
does not describe tool execution, state, sessions, credentials, endpoints,
capabilities, selection, authorization, or invocation. Availability does not
mean selected, authorized, executable, affordable, within quota, compatible
with Execution Mode, or backed by an available runtime.

The framework owns semantics and validation. The environment owns configured
access reality, and the caller supplies definitions and observations. A future
adapter may translate native facts, but AIO-028 implements no adapter, Provider
API call, discovery, polling, persistence, catalog, or project configuration.

Actor remains `id`, `kind`, and `competencies`; Assignment remains an Actor
responsibility binding; Actor Selection remains logical Actor resolution; and
Execution Mode remains Task-wide process demand. AIO-028 adds no relation among
those contracts and an Inference Option.

## Workflow and Human control

The `architecture-change` Workflow governs this implementation Task. Complexity
is `high` because it introduces two related Sources of Truth, schemas, and
cross-value validation semantics. Risk is `medium` because the foundation will
shape later routing work but remains local, pure, non-authorizing, and
network-free. `deep` is explicitly selected for the required design rigor,
boundary testing, packaging proof, and independent review; it is not inferred
automatically from Complexity or Risk.

An Architect locked the design before implementation. A Software Engineer
implements it, and genuinely separate Reviewer and Architect executions inspect
the completed work. Work stops at the review-stage Human Control checkpoint with
the Task `in_progress`. No commit or AIO-029 is authorized.
