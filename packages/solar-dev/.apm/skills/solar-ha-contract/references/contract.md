# Portable HA contract

This is a concise invariant summary, not deployment configuration. The
[canonical mapping](https://github.com/sujithq/solar-home/blob/main/docs/entity-mapping.md)
owns deployment-specific entities and accepted acquisition evidence.

| Concern | Contract |
| --- | --- |
| Transport | Each consumer independently uses authenticated HA WebSocket; no REST path or automatic HA-mode fallback to hardware or another application's API |
| Reader ownership | HA is the hardware reader; the device remains on HA to avoid direct-reader contention |
| Grid signs | Import/export inputs are nonnegative; signed net power = import - export, positive import and negative export |
| Units | Preserve source unit and explicit conversion; normalize before comparisons; reject unexpected units, signs, and nonfinite values |
| Freshness | Advancing acquisition-associated measurement timestamp plus valid session/sequence where defined; coherent required inputs with bounded age/skew |
| Distinct signals | USB presence, HA connection/authentication, and fresh measurements are separate |
| Invalid input | Explicit unavailable/neutral, not fabricated zero or retained recommendation |
| Reconnect | Invalidate decisions and reacquire eligible inputs; snapshots do not renew measurement time |
| Optional data | Inverter and household values are advisory; never renew grid freshness or physical GO |
| Energy coverage | Partial/as-of totals are not complete local-day energy; disclose timezone, DST, gaps, resets, and first-day limits |
| Demand | Instantaneous power/headroom is not verified tariff quarter-hour demand |

Keep source measurement time, HA state/report times, and monotonic receive time
distinct. `last_changed` records value changes; `last_updated` and `last_reported`
can reflect HA updates or retained reporting rather than successful physical
acquisition. Cached/repeated states, heartbeats, and connection status never
manufacture samples. Unchanged readings require advancing validated acquisition
evidence. Session changes and replay/backward timestamps require the documented
reset/reacquisition procedure, not unconditional sequence acceptance.

Do not pair a separately advancing timestamp event with cached powers and call
that atomic: measurement membership must be established. If only provisional
HA-update evidence is accepted by the existing contract, label it provisional,
never verified physical freshness, and do not upgrade it into physical GO.

Optional household derivation requires validated topology, normalized AC sign,
and coherent fresh inputs; no missing-AC-as-zero or DC substitution. Check whether
grid net already includes an appliance or generation before adding/subtracting it.
Optional failure must not invalidate otherwise independent grid-only behavior.
Preserve existing configurable staleness windows absent evidence and approval.
