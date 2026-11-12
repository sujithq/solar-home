---
name: solar-environment-preflight
description: Read-only Solar checkout isolation, toolchain, authenticated HA WebSocket, and physical-device ownership preflight.
---

Inspect readiness without changing the environment. Record pass, blocked,
not checked, or not applicable with sanitized evidence for each check.
Do not install packages, build, launch services, authenticate interactively,
change HA, open serial devices, flash, stop processes, or alter checkouts.
This procedure and available tools grant no authorization.

1. Identify repository root, checkout/worktree, branch, status, and task scope.
   Confirm it is an isolated task checkout, not the user's primary working copy.
   Never build in or modify the primary working copy. Preserve existing dirty
   work; conflicting changes block implementation rather than justify a reset.
2. Read local repository guidance and manifests. Check required compiler,
   runtime, package manager, and build-tool versions read-only against declared
   requirements. Missing tools are blockers, not permission to install them.
3. If an HA read-only network check is already authorized, use the configured
   endpoint and existing protected credentials for an authenticated WebSocket
   handshake. Require HA `auth_ok`; record transport and auth separately.
   Never print tokens, auth payloads, private URLs, headers, raw state, or
   credential-store contents; keep secrets out of command arguments and logs.
   Use no REST path and no new token creation. Close the socket after the
   bounded check. Otherwise record not checked and the needed approval.
4. An authenticated connection alone proves no measurement freshness. If an
   approved observation is in scope, independently establish advancing
   acquisition timestamps and valid session/sequence under the existing
   contract. Cached snapshots, repeated states, and ping/pong are insufficient.
5. If physical hardware is relevant, rediscover it using read-only OS inventory
   on this run; never assume a prior port or device identity. Identify the
   current owning process using non-invasive OS handle/process inspection
   before anything touches the device. Do not open the port to test ownership,
   probe protocol traffic, kill its owner, or compete with HA's reader.
   Unknown ownership or unavailable inspection means blocked, not free.
   Keep identity/ownership detail local and sanitized; do not save ports,
   serials, hostnames, or profile paths in repository artifacts/comments.
6. Report blockers and the smallest separately authorized next action. A
   completed preflight does not approve builds, installs, live access, or writes.

For any later authorized dependency installation, use only these feed proxies:

| Ecosystem | Feed |
| --- | --- |
| npm | https://packagefeedproxy.microsoft.io/npm/ |
| PyPI | https://packagefeedproxy.microsoft.io/pypi/simple |
| NuGet | https://packagefeedproxy.microsoft.io/nuget/v3/index.json |

Do not fall back silently to public feeds or install merely for preflight.
