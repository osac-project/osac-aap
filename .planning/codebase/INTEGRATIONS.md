# External Integrations

**Analysis Date:** 2026-04-27

## APIs & External Services

**OSAC Fulfillment Service:**
- REST/HTTP API for template registration and resource management
  - SDK/Client: `ansible.builtin.uri` module
  - Auth: Bearer token from `osac_fulfillment_service_token` variable
  - Base URL: `OSAC_FULFILLMENT_SERVICE_URI` env var (default: `https://fulfillment-api:8000`)
  - Endpoints: `/api/fulfillment/v1/network-classes`, `/api/fulfillment/v1/host-classes`
  - Usage: `collections/ansible_collections/osac/service/roles/publish_templates/tasks/`

**Kubernetes API:**
- Core API and Custom Resource Definitions (CRDs)
  - SDK/Client: `kubernetes` Python library (35.0.0) + `kubernetes.core` collection (5.2.0)
  - Auth: Kubeconfig files, service account tokens
  - Custom module: `osac.service.client_token` (`collections/ansible_collections/osac/service/plugins/modules/client_token.py`)
  - Usage: All workflows, cluster management, network policy enforcement

**OpenStack Cloud:**
- Compute (Nova), Identity (Keystone), Block Storage (Cinder), Ironic (Bare Metal)
  - SDK/Client: `openstacksdk` (4.10.0), `openstack.cloud` collection (2.4.1)
  - Auth: OpenStack credentials (clouds.yaml or environment variables)
  - Usage: Template roles for OpenStack-based implementations

**Amazon Web Services (AWS):**
- EC2, S3, and other AWS services
  - SDK/Client: `boto3` (1.42.70), `botocore` (1.42.70), `aiobotocore` (3.3.0)
  - Collection: `amazon.aws` (9.4.0)
  - Auth: AWS credentials (standard AWS SDK credential chain)
  - Usage: Template roles for AWS-based implementations

**ESI/MOC (Mass Open Cloud):**
- Bare metal provisioning via ESI (Elastic Secure Infrastructure)
  - SDK/Client: `esisdk` (1.5.0), `python-esiclient` (1.4 from git), `python-esileapclient` (1.1.0)
  - Collection: `osac.massopencloud` (git-based third-party collection)
  - Auth: OpenStack Keystone authentication
  - Usage: Bare metal compute instance provisioning
  - Dependencies: `metalsmith` (2.5.0), `python-ironicclient` (6.0.0)

**Ansible Automation Platform (AAP):**
- Controller API for job templates, workflows, inventories
  - Collection: `ansible.controller` (4.6.11)
  - Auth: AAP username/password (`AAP_USERNAME`, `AAP_PASSWORD`)
  - Base URL: `AAP_HOSTNAME` env var
  - Usage: `collections/ansible_collections/osac/config_as_code/` for AAP bootstrap

**Event-Driven Ansible (EDA):**
- Webhook source for event-driven automation
  - Collection: `ansible.eda` (2.8.2)
  - Webhook listener: `0.0.0.0:5000` (configurable)
  - Usage: `rulebooks/cluster_fulfillment.yml` for resource lifecycle events
  - Triggers: Job templates and workflow templates based on webhook endpoints

## Data Storage

**Databases:**
- None directly used by this repository (delegated to fulfillment-service)

**File Storage:**
- Local filesystem for kubeconfig files, templates, test fixtures
- Temporary files via `osac.service` filter plugin `to_temp_file.py`

**Caching:**
- Dogpile cache (1.5.0) - Used by OpenStack SDK for API response caching

## Authentication & Identity

**Auth Providers:**
- Kubernetes Service Account Tokens
  - Implementation: Custom module `osac.service.client_token` with duration-based expiration
  - Usage: Cross-cluster authentication, remote cluster access

- Keystone (OpenStack Identity)
  - Implementation: `keystoneauth1` library (5.13.1)
  - Usage: OpenStack and ESI/MOC authentication

- AWS IAM
  - Implementation: Standard boto3/botocore credential chain
  - Usage: AWS resource provisioning

- AAP Built-in Authentication
  - Implementation: Username/password via `ansible.controller` collection
  - Usage: AAP configuration and job execution

## Monitoring & Observability

**Error Tracking:**
- None configured (logs to AAP job output)

**Logs:**
- Ansible task output (captured by AAP)
- Custom logging via `ansible.builtin.lineinfile` in test override roles (`/tmp/osac_test_overrides.log`)

## CI/CD & Deployment

**Hosting:**
- Ansible Automation Platform (AAP) - Job and workflow execution runtime
- Container registry for execution environment: `ghcr.io/osac-project/osac-aap:latest`

**CI Pipeline:**
- GitHub Actions (implied by `ghcr.io` registry usage)
- Pre-commit hooks for local validation (yamllint, ansible-lint, trailing whitespace, etc.)

