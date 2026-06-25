# Knowledge CI

Knowledge CI applies software engineering discipline to organizational knowledge.

## Minimum checks

- Frontmatter parses.
- Required fields exist.
- `id` is unique.
- `type` is allowed.
- `status` is allowed.
- `visibility` is allowed.
- Active or verified objects have owners.
- Verified objects have `last_verified`.
- Objects with expired `valid_until` are reported as stale.
- References in `depends_on`, `supersedes`, `superseded_by`, and `conflicts_with` resolve.

## Recommended checks

- Public objects do not cite restricted evidence.
- Metrics define numerator and denominator.
- Runbooks include rollback and escalation sections.
- Datasets include license, lineage, and access metadata.
- Policies define scope and enforcement.
- Decisions include alternatives considered.
- Claims include evidence or are marked as assumptions.

## Example GitHub Actions workflow

See `.github/workflows/knowledge-ci.yml`.
