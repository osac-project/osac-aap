# Codebase Concerns

**Analysis Date:** 2026-04-27

## Tech Debt

**Delete workflow lacks override hooks**
- Issue: `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete.yaml` was refactored to add override points but older template implementations still lack comprehensive override hooks for delete operations
- Files: `tests/integration/TEMPLATE_OVERRIDES.md` (lines 38, 230)
- Impact: Testing and customization is limited for VM deletion workflows; customers cannot override delete steps without modifying template code
- Fix approach: Refactor remaining delete.yaml files to follow the pattern established in create.yaml (7 overrideable steps: pre_delete_hook, validate, resources, post_delete_hook)

**Template-level hook gaps in test coverage**
- Issue: 4 of 14 integration tests fail because noop templates lack the same hook points as real templates (modify_hosted_cluster, modify_nodepool, VM creation hooks)
- Files: `tests/integration/README.md` (lines 43-49)
- Impact: Override mechanism cannot be fully validated in CI; template parity issues may go undetected until runtime
- Fix approach: Add all required hooks to `osac.test_overrides.noop_template` and `osac.test_overrides.test_template` to match real template interfaces

**AAP-dependent tests cannot run in CI**
- Issue: Config-as-code tests require a running Ansible Automation Platform instance with API access
- Files: `tests/integration/README.md` (line 52)
- Impact: 4 tests (config_as_code baseline/override x2) always fail in CI; AAP integration code lacks automated validation
- Fix approach: Mock AAP API calls using ansible-test or create fixtures for controller/hub/eda API responses

**Vendored collection management overhead**
- Issue: Third-party collections are vendored in `vendor/` directory (over 15,000 lines of YAML); requires manual re-vendoring after updates and Red Hat Automation Hub credentials
- Files: `README.md` (lines 29-50), `collections/requirements.yml`
- Impact: Stale dependencies, security vulnerabilities in vendored code, complex onboarding (developers need RH credentials)
- Fix approach: Consider using Ansible Galaxy proxying or container-based dependency management to avoid vendoring; alternatively document security scanning process for vendored collections

**Python module lacks error handling**
- Issue: `client_token.py` module catches `DurationError` but does not validate namespace/service account existence before attempting token creation
- Files: `collections/ansible_collections/osac/service/plugins/modules/client_token.py` (lines 52-102)
- Impact: Fails late with Kubernetes API errors instead of early with clear validation messages
- Fix approach: Add validation checks for namespace and service account existence before calling `create_namespaced_service_account_token`

**No workflow-level error handling or rollback**
- Issue: Workflows lack `rescue:` and `block:` error handling (0 instances found); failed operations leave partial infrastructure
- Files: Across all `collections/ansible_collections/osac/workflows/playbooks/`
- Impact: Failed cluster creation leaves namespaces, leases, finalizers; manual cleanup required
- Fix approach: Wrap critical workflow sections in `block/rescue` with cleanup tasks in rescue section; release leases and remove finalizers on failure

**Lease retry defaults may cause lock contention**
- Issue: Lease acquisition uses `retries: 0` by default, meaning concurrent workflow executions fail immediately rather than waiting
- Files: `collections/ansible_collections/osac/service/roles/lease/tasks/main.yaml` (line 28)
- Impact: Race conditions in multi-tenant environments cause workflow failures; operators must manually configure retries
- Fix approach: Set sensible defaults (e.g., `retries: 10`, `delay: 5`) for lease acquisition to handle typical contention scenarios

## Known Bugs

**ICMP protocol filtering not supported**
- Symptoms: SecurityGroups with ICMP rules allow ALL traffic from source CIDR, not just ICMP
- Files: `collections/ansible_collections/osac/templates/roles/cudn_net/README.md` (lines 72-73)
- Trigger: Create SecurityGroup with protocol="icmp" and source CIDR specification
- Workaround: Document that ICMP filtering requires CNI-specific NetworkPolicy CRDs (e.g., Calico NetworkPolicy) rather than standard Kubernetes NetworkPolicy

