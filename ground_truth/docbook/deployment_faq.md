# Deployment FAQ

Common questions about rolling the service into production. If your
question is not answered here, check the runbook before paging an
on-call engineer.

## Rollout

**How do I promote a build to production?** Tag the release and let the
pipeline gate it. A promotion is *never* a manual copy — the `promote`
job verifies the artifact checksum first.

**Can I skip the staging environment?** No. Staging runs the same smoke
suite as production and catches roughly a third of config regressions
before they reach users.

## Configuration

Configuration precedence, from highest to lowest, is:

- Command-line flags passed to the process.
- Environment variables prefixed with `APP_`.
- Values in the mounted `config.toml`.
- Built-in defaults compiled into the binary.

A missing required key fails startup **fast** rather than serving with a
bad default.

## Resource Limits

The container ships with conservative defaults you should tune per tier:

| Setting           | Default | When to raise it                |
|-------------------|---------|---------------------------------|
| `max_connections` | `256`   | Sustained connection saturation |
| `worker_threads`  | `4`     | CPU-bound request handlers      |
| `heap_limit_mb`   | `512`   | Frequent out-of-memory restarts |

## Rollback

If a deploy misbehaves, roll back before debugging:

1.  Run `deployctl rollback --to previous` to restore the last good
    build.
2.  Confirm health checks are green on every replica.
3.  Only then open the logs and investigate the failed build offline.

Rolling back is *cheap and reversible*; debugging a live incident is
not.