**Collection Distribution:**
- Git-based: Collections embedded in repository at `collections/ansible_collections/osac/`
- Third-party: Vendored in `vendor/` directory
- Git dependency: `osac.massopencloud` collection from `https://github.com/osac-project/osac-massopencloud-templates`

## Environment Configuration

**Required env vars:**
- `OSAC_FULFILLMENT_SERVICE_URI` - Fulfillment service API endpoint
- `AAP_HOSTNAME` - AAP instance URL
- `AAP_USERNAME`, `AAP_PASSWORD` - AAP credentials
- `AAP_ORGANIZATION_NAME` - Target AAP organization

**Optional env vars:**
- `AAP_INSTANCE_NAME` - AAP instance name (default: `osac-aap`)
- `AAP_PROJECT_GIT_URI` - Git repo for AAP project (default: `https://github.com/osac-project/osac-aap.git`)
- `AAP_PROJECT_GIT_BRANCH` - Git branch (default: `main`)
- `AAP_PROJECT_ARCHIVE_URI` - Alternative archive-based project source
- `AAP_EE_IMAGE` - Execution environment image (default: `ghcr.io/osac-project/osac-aap:latest`)
- `AAP_PREFIX` - Prefix for AAP resources (default: organization name)
- `AAP_VALIDATE_CERTS` - TLS certificate validation (default: `true`)
- OpenStack credentials (via standard `OS_*` environment variables or `clouds.yaml`)
- AWS credentials (via standard `AWS_*` environment variables or `~/.aws/credentials`)

**Secrets location:**
- Environment variables (managed by AAP credentials system)
- Kubeconfig files (generated dynamically or provided via AAP credentials)
- OpenStack `clouds.yaml` (if using file-based auth)

## Webhooks & Callbacks

**Incoming:**
- Event-Driven Ansible webhook listener at `0.0.0.0:5000`
  - Endpoints: `create-hosted-cluster`, `delete-hosted-cluster`, `create-compute-instance`, `delete-compute-instance`, `create-virtual-network`, `delete-virtual-network`, `create-subnet`, `delete-subnet`, `create-public-ip-pool`, `delete-public-ip-pool`, `create-security-group`, `delete-security-group`
  - Source: `ansible.eda.webhook` plugin
  - Configuration: `rulebooks/cluster_fulfillment.yml`

**Outgoing:**
- HTTP requests to OSAC Fulfillment Service
  - Operations: Template registration (POST, PATCH, GET)
  - Usage: `publish_templates` role for NetworkClass and HostClass registration

## External CRD Dependencies (Kubernetes)

**KubeVirt:**
- VirtualMachine CRD for compute instance provisioning
- CDI (Containerized Data Importer) DataVolume CRD for disk provisioning
- Version: v1.1.0 (KubeVirt), v1.58.0 (CDI)
- Installation: Operator-based deployment (scaled down in test environments)

**Operator Lifecycle Manager (OLM):**
- CRDs for operator management
- Version: v0.25.0
- Usage: Cluster management workflows

**Red Hat Advanced Cluster Management (RHACM):**
- ManagedCluster CRD for multi-cluster management
- Source: `stolostron/managedcluster-import-controller`
- Usage: Hosted cluster management

**OSAC CRDs:**
- ClusterOrder, ComputeInstance, VirtualNetwork, Subnet, SecurityGroup, PublicIPPool
- Source: `osac-operator` repository (`https://github.com/osac-project/osac-operator`)
- Usage: Core resource definitions for all workflows

## Development & Testing Infrastructure

**Kind (Kubernetes in Docker):**
- Test cluster name: `osac-test`
- Usage: Integration test environment (`tests/integration/setup_test_env.sh`)
- Includes: CRD installation, namespace setup, test fixture deployment

**Mock API Server:**
- HTTP server for testing fulfillment service integration
- Implementation: `collections/ansible_collections/osac/service/roles/publish_templates/tests/mock_api_server.py`
- Port: Configurable via `test_mock_port` variable

## Third-Party Ansible Collections

**Infrastructure:**
- `kubernetes.core` 5.2.0 - Kubernetes resource management
- `openstack.cloud` 2.4.1 - OpenStack cloud automation
- `amazon.aws` 9.4.0 - AWS cloud automation
- `community.general` 10.5.0 - General-purpose modules

**AAP Configuration:**
- `ansible.platform` 2.5.20250326 - AAP platform operations
- `ansible.hub` 1.0.0 - Private Automation Hub management
- `ansible.controller` 4.6.11 - AAP Controller configuration
- `ansible.eda` 2.8.2 - Event-Driven Ansible
- `infra.aap_configuration` 4.4.0 - Infrastructure-as-code for AAP

**Utilities:**
- `ansible.utils` 5.1.2 - Network and data utilities

**Custom/Third-Party:**
- `osac.massopencloud` (git) - MOC-specific templates (`https://github.com/osac-project/osac-massopencloud-templates`)

---

*Integration audit: 2026-04-27*