**Failed resource cleanup suppresses errors**
- Symptoms: Delete operations use `failed_when: false` patterns, masking actual deletion failures
- Files: `collections/ansible_collections/osac/service/roles/cleanup_stale_network_resources/tasks/cleanup.yaml` (line 8), `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml` (lines 111, 125, 139), `collections/ansible_collections/osac/templates/roles/cudn_net/tasks/delete_subnet.yaml` (lines 33, 53)
- Trigger: Delete resources that are already gone or have dependent resources blocking deletion
- Workaround: Check task results manually in AAP job output; add conditional `failed_when` logic that only ignores "not found" errors

**Cleanup role ignores API failures**
- Symptoms: Stale network resource cleanup ignores ClusterOrder API failures with `failed_when: false`, proceeds with incomplete data
- Files: `collections/ansible_collections/osac/service/roles/cleanup_stale_network_resources/tasks/cleanup.yaml` (line 8)
- Trigger: Run cleanup when ClusterOrder CRD is not installed or namespace does not exist
- Workaround: Ensure CRDs are installed before running cleanup; validate namespace existence in pre-tasks

## Security Considerations

**Password generation uses deprecated lookup**
- Risk: `ansible.builtin.password` lookup with `/dev/null` creates predictable passwords when `seed` parameter is used
- Files: `collections/ansible_collections/osac/config_as_code/roles/aap/defaults/main.yml` (line 3)
- Current mitigation: Used only for AAP EDA service user (internal service-to-service auth)
- Recommendations: Replace with `community.general.random_string` or `ansible.builtin.password` with persistent storage to avoid seed-based generation

**Environment variables for secrets**
- Risk: Secrets passed via environment variables (`AAP_PASSWORD`, `LICENSE_MANIFEST_PATH`) logged in AAP job output or shell history
- Files: `collections/ansible_collections/osac/config_as_code/playbooks/vars/config.yml` (lines 6, 15, 16)
- Current mitigation: AAP marks fields as `secret: true` in credential types
- Recommendations: Use Kubernetes Secrets with volume mounts instead of environment variables; enforce `no_log: true` on tasks using these variables

**No validation of remote cluster kubeconfig source**
- Risk: `remote_cluster_kubeconfig_secret_name` pulled from environment without validation; could reference attacker-controlled secret
- Files: `collections/ansible_collections/osac/config_as_code/playbooks/vars/config.yml` (lines 16-17)
- Current mitigation: Runs in controlled AAP environment with RBAC
- Recommendations: Validate secret namespace and ownership before reading; use service account tokens with limited scope instead of full kubeconfig

**Git collection dependency uses HTTPS (not SSH)**
- Risk: `osac.massopencloud` collection pulled via HTTPS from public GitHub without integrity verification
- Files: `collections/requirements.yml` (lines 22-24)
- Current mitigation: Vendored in repo after initial install
- Recommendations: Use commit hash (`version: commit-sha`) instead of branch/tag to ensure reproducibility; consider migrating to Galaxy or private registry for production

## Performance Bottlenecks

**Cleanup scans all resources in OpenStack**
- Problem: `cleanup_stale_network_resources` lists all networks, floating IPs, routers, and subnets with OpenStack tags, then filters in Ansible
- Files: `collections/ansible_collections/osac/service/roles/cleanup_stale_network_resources/tasks/cleanup.yaml` (lines 23-92)
- Cause: OpenStack API called multiple times without pagination or filtering; relies on tag intersections computed in Ansible loops
- Improvement path: Use OpenStack API filtering to reduce payload size; implement pagination for large environments; add namespace-scoped cleanup option to limit scope

**Lease retries block workflow execution**
- Problem: Lease acquisition retries with `delay: 1` second (configurable) blocks entire workflow; no async lease acquisition
- Files: `collections/ansible_collections/osac/service/roles/lease/tasks/main.yaml` (lines 27-29)
- Cause: Synchronous retry loop waits for lease availability
- Improvement path: Implement exponential backoff; add timeout parameter; consider using Kubernetes events to trigger retry instead of polling

