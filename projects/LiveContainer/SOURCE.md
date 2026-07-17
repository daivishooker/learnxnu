# Source

Vendored snapshot of https://github.com/LiveContainer/LiveContainer for study inside learnxnu.

| 项 | 值 |
|----|----|
| Upstream commit | `e370a92dfc03ce109ebce00ed4a7cfc64ad1c801` |
| Date | 2026-07-17 15:35:59 +0800 |
| Tip | Update localization & bump version, 3.8.0 |
| License | **AGPL-3.0** (see LICENSE; README also mentions Apache historically) |
| Official docs | https://livecontainer.github.io/docs/intro |
| Learning notes | ../../docs/livecontainer/ |

## Submodules

| Path | Vendored? | Notes |
|------|-----------|-------|
| `litehook/` | yes | hook / symbol rebind; needed to read Dyld/SecItem paths |
| `OpenSSL/` | **no** (stub only) | ~360MB prebuilt frameworks; see `OpenSSL/README.VENDOR.md` |
| `fishhook` | removed upstream | `.gitmodules` may still list it; current tip uses litehook |

Do not redistribute modified network-facing builds without complying with AGPL.
