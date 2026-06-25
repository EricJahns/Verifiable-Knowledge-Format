# Security and Permissions

VKF supports both simple visibility and contextual usage restrictions.

## Visibility

Allowed visibility levels:

- `public`: safe for public release.
- `internal`: usable inside the organization.
- `confidential`: limited internal use.
- `restricted`: highly controlled use.
- `private`: individual or sensitive use only.

## Contextual usage

Objects may specify allowed/forbidden uses, and role gating:

```yaml
access:
  allowed_uses:
    - internal_question_answering
    - internal_strategy
  forbidden_uses:
    - public_release
    - model_training
    - customer_visible_response
  allowed_roles: [employee]        # if set, only these roles may use the object
  denied_roles: [contractor]       # these roles may never use it
  requires_review_for:             # allowed, but flagged for human review
    - external_sharing
```

## Resolution order

`vkf check` / `permissions.can_use(metadata, use, role)` decides in this order
(first match wins):

1. **Role denied** — `role` in `denied_roles`, or a non-empty `allowed_roles`
   that doesn't include `role` → **deny**.
2. **Use forbidden** — `use` in `forbidden_uses`, or a non-empty `allowed_uses`
   that doesn't include `use` → **deny**.
3. **Default external-use protection** — if `use` is an external context
   (`public_release`, `external_sharing`, `training_data`) and `visibility` is
   `confidential`, `restricted`, or `private` → **deny by default**, even with no
   explicit `forbidden_uses`. This is the safety net that prevents accidental
   leaks of non-public knowledge.
4. **Requires review** — `use` in `requires_review_for` → **allow, but flagged**
   for human review.
5. Otherwise → **allow**.

## Recommended use contexts

```text
internal_question_answering
internal_strategy
public_release
customer_visible_response
model_training
external_tool_use
legal_review
security_review
academic_publication
```

## Policy recommendation

If an object is `confidential`, `restricted`, or `private`, agents should not
quote it in public output unless a policy explicitly permits that use. The
default external-use protection (step 3 above) enforces this even when an author
forgets to set `forbidden_uses`.

## Checking it

```bash
vkf check examples/datasets/user-events.md --use public_release          # -> DENY
vkf check examples/datasets/user-events.md --use internal_question_answering  # -> ALLOW
```

The same logic backs the server's permission-aware retrieval
(`GET /search?use=...&role=...`), so confidential concepts are filtered out of
results destined for an external context rather than relying on the agent to
self-censor. Note: this is a *cooperative* control for trusted agents and
retrieval pipelines, not a hard access-control boundary — enforce real
authorization at your storage and API layers as well.