**No parallel resource creation**
- Problem: Templates create resources serially (DataVolumes, VirtualMachine, Services created one after another)
- Files: `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_resources.yaml`
- Cause: Ansible playbook tasks execute sequentially by default
- Improvement path: Use `async` and `poll` parameters for independent resource creation tasks; create DataVolumes and Secrets in parallel

## Fragile Areas

**Workflow variable propagation across roles**
- Files: `collections/ansible_collections/osac/workflows/playbooks/cluster/create.yml`, `collections/ansible_collections/osac/templates/roles/ocp_4_17_small/tasks/install.yaml`
- Why fragile: Variables set in `pre_tasks` must be available in nested `include_role` calls; Ansible variable scoping can cause silent failures if variables not explicitly passed
- Safe modification: Always use `set_fact` in playbooks (not roles) for critical variables; pass variables explicitly to roles via `vars:` section; test with `ansible-playbook --check` to verify variable availability
- Test coverage: Integration tests validate variable extraction but not all override scenarios

**Override mechanism relies on consistent naming**
- Files: All templates in `collections/ansible_collections/osac/templates/roles/*/tasks/`
- Why fragile: Override variables follow pattern `{phase}_{action}_override` but no schema validation; typos silently ignore overrides
- Safe modification: Add validation that checks override variables match expected pattern; use JSON Schema or argument_specs to validate override structure
- Test coverage: Override tests check execution logs but do not validate unused override variables are flagged

**Lease cleanup depends on Pod ownerReference**
- Files: `collections/ansible_collections/osac/service/roles/lease/tasks/main.yaml` (lines 17-21), `tests/integration/run_tests.sh` (lines 14-16)
- Why fragile: Leases use Pod UID as ownerReference for garbage collection; if Pod UID not set or placeholder used, leases persist forever
- Safe modification: Always set `POD_NAMESPACE`, `POD_NAME`, `POD_UID` environment variables; integration tests use placeholder UID (00000000-0000-0000-0000-000000000000) which bypasses K8s GC
- Test coverage: Integration tests explicitly document placeholder UID usage (line 16 of run_tests.sh) but do not test real GC behavior

**Template task file naming must match override expectations**
- Files: `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_*.yaml`
- Why fragile: Overrides reference task files by name (e.g., `tasks_from: create_validate.yaml`); renaming breaks overrides
- Safe modification: Treat task file names as stable API; add deprecation warnings before renaming; create symlinks for backward compatibility
- Test coverage: Baseline tests would catch missing files but override tests may not if noop template lacks same task files

## Scaling Limits

**Single-playbook execution per workflow**
- Current capacity: One workflow execution per AAP job; no parallelization within playbook
- Limit: Large clusters with many subnets/security groups create resources serially; 10 subnets = 10x execution time
- Scaling path: Use AAP workflow templates to parallelize independent resource creation; batch operations in templates (create multiple subnets in single task)

**Kind cluster for integration tests**
- Current capacity: Tests run on single-node kind cluster; limited to ~10 concurrent test executions
- Limit: CI runs tests serially; full suite takes 5-10 minutes
- Scaling path: Parallelize test execution using pytest-xdist or Ansible Tower workflow; use ephemeral clusters per test to enable parallelization

**No pagination in list operations**
- Current capacity: Cleanup operations list all resources in single API call
- Limit: OpenStack/Kubernetes environments with 1000+ resources may hit API timeouts or memory limits
- Scaling path: Implement pagination in `cleanup_stale_network_resources`; use Kubernetes label selectors to reduce payload

## Dependencies at Risk

**python-esiclient using git dependency**
- Risk: Depends on unreleased commit from GitHub (rev: 1.4) instead of PyPI package
- Files: `pyproject.toml` (line 29)
- Impact: Cannot verify integrity; upstream force-push could change code without version bump
- Migration plan: Work with cci-moc/python-esiclient maintainers to publish 1.4 release to PyPI; pin to released version

