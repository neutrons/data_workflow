# Per-Instrument Queue Routing (workflow manager)

## What this is

The workflow manager can route completed-run messages to **dedicated
per-instrument queues** instead of the single shared queues, so that one busy
instrument's backlog can no longer block reduction for every other instrument
(the March 2026 blocking incident).

This document covers the **producer side only** — the routing logic in the
workflow manager (`workflow/states.py`). How the autoreducers *consume* these
queues is a separate change in `post_processing_agent`. See "Sequencing" below —
the two must be deployed in order.

## Scope: which queues become per-instrument

| Message handled | Shared queue (flag off) | Per-instrument queue (flag on) |
| --- | --- | --- |
| `POSTPROCESS.DATA_READY` → reduction | `REDUCTION.DATA_READY` | `REDUCTION.<INSTRUMENT>.DATA_READY` |
| `REDUCTION.REQUEST` → reduction | `REDUCTION.DATA_READY` | `REDUCTION.<INSTRUMENT>.DATA_READY` |
| `REDUCTION.COMPLETE` → cataloging | `REDUCTION_CATALOG.DATA_READY` | `REDUCTION_CATALOG.<INSTRUMENT>.DATA_READY` |
| `POSTPROCESS.DATA_READY` → cataloging | `CATALOG.ONCAT.DATA_READY` | `CATALOG.ONCAT.DATA_READY` (**always shared**) |

`<INSTRUMENT>` is the upper-cased instrument name from the message
(`REDUCTION.EQSANS.DATA_READY`, `REDUCTION.CG2.DATA_READY`, ...).

**Cataloging stays on the shared `CATALOG.ONCAT.DATA_READY` queue** — OnCat is a
single external service and does not have the per-instrument fairness problem, so
splitting it buys nothing and would only create orphaned queues.

## Configuration

Routing is controlled by a single environment variable, read by
`workflow/settings.py` at process start:

```
ENABLE_PER_INSTRUMENT_QUEUES=false   # default
```

- **Default is OFF.** Merging this change does **not** alter current behavior.
- Accepted truthy values (case-insensitive): `1`, `true`, `yes`, `on`.
  Anything else (including unset) is treated as OFF.
- It is a single global flag for the whole workflow manager process. Rolling out
  to one environment at a time is done by setting the variable per environment,
  not per instrument.

### How to set it per environment

- **Local Docker Compose:** the `workflow` service passes it through
  (`docker-compose.yml`), defaulting to the value in `.env` (`false`). Override
  for a session:
  ```bash
  ENABLE_PER_INSTRUMENT_QUEUES=true docker compose up workflow
  ```
- **TEST / production:** set `ENABLE_PER_INSTRUMENT_QUEUES` in the deployment
  environment for the workflow manager and restart the process. Settings are
  read once at start, so a restart is required for a change to take effect.

## Behavior details

- **Flag off:** every message goes to the shared queues, exactly as before.
- **Flag on + valid instrument:** reduction / reduction-catalog messages route to
  the instrument-specific queue; an `INFO` line records the decision
  (`Routing eqsans message to per-instrument queue REDUCTION.EQSANS.DATA_READY`).
- **Flag on + missing/invalid instrument:** the message falls back to the shared
  queue and a `WARNING` is logged
  (`Per-instrument routing enabled but no valid instrument in message; falling
  back to shared queue REDUCTION.DATA_READY`). "Invalid" includes non-JSON
  messages, a non-string `instrument`, an empty value, or any value that is not a
  plain alphanumeric token (guards against injecting queue delimiters `.`, STOMP
  path segments `/queue/`, or Artemis wildcard characters `*` / `#`).

## Sequencing — READ BEFORE ENABLING

Routing to per-instrument queues is only safe **while a consumer is listening on
them.** If the flag is turned on while the autoreducers still subscribe only to
`REDUCTION.DATA_READY`, the routed messages pile up in the new queues **with no
consumer** and reduction effectively stops.

Therefore:

> **The consumer-side change (`post_processing_agent`, wildcard/per-instrument
> subscription) MUST be deployed and confirmed subscribed in an environment
> before `ENABLE_PER_INSTRUMENT_QUEUES` is turned on in that environment.**

This producer-side change ships with the flag **off** specifically so it can land
independently and safely ahead of the consumer work.

## Rollout procedure (per environment)

1. **Deploy the workflow manager with this change, flag OFF.** No behavior
   change; verify the pipeline is healthy on the shared queues.
2. **Deploy the consumer-side story** (`post_processing_agent`) so autoreducers
   subscribe to the per-instrument queues (`REDUCTION.*.DATA_READY` /
   `REDUCTION_CATALOG.*.DATA_READY`).
3. **Confirm consumers are subscribed** — check the ActiveMQ console / Jolokia
   that the per-instrument addresses have consumers attached.
4. **Enable the flag:** set `ENABLE_PER_INSTRUMENT_QUEUES=true` for the workflow
   manager and restart it.
5. **Verify:** send/observe a few runs and confirm they appear on
   `REDUCTION.<INSTRUMENT>.DATA_READY` and are drained by the autoreducers.
   Watch that `REDUCTION.DATA_READY` no longer receives new reduction traffic
   (except genuine fallbacks) and that per-instrument depths stay near zero.
6. **Add per-instrument queues to monitoring.** `artemis_data_collector`'s
   `QUEUE_LIST` currently tracks only the shared queues; extend it to include the
   per-instrument queues that are now in use.

## Rollback procedure

Rollback is immediate and low-risk because the flag only affects *future*
message routing:

1. **Set `ENABLE_PER_INSTRUMENT_QUEUES=false`** for the workflow manager and
   restart it. New reduction traffic returns to the shared queues at once.
2. **Drain any in-flight per-instrument queues.** Messages already sitting in
   `REDUCTION.<INSTRUMENT>.DATA_READY` will still be consumed as long as the
   autoreducers remain subscribed to them (leave the consumer subscription in
   place until these are empty).
3. **Delete now-empty per-instrument queues** to avoid leaving orphaned queues
   behind, via the ActiveMQ console or Jolokia `destroyQueue`.

If you must roll back the **consumer** side, disable the producer flag **first**
(step 1) so no new messages are routed to queues that will lose their consumer.

## Validation

- **Unit tests** (routing, queue-name generation, both fallback paths, the
  env-driven flag and its default):
  ```bash
  DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.unittest \
    pixi run -e test python -m pytest \
    src/workflow_app/workflow/tests/test_per_instrument_routing.py -v
  ```
- **Against a running broker** — drives the real handlers through STOMP and
  confirms delivery via the subscribed consumer and Jolokia, for both flag
  states, then deletes the per-instrument queues it created:
  ```bash
  docker compose up -d activemq
  python tests/validate_per_instrument_routing.py
  ```
  (If the broker is only reachable on the Docker network, run the script from a
  container attached to that network — e.g. `docker compose run` on a service
  that has `stomp.py` and the `workflow` package, pointing `BROKER_HOST` at
  `activemq`.)
