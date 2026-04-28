---
phase: 01
slug: windows-vm-provisioning
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-28
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| ComputeInstance spec -> task variables | User-controlled spec fields (cores, memoryGiB, name, image) cross into Ansible variables | Spec values: integers, strings, resource references |
| Ansible variables -> Kubernetes API | Variables are embedded in K8s resource definitions sent to the API server | VM spec, DataVolume definitions, ConfigMap data |
| ComputeInstance name -> unattend.xml | User-controlled name is injected into XML content via vm_hostname | Hostname string (max 15 chars, K8s DNS subdomain charset) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Tampering | tasks/create.yaml, tasks/delete.yaml | accept | Orchestration files contain no user input processing; all input validation happens in create_validate.yaml. Override dispatch uses Ansible's built-in include_role which validates role existence. | closed |
| T-01-02 | Tampering | create_validate.yaml | mitigate | Regex assertion validates exposed_ports format (line 29). Port range validation enforces 1-65535 (lines 32-40). Hostname truncated to 15 chars via `[:15]` slice (line 19). | closed |
| T-01-03 | Tampering | create_secrets.yaml (unattend.xml) | mitigate | ComputerName value is truncated to 15 chars by create_validate.yaml. Kubernetes metadata.name validation restricts to lowercase alphanumeric + hyphens (DNS subdomain rules), which are safe XML characters. No XML injection possible through this path. | closed |
| T-01-04 | Information Disclosure | create_secrets.yaml (user-data) | accept | User-data secret is copied from ComputeInstance namespace to VM namespace. Both namespaces are under same tenant RBAC scope. Secret data is opaque passthrough — template does not inspect contents. | closed |
| T-01-05 | Denial of Service | create_wait_annotate.yaml | accept | Wait timeout of 900 seconds is a fixed upper bound. If VM never becomes ready, the Ansible task fails cleanly after timeout. No unbounded loops. | closed |
| T-01-06 | Spoofing | computeinstance-windows-test.yaml | accept | Test fixture is a static file used only in integration test environments. The templateID value is hardcoded and not user-controlled in test context. | closed |

*Status: open / closed*
*Disposition: mitigate (implementation required) / accept (documented risk) / transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-01 | Orchestration files are static dispatch wiring with no user input processing; Ansible include_role validates role existence | Phase 1 security audit | 2026-04-28 |
| AR-02 | T-01-04 | User-data secret is opaque passthrough within same tenant RBAC scope; template never inspects secret contents | Phase 1 security audit | 2026-04-28 |
| AR-03 | T-01-05 | 900-second timeout is a fixed upper bound with clean failure semantics; no unbounded resource consumption | Phase 1 security audit | 2026-04-28 |
| AR-04 | T-01-06 | Test fixture contains only hardcoded values for integration test environments; no user-controlled input | Phase 1 security audit | 2026-04-28 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-28 | 6 | 6 | 0 | gsd-secure-phase |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-28
