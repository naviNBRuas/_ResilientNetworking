# _ResilientNetworking

Foundational networking resilience packages for reliability, adaptive control, and fault-tolerant communication.

## Overview

`_ResilientNetworking` is a modular repository of resilience-focused networking components designed for standalone use or composition.

## Packages

- [`adaptive-retry-strategy`](./adaptive-retry-strategy/)
- [`benchmark-lab`](./benchmark-lab/)
- [`chaos-network-simulator`](./chaos-network-simulator/)
- [`config-rollout`](./config-rollout/)
- [`congestion-control`](./congestion-control/)
- [`connection-multiplexer`](./connection-multiplexer/)
- [`crypto-envelope`](./crypto-envelope/)
- [`discovery-health`](./discovery-health/)
- [`idl-contracts`](./idl-contracts/)
- [`observability-policy-hub`](./observability-policy-hub/)
- [`offline-sync-engine`](./offline-sync-engine/)
- [`ordering-dedupe`](./ordering-dedupe/)
- [`protocol-fallback-layer`](./protocol-fallback-layer/)
- [`replay-capture`](./replay-capture/)
- [`sample-consumers`](./sample-consumers/)
- [`session-continuity`](./session-continuity/)
- [`traffic-shaper-qos`](./traffic-shaper-qos/)
- [`transport-adapters-pack`](./transport-adapters-pack/)

## Installation

### Option A: consume the whole repository

```bash
git submodule add https://github.com/navinBRuas/_ResilientNetworking.git vendor/resilient-networking
```

### Option B: install a single package

```bash
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=connection-multiplexer
pip install git+https://github.com/navinBRuas/_ResilientNetworking#subdirectory=adaptive-retry-strategy
```

## Usage

1. Choose the resilience layer(s) you need.
2. Follow package-level `README.md` instructions for setup and runtime behavior.
3. Integrate with explicit contracts and failure-handling semantics.

## Development

- Keep packages decoupled with stable interfaces.
- Run tests and benchmark checks in the package you modify.
- Update package docs/changelog for behavioral changes.

## Governance & docs

- [GOVERNANCE.md](./GOVERNANCE.md)
- [SECURITY.md](./SECURITY.md)
- [SUPPORT.md](./SUPPORT.md)
- [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

## Version

`0.1.0`

## License

See [LICENSE](./LICENSE).
