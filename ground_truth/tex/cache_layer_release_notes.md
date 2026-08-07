# Cache Layer 4.2 Release Notes

Version 4.2 focuses on eviction correctness and observability. This
release is **backward compatible** with 4.1 configuration files, but the
default eviction policy has changed — read the migration note below.

## Highlights

- Adaptive replacement replaces plain LRU as the default policy.
- Per-key TTLs are now honored to millisecond precision.
- A new `cache.stats()` call exposes hit rate without a debug build.

## Behavior Changes

The eviction default moved from `lru` to `arc`. ARC keeps both a recency
and a frequency list, so a single large scan no longer flushes hot keys.
To keep the old behavior, set `policy = "lru"` explicitly.

## Metrics

The following counters are emitted on every flush interval:

| Metric            | Type    | Meaning                        |
|-------------------|---------|--------------------------------|
| `cache_hits`      | counter | Lookups served from memory     |
| `cache_misses`    | counter | Lookups that fell through      |
| `evicted_entries` | counter | Keys removed under pressure    |
| `resident_bytes`  | gauge   | Current heap held by the cache |

## Migration

Upgrading is a *drop-in* replacement for most users:

1.  Bump the dependency to `4.2` and rebuild.
2.  If you relied on strict LRU ordering, pin `policy = "lru"`.
3.  Delete any custom `warmup_hook` — warmup is now automatic.

Call `cache.compact()` once after startup to reclaim fragmented slabs
left by the previous version.
