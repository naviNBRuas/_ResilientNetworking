# Governance & Maintenance

## Contribution Guidelines

### Code Standards
- **Style:** PEP 8 with type hints on all public APIs
- **Testing:** All changes require tests; >90% coverage expected
- **Documentation:** Public APIs must have docstrings with Args/Returns/Raises
- **Logging:** Use structured logging (import logging, create module logger)

### Review Process
1. Fork and create feature branch (`feature/module-name-feature`)
2. Implement with tests and documentation
3. Run: `pytest` and `coverage` to validate
4. Submit PR with clear description of changes
5. Maintainers review for:
   - API consistency with other modules
   - Test coverage adequacy
   - Documentation clarity
   - No breaking changes to stable APIs (version <2.0 only)
6. Merge to `main` and tag for release

### Module Lifecycle

#### Phase: Experimental (v0.x.x)
- API may change without notice
- Use case(s) not yet proven in production
- Useful for prototyping, not recommended for critical systems

#### Phase: Stable (v1.x.x, v2.x.x, ...)
- Public API is locked (breaking changes only on major version bump)
- Well-documented and production-tested
- Recommended for production adoption

#### Phase: Deprecated (end-of-life)
- No new features
- Only critical security/bug fixes
- Clearly marked in documentation
- Recommended migration path provided

## Release Process

### Per-Module Versioning
Modules are released independently. To release a module:

1. Update version in `<module>/pyproject.toml`
2. Update `<module>/CHANGELOG.md` (or create if needed)
3. Commit: `git commit -m "Release <module>/vX.Y.Z"`
4. Tag: `git tag <module>/vX.Y.Z`
5. Push: `git push && git push --tags`

### Maintenance Schedule
- **Security fixes:** Released immediately (hotfix)
- **Bug fixes:** Released weekly or on demand
- **New features:** Released monthly
- **Major releases:** Every 6 months (planning cycle)

## Deprecation Policy

When introducing breaking changes:
1. **Announcement:** Document in CHANGELOG and via issue
2. **Transition Period:** Support both old and new API for at least one major release
3. **Warning:** Add `warnings.warn()` in deprecated code paths
4. **Migration Guide:** Provide clear examples of migration path
5. **Final Removal:** Remove deprecated code in next major version after transition

### Example
```python
import warnings

class RetryPolicy:
    def __init__(self, retry_times=None, *, max_attempts=None):
        if retry_times is not None:
            warnings.warn(
                "retry_times is deprecated, use max_attempts instead",
                DeprecationWarning,
                stacklevel=2
            )
            max_attempts = retry_times
        self.max_attempts = max_attempts or 3
```

## Maintenance Responsibilities

### Core Modules
- **Owner:** Primary maintainer
- **Backup:** Secondary reviewer
- **SLA:** Critical bugs fixed within 48 hours
- **Response Time:** Issues acknowledged within 24 hours

### Extended Modules
- **Owner:** Maintainer or community
- **SLA:** Critical bugs fixed within 1 week
- **Response Time:** Issues acknowledged within 3 days

### Operations Modules
- **Owner:** Maintainer or community
- **SLA:** Best effort
- **Response Time:** Issues acknowledged when capacity permits

## Testing Requirements

### For All Changes
```bash
# Code style
python -m black --check <module>/src <module>/tests

# Type checking
python -m mypy <module>/src

# Tests with coverage
cd <module> && pytest --cov=src --cov-report=term-missing

# Expect >90% coverage for all modules
```

### For Core Modules (before release)
```bash
# Stress test
pytest --stress-iterations=100 <module>/tests

# Performance regression
pytest --benchmark <module>/tests

# Chaos scenarios
pytest --chaos <module>/tests
```

## Documentation Requirements

### Each Module Must Include
- **README.md** — Overview, use cases, getting started
- **ARCHITECTURE.md** or section in main — Design decisions, data flows
- **Examples/** — Runnable code samples
- **API.md** or in docstrings — Complete API reference
- **TROUBLESHOOTING.md** — Common issues and solutions

### Root Documentation
- **README.md** — Project overview and module catalog
- **ARCHITECTURE.md** — System design and patterns
- **GOVERNANCE.md** (this file) — Contribution and release process
- **DEPLOYMENT.md** — Production setup and operations
- **SECURITY.md** — Security best practices

## Dependency Management

### Rules
- **Minimize dependencies:** Each module should have <5 direct deps
- **Core modules:** No external dependencies (stdlib only, except dev deps)
- **Extended modules:** Can use curated deps (e.g., cryptography, jsonschema)
- **Version pinning:** Use loose pinning (e.g., `numpy>=1.20,<2.0`)
- **Security:** Check deps regularly with `safety check` or similar

### Adding a New Dependency
1. Open issue explaining need and security review
2. Discuss in community (pros/cons, alternatives)
3. Minimal changes to add dep
4. Update CHANGELOG
5. PR review includes dep security check

## Community & Communication

### Forums
- **GitHub Issues:** Bug reports, feature requests, design discussions
- **GitHub Discussions:** Architecture questions, best practices
- **Security:** `founder@nbr.company` for vulnerability reports

### Decision Making
- **Consensus:** Aim for community agreement on design changes
- **BDFL:** Principal maintainer breaks ties on major decisions
- **RFC:** Request for Comments process for significant features
  - Create RFC document in `rfc/` directory
  - Community reviews for 2 weeks
  - Maintainer makes final decision

## Roadmap

### Next 6 Months
- [ ] Stable v1.0.0 release of all core modules
- [ ] Comprehensive performance benchmarks and optimization
- [ ] gRPC and OpenAPI schema generation for idl-contracts
- [ ] Observability: OpenTelemetry integration for all modules
- [ ] Security: Formal security audit

### Next 12 Months
- [ ] Language bindings: Go, Rust, Java reference implementations
- [ ] Kubernetes operators for deployment and monitoring
- [ ] Chaos engineering platform integration (Gremlin, Chaos Toolkit)
- [ ] Enterprise support and SLA offerings

## Support

### Community Support
- Free: GitHub issues and discussions
- Expected response time: 1-2 weeks (community dependent)

### Enterprise Support
- **Tier 1:** Development assistance, code review
  - Response time: 24 hours
  - SLA: 95% uptime
- **Tier 2:** Production incident support, emergency patches
  - Response time: 4 hours
  - SLA: 99% uptime
- **Tier 3:** Architecture consulting, custom development
  - Bespoke terms

For enterprise support: contact `founder@nbr.company`
