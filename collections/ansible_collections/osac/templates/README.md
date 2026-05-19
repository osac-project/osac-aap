# OSAC Templates Ansible Collection

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Base templates for OSAC (Open Sovereign AI Cloud) Fulfillment Services solution,
providing automated provisioning of OpenShift clusters and virtual machines on OpenShift
Virtualization.

## Overview

The `osac.templates` collection provides ready-to-use templates for deploying
infrastructure on OpenShift through the OSAC fulfillment service system. Templates are
defined as Ansible roles with metadata that enables self-service provisioning via the
OSAC [fulfillment service](https://github.com/osac-project/fulfillment-service).

## Features

- **Cluster Templates**: Deploy complete OpenShift clusters with customizable configurations
- **VM Templates**: Provision virtual machines on OpenShift Virtualization with cloud-init support

## Installation

This collection is maintained as part of the [osac-aap](https://github.com/osac-project/osac-aap) repository and is automatically available when working within that repository.

### For Development

When working within the osac-aap repository, the collection is automatically available from the `collections/` directory. No installation is required.

### For System-wide Installation

To install the collection system-wide from source:

```bash
git clone https://github.com/osac-project/osac-aap
cd osac-aap/collections/ansible_collections/osac/templates
ansible-galaxy collection build
ansible-galaxy collection install osac-templates-*.tar.gz
```

## Available Templates

### Cluster Templates

#### `ocp_4_17_small`
Minimal OpenShift 4.17 cluster configuration.

**Default Configuration:**
- 2 nodes
- Resource class: fc430
- OpenShift 4.17 release

**Required Parameters:**
- `pull_secret`: Red Hat pull secret for OpenShift installation
- `ssh_public_key`: SSH public key for node access

#### `ocp_4_17_small_github`
OpenShift 4.17 cluster with GitHub OAuth authentication pre-configured.

**Additional Parameters:**
- GitHub OAuth client credentials
- Organization/team membership configuration

### VM Templates

#### `ocp_virt_vm`
Virtual machine template for OpenShift Virtualization: **Linux and Windows** guests use the same template ID. Linux is the default. Windows is selected when any of the following is true (in order): role var `guest_os_family: windows` (e.g. extra vars), annotation `osac.openshift.io/guest-os-family: windows` on the `ComputeInstance`, or `spec.image.sourceRef` contains the substring `containerdisks/windows` (an informal convention in some community Windows disk images — not a Microsoft-official image catalog). **Windows requires** `spec.image.sourceRef` to point at **your** Windows container disk (golden image or registry path you maintain); this template does not ship a default. Windows uses sysprep / CloudBase-Init paths, Hyper-V domain defaults, and matching delete cleanup.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `guest_os_family` | string | `linux` | `linux` or `windows` — overrides inference when set before the role runs |
| `exposed_ports` | string | "22/tcp" (linux) / "3389/tcp" (windows) | Comma-separated ports (e.g., "22/tcp,80/tcp") |

The following are read from the `ComputeInstance` spec:

| Spec Field | Description |
|-----------|-------------|
| `spec.cores` | Number of CPU cores |
| `spec.memoryGiB` | Memory allocation in GiB |
| `spec.bootDisk.sizeGiB` | Root disk size in GiB |
| `spec.image.sourceRef` | Container disk image |
| `spec.runStrategy` | VM run strategy (Always, Halted, etc.) |
| `spec.sshKey` | SSH public key for VM access |
| `spec.userDataSecretRef.name` | Secret containing cloud-init user data |
| `spec.additionalDisks` | Additional data disks |

**Windows-specific behavior** (when guest OS resolves to `windows`): hostname via sysprep unattend.xml (15-character NetBIOS limit), enhanced Hyper-V enlightenments and clock policy, SATA sysprep CD-ROM, optional CloudBase-Init user-data secret, 900s ready wait.

## Usage

Templates are deployed through the OSAC fulfillment service, not directly via
ansible-playbook. The OSAC orchestrator handles template selection, parameter
validation, and lifecycle management.

## Template Development

### Creating a New Cluster Template

1. Create a new role directory under `roles/`:
   ```bash
   mkdir -p roles/my_cluster_template/{tasks,defaults,meta}
   ```

2. Define template metadata in `roles/my_cluster_template/meta/osac.yaml`:
   ```yaml
   title: My Cluster Template
   description: Description of what this template provides
   default_node_request:
   - resourceClass: fc430
     numberOfNodes: 2
   allowed_resource_classes: []
   ```

3. Define parameters in `roles/my_cluster_template/meta/argument_specs.yaml`:
   ```yaml
   argument_specs:
     main:
       options:
         template_parameters:
           type: dict
           options:
             my_param:
               description: Parameter description
               type: str
               required: true
   ```

4. Implement provisioning tasks in `roles/my_cluster_template/tasks/install.yaml`
5. Implement cleanup tasks in `roles/my_cluster_template/tasks/delete.yaml`

### Creating a New ComputeInstance Template

ComputeInstance templates define all metadata, spec defaults, and parameters in a
single file: `meta/osac.yaml`.

1. Create a new role directory under `roles/`:
   ```bash
   mkdir -p roles/my_vm_template/{tasks,meta}
   ```

2. Define template metadata, spec defaults, and parameters in `roles/my_vm_template/meta/osac.yaml`:
   ```yaml
   title: My VM Template
   description: Description of what this template provides
   template_type: compute_instance

   spec_defaults:
     cores: 2
     memory_gib: 2
     boot_disk:
       size_gib: 10
     image:
       source_type: registry
       source_ref: "quay.io/containerdisks/fedora:latest"
     run_strategy: "Always"

   parameters:
     - name: my_param
       title: My Parameter
       description: What this parameter controls
       type: string
       required: false
       default: "some_default"
       validation:
         pattern: '^[a-z]+$'
   ```

3. Implement provisioning tasks in `roles/my_vm_template/tasks/create.yaml`
4. Implement cleanup tasks in `roles/my_vm_template/tasks/delete.yaml`

See roles/ocp_virt_vm for more examples

## Architecture

Templates integrate with OSAC through a well-defined interface:

### Cluster Template Lifecycle
1. OSAC creates a dedicated namespace for the cluster
2. Template receives `cluster_order` and `template_parameters` variables
3. OSAC delegates to template id role for provisioning
4. OSAC monitors cluster status and provides kubeconfig access
5. On deletion, template cleans up all resources

### ComputeInstance Template Lifecycle
1. OSAC creates a dedicated namespace for the ComputeInstance
2. OSAC receives `compute_instance` and `template_parameters` variables
3. OSAC delegeates to template id role for provisioning
4. OSAC assigns floating IP and configures port forwarding
5. On deletion, template removes all resources in order

## Dependencies

### Runtime Dependencies
- `osac.service` collection (for cluster templates)
- `kubernetes.core` collection (for VM templates)
- `osac.esi` collection (for floating IP management)

### Environment Requirements
- OpenShift 4.x cluster with cluster-admin access
- OpenShift Virtualization operator (for VM templates)
- OSAC orchestrator and fulfillment service

## Contributing

Contributions are welcome! Please ensure all templates:
- Include comprehensive `meta/osac.yaml` metadata
- Define parameters in `meta/osac.yaml` (ComputeInstance templates) or `meta/argument_specs.yaml` (cluster templates)
- Implement both create and delete operations
- Follow Ansible best practices
- Include descriptive variable names and comments

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Support

- **Issues**: https://github.com/osac-project/osac-aap/issues
- **Documentation**: https://github.com/osac-project/osac-aap
- **Repository**: https://github.com/osac-project/osac-aap

## Author

Jason Kary <jkary@redhat.com>