**ansible.platform collection version pinned to date**
- Risk: `ansible.platform` version `2.5.20250326` appears to be date-based; unclear versioning scheme
- Files: `collections/requirements.yml` (line 13)
- Impact: Difficult to track breaking changes; unclear upgrade path
- Migration plan: Clarify versioning scheme with Red Hat; consider locking to semantic version if available

**Execution environment uses specific OCP CLI version**
- Risk: OpenShift CLI pinned to `quay.io/openshift/origin-cli:4.19`; may not work with older/newer clusters
- Files: `execution-environment/execution-environment.yaml` (line 41)
- Impact: Template compatibility limited to OCP 4.19 clusters; fails on OCP 4.17 or 4.21+ if API changes
- Migration plan: Add version detection logic; allow CLI version override via build argument; test against multiple OCP versions

## Missing Critical Features

**No workflow idempotency for partial failures**
- Problem: Workflows that fail mid-execution cannot be safely re-run; no state tracking for completed steps
- Blocks: Recovery from transient failures (network timeouts, API rate limits, temporary resource unavailability)
- Priority: High - operators must manually clean up and retry

**No observable status for workflow progress**
- Problem: Workflows update ClusterOrder/ComputeInstance status only at completion; no intermediate progress reporting
- Blocks: Operators cannot determine which step failed or estimate completion time
- Priority: Medium - adds operational overhead but workarounds exist (check AAP job logs)

**No dry-run mode for workflows**
- Problem: Cannot preview infrastructure changes before execution; testing requires real resource creation
- Blocks: Safe testing of template modifications; cost estimation for cluster provisioning
- Priority: Medium - integration tests provide some coverage but lack full infrastructure validation

**No resource quota enforcement**
- Problem: Templates do not check tenant quotas before creating resources; workflows fail late when quotas exceeded
- Blocks: Multi-tenant environments with hard resource limits; cost control
- Priority: Low - AAP/Kubernetes admission controllers can enforce quotas externally

**Limited observability for override execution**
- Problem: Override execution logged to `/tmp/osac_test_overrides.log` in tests but no production logging of which overrides were applied
- Blocks: Debugging customer customizations; understanding workflow execution path in production
- Priority: Low - AAP job logs show task execution but override variables not explicitly logged

## Test Coverage Gaps

**Override tests require template parity**
- What's not tested: 4 override tests fail because test templates lack hooks present in real templates
- Files: `tests/integration/targets/cluster_create/tasks/overrides.yml`, `tests/integration/targets/compute_instance_create/tasks/overrides.yml`
- Risk: Real template hook changes may not be reflected in test templates; override mechanism may break silently
- Priority: Medium - baseline tests provide coverage but override mechanism is key differentiator

**No infrastructure integration tests**
- What's not tested: OpenStack/ESI resource creation; actual VM provisioning; bare metal host management
- Files: All `osac.service.cluster_infra` and `osac.service.external_access` roles
- Risk: Breaking changes in OpenStack API or ESI client may not be caught until production deployment
- Priority: High - core functionality has no automated validation

**No multi-tenancy isolation tests**
- What's not tested: SecurityGroup NetworkPolicies across multiple tenant namespaces; lease conflicts between tenants
- Files: `collections/ansible_collections/osac/templates/roles/cudn_net/tasks/create_security_group.yaml`
- Risk: Tenant isolation bugs could allow cross-tenant network access or resource conflicts
- Priority: High - security-critical functionality

**Config-as-code tests require external AAP**
- What's not tested: AAP configuration automation; credential management; project/job template creation
- Files: `collections/ansible_collections/osac/config_as_code/` (entire collection)
- Risk: Breaking changes in AAP API or infra.aap_configuration collection may not be caught
- Priority: Medium - manual testing required for each release

---

*Concerns audit: 2026-04-27*
