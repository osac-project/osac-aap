# Technology Stack

**Analysis Date:** 2026-04-27

## Languages

**Primary:**
- Python 3.13+ - All automation code, modules, plugins, filters
- YAML - Playbooks, roles, rulebooks, task definitions, configuration

**Secondary:**
- Jinja2 - Template language embedded in playbooks and roles
- Bash - Integration test scripts, environment setup

## Runtime

**Environment:**
- Python 3.13+ (managed by `uv`)
- Ansible Core 2.20.3
- Ansible 13.4.0

**Package Manager:**
- `uv` - Python dependency management and virtual environment
- `ansible-galaxy` - Ansible collection dependency management
- Lockfile: `uv.lock` (auto-generated from `pyproject.toml`)

**Container Runtime:**
- Execution Environment based on `quay.io/centos/centos:stream9`
- Built with `ansible-builder` tool
- Python 3.12 runtime in container (differs from dev environment)

## Frameworks

**Core:**
- Ansible 13.4.0 - Automation framework
- Ansible Core 2.20.3 - Core automation engine
- Ansible Runner 2.4.3 - Programmatic playbook execution

**Testing:**
- Ginkgo-style integration tests (bash scripts with kind clusters)
- Mock API server (`collections/ansible_collections/osac/service/roles/publish_templates/tests/mock_api_server.py`)
- Kind (Kubernetes in Docker) for test environments

**Build/Dev:**
- `ansible-builder` 3.x - Container image builder for execution environments
- `ansible-lint` 25.2.1+ - Static analysis and linting
- `yamllint` 1.35.1 - YAML validation
- `pre-commit` 5.0.0 - Git hook framework
- `antsibull-changelog` 0.33.0+ - Changelog generation
- `uv` - Fast Python package installer and resolver

## Key Dependencies

**Critical:**
- `kubernetes` 35.0.0 - Kubernetes Python client for custom modules and dynamic inventory
- `ansible-core` 2.20.3 - Required for jinja2_native=True configuration
- `openstacksdk` 4.10.0 - OpenStack cloud integration (indirect via collections)
- `boto3` 1.42.70 / `botocore` 1.42.70 - AWS cloud integration
- `aiobotocore` 3.3.0 - Async AWS operations

**Infrastructure:**
- `python-ironicclient` 6.0.0 - OpenStack Ironic bare metal provisioning
- `python-openstackclient` 9.0.0 - OpenStack CLI and SDK
- `python-esiclient` 1.4 (git) - ESI (Elastic Secure Infrastructure) management
- `python-esileapclient` 1.1.0 - ESI LEAP bare metal leasing
- `esisdk` 1.5.0 - ESI SDK for MOC (Mass Open Cloud)
- `metalsmith` 2.5.0 - Bare metal instance provisioning
- `durationpy` 0.10 - Duration parsing for Kubernetes token expiration
- `dnspython` 2.8.0 - DNS operations
- `pydantic` 2.12.5 - Data validation and settings management
- `jmespath` 1.1.0 - JSON query language

**OpenStack Clients:**
- `python-keystoneclient` 5.8.0 - Identity service
- `python-novaclient` 17.4.0 - Compute service
- `python-cinderclient` 9.9.0 - Block storage service
- `keystoneauth1` 5.13.1 - Authentication library

**Kubernetes CLI Tools (in execution environment):**
- `oc` 4.19 - OpenShift CLI (from `quay.io/openshift/origin-cli:4.19`)
- `kubectl` 4.19 - Kubernetes CLI (from `quay.io/openshift/origin-cli:4.19`)

## Configuration

**Environment:**
- Variables read from environment via `lookup('env', 'VAR_NAME', default=...)`
- Key environment variables:
  - `OSAC_FULFILLMENT_SERVICE_URI` - Fulfillment service API endpoint
  - `AAP_HOSTNAME`, `AAP_USERNAME`, `AAP_PASSWORD` - AAP connection
  - `AAP_INSTANCE_NAME`, `AAP_ORGANIZATION_NAME` - AAP configuration
  - `AAP_PROJECT_GIT_URI`, `AAP_PROJECT_GIT_BRANCH` - Project source
  - `AAP_EE_IMAGE` - Execution environment image
  - `AAP_VALIDATE_CERTS` - TLS verification toggle

**Ansible Configuration (`ansible.cfg`):**
- `jinja2_native=True` - Critical: Enables native Python types in templates
- `collections_path=./vendor:./collections` - Local collections override system
- `collections_scan_sys_path=False` - Ignore system-wide collections
- `become_method=sudo` - Privilege escalation
- `connect_timeout=30`, `command_timeout=30` - Persistent connection settings

**Build:**
- `execution-environment/execution-environment.yaml` - Container build definition
- `pyproject.toml` - Python dependencies (compiled to `requirements.txt`)
- `collections/requirements.yml` - Ansible collection dependencies

## Platform Requirements

**Development:**
- Python 3.13+
- `uv` package manager
- Kind cluster for integration tests
- Git (required for non-versioned git collection dependencies)

**Production:**
- Ansible Automation Platform (AAP) 2.5+
- AAP Event-Driven Ansible (EDA) 2.8.2+
- Kubernetes/OpenShift cluster for hosted clusters
- OpenStack cloud (optional, for OpenStack templates)
- AWS cloud (optional, for AWS templates)
- ESI/MOC infrastructure (optional, for bare metal templates)

**System Dependencies (in execution environment):**
- `systemd-libs`, `systemd-devel` - Systemd integration
- `gcc`, `python3.12-devel` - Build tools for native extensions
- `git-core` - Git for cloning collections
- `bind-utils` - DNS tools
- `krb5-devel` - Kerberos authentication

---

*Stack analysis: 2026-04-27*
