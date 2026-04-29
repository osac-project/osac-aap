# Phase 1: Windows VM Provisioning - Pattern Map

**Mapped:** 2026-04-28
**Files analyzed:** 17 (new files for `windows_oci_vm` template role + 1 test fixture)
**Analogs found:** 17 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `roles/windows_oci_vm/tasks/create.yaml` | template-orchestrator | request-response | `roles/ocp_virt_vm/tasks/create.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_validate.yaml` | template-task | transform | `roles/ocp_virt_vm/tasks/create_validate.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_build_spec.yaml` | template-task | transform | `roles/ocp_virt_vm/tasks/create_build_spec.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_secrets.yaml` | template-task | CRUD | `roles/ocp_virt_vm/tasks/create_secrets.yaml` | role-match |
| `roles/windows_oci_vm/tasks/create_modify_vm_spec.yaml` | template-hook | transform | `roles/ocp_virt_vm/tasks/create_modify_vm_spec.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_pre_create_hook.yaml` | template-hook | event-driven | `roles/ocp_virt_vm/tasks/create_pre_create_hook.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_resources.yaml` | template-task | CRUD | `roles/ocp_virt_vm/tasks/create_resources.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_post_create_hook.yaml` | template-hook | event-driven | `roles/ocp_virt_vm/tasks/create_post_create_hook.yaml` | exact |
| `roles/windows_oci_vm/tasks/create_wait_annotate.yaml` | template-task | request-response | `roles/ocp_virt_vm/tasks/create_wait_annotate.yaml` | exact |
| `roles/windows_oci_vm/tasks/delete.yaml` | template-orchestrator | request-response | `roles/ocp_virt_vm/tasks/delete.yaml` | exact |
| `roles/windows_oci_vm/tasks/delete_resources.yaml` | template-task | CRUD | `roles/ocp_virt_vm/tasks/delete_resources.yaml` | exact |
| `roles/windows_oci_vm/tasks/delete_pre_delete_hook.yaml` | template-hook | event-driven | `roles/ocp_virt_vm/tasks/delete_pre_delete_hook.yaml` | exact |
| `roles/windows_oci_vm/tasks/delete_post_delete_hook.yaml` | template-hook | event-driven | `roles/ocp_virt_vm/tasks/delete_post_delete_hook.yaml` | exact |
| `roles/windows_oci_vm/defaults/main.yaml` | config | N/A | `roles/ocp_virt_vm/defaults/main.yaml` | exact |
| `roles/windows_oci_vm/meta/argument_specs.yaml` | config | N/A | `roles/ocp_virt_vm/meta/argument_specs.yaml` | exact |
| `roles/windows_oci_vm/meta/osac.yaml` | config | N/A | `roles/ocp_virt_vm/meta/osac.yaml` | exact |
| `tests/integration/fixtures/computeinstance-windows-test.yaml` | test-fixture | N/A | `tests/integration/fixtures/computeinstance-test.yaml` | exact |

**All role paths relative to:** `collections/ansible_collections/osac/templates/`

## Pattern Assignments

### `roles/windows_oci_vm/tasks/create.yaml` (template-orchestrator, request-response)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create.yaml`

This is the main orchestration file. It sets up override defaults, then calls each step in sequence. The new role MUST reference `osac.templates.windows_oci_vm` (not `ocp_virt_vm`) in all step default definitions.

**Header comment pattern** (lines 1-6):
```yaml
# Create flow: each step is overridable via create_step_*_override (default: create_step_*_default).
# Override points: secrets, modify_vm_spec, pre_create_hook, resources, post_create_hook, wait_annotate
# NOT overrideable: validate, build_spec (CRITICAL steps for correct operation)
# Variables: compute_instance, compute_instance_name, tenant_target_namespace,
# template_id, template_parameters, default_arg_specs, default_vm_labels, default_spec.
---
```

**Remote kubeconfig + namespace resolution pattern** (lines 7-19):
```yaml
- name: Include get remote cluster kubeconfig
  ansible.builtin.include_role:
    name: osac.service.common
    tasks_from: get_remote_cluster_kubeconfig

- name: Determine target namespace for VM resources
  ansible.builtin.set_fact:
    compute_instance_target_namespace: "{{ (compute_instance.metadata.annotations | default({})).get('osac.openshift.io/subnet-target-namespace', tenant_target_namespace) }}"

- name: Log namespace selection
  ansible.builtin.debug:
    msg: "VM will be created in namespace: {{ compute_instance_target_namespace }} (tenant namespace: {{ tenant_target_namespace }})"
```

**Override step defaults pattern** (lines 20-39) -- CRITICAL: change all `name:` to `osac.templates.windows_oci_vm`:
```yaml
- name: Set create step defaults
  ansible.builtin.set_fact:
    create_step_secrets_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_secrets.yaml
    create_step_modify_vm_spec_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_modify_vm_spec.yaml
    create_step_pre_create_hook_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_pre_create_hook.yaml
    create_step_resources_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_resources.yaml
    create_step_post_create_hook_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_post_create_hook.yaml
    create_step_wait_annotate_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: create_wait_annotate.yaml
```

**Non-overrideable step call pattern** (lines 41-49):
```yaml
- name: Step - Validate (params, VM config, exposed_ports)
  ansible.builtin.include_role:
    name: osac.templates.ocp_virt_vm
    tasks_from: create_validate.yaml

- name: Build VM template spec base
  ansible.builtin.include_role:
    name: osac.templates.ocp_virt_vm
    tasks_from: create_build_spec.yaml
```

**Overrideable step invocation pattern** (lines 52-54):
```yaml
- name: Step - Create secrets (user-data, SSH) and add to spec
  ansible.builtin.include_role:
    name: "{{ (create_step_secrets_override | default(create_step_secrets_default)).name }}"
    tasks_from: "{{ (create_step_secrets_override | default(create_step_secrets_default)).tasks_from }}"
```

---

### `roles/windows_oci_vm/tasks/create_validate.yaml` (template-task, transform)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_validate.yaml`

Extracts VM configuration from ComputeInstance spec, applies defaults, validates parameters.

**Template parameter merge pattern** (lines 1-4):
```yaml
---
- name: Merge template defaults into template_parameters
  ansible.builtin.set_fact:
    params: "{{ default_arg_specs | combine(template_parameters) }}"
```

**ComputeInstance spec extraction pattern** (lines 6-16). Each spec field uses `compute_instance.spec.X | default(default_spec.X)` with type conversion:
```yaml
- name: Extract VM configuration from ComputeInstance spec
  ansible.builtin.set_fact:
    vm_cpu_cores: "{{ (compute_instance.spec.cores | default(default_spec.cores)) | int }}"
    vm_memory: "{{ (compute_instance.spec.memoryGiB | default(default_spec.memoryGiB)) | string + 'Gi' }}"
    vm_boot_disk_size: "{{ (compute_instance.spec.bootDisk.sizeGiB | default(default_spec.bootDisk.sizeGiB)) | string + 'Gi' }}"
    vm_image_source: "{{ compute_instance.spec.image.sourceRef | default(default_spec.image.sourceRef) }}"
    vm_run_strategy: "{{ compute_instance.spec.runStrategy | default(default_spec.runStrategy) }}"
    vm_ssh_key: "{{ compute_instance.spec.sshKey | default('') }}"
    vm_user_data_secret_ref: "{{ (compute_instance.spec.userDataSecretRef | default({})).name | default('') }}"
    vm_additional_disks: "{{ compute_instance.spec.additionalDisks | default([]) }}"
```

**Assertion pattern** (lines 18-22):
```yaml
- name: Validate exposed_ports format
  ansible.builtin.assert:
    that:
      - params.exposed_ports is match('^([0-9]+/(tcp|udp))(,[0-9]+/(tcp|udp))*$')
    fail_msg: "exposed_ports must be in format 'port/protocol' (e.g., '22/tcp,80/tcp') where protocol is 'tcp' or 'udp'"
```

**Windows changes needed:**
- Change default `exposed_ports` to `"3389/tcp"` (RDP instead of SSH) -- handled via `defaults/main.yaml`
- Add hostname extraction: `vm_hostname: "{{ compute_instance.metadata.name }}"` for sysprep configuration
- `vm_ssh_key` may be kept for compatibility but is typically unused for Windows

---

### `roles/windows_oci_vm/tasks/create_build_spec.yaml` (template-task, transform)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_build_spec.yaml`

This is where the **most significant Windows-specific changes** occur. The full spec structure:

**VM template spec base pattern** (lines 1-36):
```yaml
---
- name: Build template spec base
  ansible.builtin.set_fact:
    vm_template_spec:
      domain:
        cpu:
          cores: "{{ vm_cpu_cores }}"
        memory:
          guest: "{{ vm_memory }}"
        devices:
          disks:
            - name: root-disk
              disk:
                bus: virtio
          interfaces:
            - name: default
              masquerade: {}
          rng: {}
        features:
          smm:
            enabled: true
          acpi: {}
          apic: {}
          hyperv:
            relaxed: {}
            vapic: {}
            spinlocks:
              spinlocks: 8191
      networks:
        - name: default
          pod: {}
      volumes:
        - name: root-disk
          dataVolume:
            name: "{{ compute_instance_name }}-root-disk"
```

**Windows-specific modifications to this spec:**
1. Keep `bus: virtio` for disks (D-01 decision -- virtio-win drivers pre-installed in image)
2. Keep Hyper-V enlightenments as-is (D-03 decision -- relaxed, vapic, spinlocks already present and optimized for Windows)
3. Add `clock` configuration: `clock: { utc: {}, timer: { hpet: { present: false }, hyperv: {} } }`
4. Optionally add `tpm: {}` to devices for Windows 11+
5. Add `synic: {}` to hyperv features (enables Windows synthetic interrupt controller)

**GPU passthrough pattern** (lines 38-47) -- copy as-is, OS-agnostic:
```yaml
- name: Add GPU passthrough device to template spec if required
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(gpu_patch, recursive=True, list_merge='append') }}"
  vars:
    gpu_patch:
      domain:
        devices:
          hostDevices:
            - name: gpu
              deviceName: "{{ gpu_device_name }}"
  when: (gpu_device_name | default('')) | length > 0
```

The `combine(patch, recursive=True, list_merge='append')` pattern is the critical technique for extending the spec incrementally.

---

### `roles/windows_oci_vm/tasks/create_secrets.yaml` (template-task, CRUD)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_secrets.yaml`

Handles user-data secret injection and SSH key propagation. For Windows, the significant change is CloudBase-Init / sysprep instead of cloud-init.

**User-data secret copy pattern** (lines 1-51):
```yaml
---
- name: Copy user-data secret to VM namespace and add cloud-init disk to template spec
  when: vm_user_data_secret_ref | length > 0
  block:
    - name: Read user-data secret from ComputeInstance namespace
      kubernetes.core.k8s_info:
        api_version: v1
        kind: Secret
        name: "{{ vm_user_data_secret_ref }}"
        namespace: "{{ compute_instance.metadata.namespace }}"
      register: user_data_secret

    - name: Fail if user-data secret not found
      ansible.builtin.assert:
        that:
          - user_data_secret.resources | length > 0
        fail_msg: >-
          Secret '{{ vm_user_data_secret_ref }}' not found in namespace
          '{{ compute_instance.metadata.namespace }}'

    - name: Create user-data secret in VM namespace
      kubernetes.core.k8s:
        kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
        state: present
        definition:
          apiVersion: v1
          kind: Secret
          metadata:
            name: "{{ compute_instance_name }}-user-data"
            namespace: "{{ compute_instance_target_namespace }}"
            labels: "{{ default_vm_labels }}"
          type: Opaque
          data: "{{ user_data_secret.resources[0].data }}"

    - name: Add cloud-init disk to template spec
      ansible.builtin.set_fact:
        vm_template_spec: "{{ vm_template_spec | combine(cloud_init_patch, recursive=True, list_merge='append') }}"
      vars:
        cloud_init_patch:
          domain:
            devices:
              disks:
                - name: cloud-init-disk
                  disk:
                    bus: virtio
                  serial: cloud-init
          volumes:
            - name: cloud-init-disk
              cloudInitNoCloud:
                secretRef:
                  name: "{{ compute_instance_name }}-user-data"
```

**Minimal cloud-init disk pattern** (lines 53-71):
```yaml
- name: Add minimal cloud-init disk for SSH key propagation
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(cloud_init_patch, recursive=True, list_merge='append') }}"
  vars:
    cloud_init_patch:
      domain:
        devices:
          disks:
            - name: cloud-init-disk
              disk:
                bus: virtio
              serial: cloud-init
      volumes:
        - name: cloud-init-disk
          cloudInitNoCloud:
            userData: "#cloud-config"
  when:
    - vm_ssh_key | length > 0
    - vm_user_data_secret_ref | length == 0
```

**SSH key secret + accessCredentials pattern** (lines 73-103):
```yaml
- name: Create ssh public key secret and add accessCredentials to template spec
  when: vm_ssh_key | length > 0
  block:
    - name: Create Secret resource containing ssh public key
      kubernetes.core.k8s:
        kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
        state: present
        definition:
          apiVersion: v1
          kind: Secret
          metadata:
            name: "{{ compute_instance_name }}-ssh-public-key"
            namespace: "{{ compute_instance_target_namespace }}"
            labels: "{{ default_vm_labels }}"
          data:
            ssh-public-key: "{{ vm_ssh_key | b64encode }}"
          type: Opaque

    - name: Add accessCredentials to template spec
      ansible.builtin.set_fact:
        vm_template_spec: "{{ vm_template_spec | combine(ssh_public_key_patch, recursive=True, list_merge='append') }}"
      vars:
        ssh_public_key_patch:
          accessCredentials:
            - sshPublicKey:
                source:
                  secret:
                    secretName: "{{ compute_instance_name }}-ssh-public-key"
                propagationMethod:
                  noCloud: {}
```

**Windows changes needed:**
1. Replace `cloudInitNoCloud` with CloudBase-Init compatible delivery. CloudBase-Init can consume `cloudInitNoCloud` with cloud-config YAML (D-02 decision), so the volume type may remain the same.
2. Add sysprep unattend.xml for hostname configuration (D-04 decision). Create a ConfigMap or Secret with minimal unattend.xml containing `<ComputerName>{{ vm_hostname }}</ComputerName>`, then mount as a `sysprep` volume or embed in CloudBase-Init user-data.
3. SSH key section likely omitted for Windows (RDP is primary access). Keep the user-data secret copy pattern for CloudBase-Init cloud-config.

---

### `roles/windows_oci_vm/tasks/create_resources.yaml` (template-task, CRUD)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_resources.yaml`

Creates DataVolume and VirtualMachine CRs. Handles storage class, additional disks, and restart logic.

**Storage class assertion pattern** (lines 1-15):
```yaml
---
- name: Require non-empty tenant StorageClass
  ansible.builtin.assert:
    that: tenant_storage_class_name | length > 0
    fail_msg: >-
      ComputeInstance provisioning requires a StorageClass for the tenant.
      tenant_storage_class_name is set but empty.
    success_msg: "Using tenant StorageClass: {{ tenant_storage_class_name }}"

- name: Set storage_class from tenant StorageClass
  ansible.builtin.set_fact:
    storage_class: "{{ tenant_storage_class_name }}"

- name: Using tenant storage_class
  ansible.builtin.debug:
    var: storage_class
```

**DataVolume creation pattern** (lines 18-40):
```yaml
- name: Create DataVolume for VM root disk
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    apply: true
    definition:
      apiVersion: cdi.kubevirt.io/v1beta1
      kind: DataVolume
      metadata:
        name: "{{ compute_instance_name }}-root-disk"
        labels: "{{ default_vm_labels }}"
        namespace: "{{ compute_instance_target_namespace }}"
      spec:
        source:
          registry:
            url: "docker://{{ vm_image_source }}"
        pvc:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: "{{ vm_boot_disk_size }}"
          storageClassName: "{{ storage_class }}"
    state: present
```

**Additional disks pattern** (lines 42-87):
```yaml
- name: Create DataVolumes for additional disks
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    apply: true
    definition:
      apiVersion: cdi.kubevirt.io/v1beta1
      kind: DataVolume
      metadata:
        name: "{{ compute_instance_name }}-disk-{{ idx + 1 }}"
        labels: "{{ default_vm_labels }}"
        namespace: "{{ compute_instance_target_namespace }}"
      spec:
        source:
          blank: {}
        pvc:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: "{{ item.sizeGiB }}Gi"
          storageClassName: "{{ storage_class }}"
    state: present
  loop: "{{ vm_additional_disks }}"
  loop_control:
    index_var: idx
  when: vm_additional_disks | length > 0

- name: Add additional disks to template spec
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(additional_disk_patch, recursive=True, list_merge='append') }}"
  vars:
    additional_disk_patch:
      domain:
        devices:
          disks:
            - name: "additional-disk-{{ idx + 1 }}"
              disk:
                bus: virtio
      volumes:
        - name: "additional-disk-{{ idx + 1 }}"
          dataVolume:
            name: "{{ compute_instance_name }}-disk-{{ idx + 1 }}"
  loop: "{{ vm_additional_disks }}"
  loop_control:
    index_var: idx
  when: vm_additional_disks | length > 0
```

**VirtualMachine creation pattern** (lines 89-106):
```yaml
- name: Create VirtualMachine
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    apply: true
    definition:
      apiVersion: kubevirt.io/v1
      kind: VirtualMachine
      metadata:
        name: "{{ compute_instance_name }}"
        namespace: "{{ compute_instance_target_namespace }}"
        labels: "{{ default_vm_labels }}"
      spec:
        runStrategy: "{{ vm_run_strategy }}"
        template:
          metadata:
            labels: "{{ default_vm_labels }}"
          spec: "{{ vm_template_spec }}"
    state: present
```

**Restart check pattern** (lines 108-144):
```yaml
- name: Check if restart is requested
  ansible.builtin.set_fact:
    restart_requested: >-
      {{
        (compute_instance.spec.restartRequestedAt | default('') | string | length > 0)
        and
        (
          (compute_instance.status.lastRestartedAt | default('') | string | length == 0)
          or
          (compute_instance.spec.restartRequestedAt | string > compute_instance.status.lastRestartedAt | default('1970-01-01T00:00:00Z') | string)
        )
      }}

- name: Delete VirtualMachineInstance to trigger restart
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachineInstance
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  when: restart_requested | bool

- name: Wait for VMI to be recreated after restart
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachineInstance
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
  register: vmi_info
  until:
    - vmi_info.resources | length > 0
    - vmi_info.resources[0].metadata.creationTimestamp | string > compute_instance.spec.restartRequestedAt | string
  retries: 60
  delay: 5
  when: restart_requested | bool
```

**Windows delta:** This file can be reused with minimal or no changes. All resource creation is OS-agnostic; Windows config is embedded in `vm_template_spec` by prior steps.

---

### `roles/windows_oci_vm/tasks/create_wait_annotate.yaml` (template-task, request-response)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_wait_annotate.yaml`

**Wait for VM ready pattern** (lines 1-18):
```yaml
---
- name: Show VM Namespace and VM Name
  ansible.builtin.debug:
    msg: "Namespace {{ compute_instance_target_namespace }} - Name: {{ compute_instance_name }}"

- name: Wait for VM to be ready
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    wait: true
    wait_condition:
      type: Ready
      status: "True"
    wait_timeout: 600
  when: vm_run_strategy != "Halted"
```

**Annotate reconciled version pattern** (lines 20-30):
```yaml
- name: Annotate the reconciledConfigVerion
  kubernetes.core.k8s:
    api_version: osac.openshift.io/v1alpha1
    kind: ComputeInstance
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance.metadata.namespace }}"
    state: present
    definition:
      metadata:
        annotations:
          osac.openshift.io/reconciled-config-version: "{{ compute_instance.status.desiredConfigVersion | default('unknown') }}"
```

**Display VM info pattern** (lines 32-52):
```yaml
- name: Get VM status
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
  register: vm_status

- name: Display VM information
  ansible.builtin.debug:
    msg:
      - "Virtual Machine '{{ compute_instance_name }}' created successfully"
      - "Namespace: {{ compute_instance_target_namespace }}"
      - "Image: {{ vm_image_source }}"
      - "CPU Cores: {{ vm_cpu_cores }}/Memory: {{ vm_memory }}"
      - "Root Disk Size: {{ vm_boot_disk_size }}"
      - "Additional Disks: {{ vm_additional_disks | length }}"
      - "RunStrategy: {{ vm_run_strategy }}"
      - "Status: {{ vm_status.resources[0].status.printableStatus | default('Unknown') }}"
```

**Windows changes:** Increase `wait_timeout` from 600 to 900+ (Windows boots slower). Add `"OS: Windows"` to display message.

---

### `roles/windows_oci_vm/tasks/create_modify_vm_spec.yaml` (template-hook, transform)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/create_modify_vm_spec.yaml`

**No-op hook pattern** (entire file, 4 lines):
```yaml
---
- name: Modify VM spec (no-op by default; override step to customize vm_template_spec)
  ansible.builtin.debug:
    msg: "Modify VM spec step (no-op). Override create_step_modify_vm_spec_override to customize."
```

Copy verbatim. All four hook files (`create_pre_create_hook`, `create_post_create_hook`, `delete_pre_delete_hook`, `delete_post_delete_hook`) follow this exact same pattern -- a single `debug` task documenting the override variable name.

---

### `roles/windows_oci_vm/tasks/create_pre_create_hook.yaml` (template-hook, event-driven)

**Analog:** `ocp_virt_vm/tasks/create_pre_create_hook.yaml` -- copy as-is:
```yaml
---
- name: Pre-create hook (no-op by default; override step to run custom logic before resources)
  ansible.builtin.debug:
    msg: "Pre-create hook step (no-op). Override create_step_pre_create_hook_override to run custom logic."
```

---

### `roles/windows_oci_vm/tasks/create_post_create_hook.yaml` (template-hook, event-driven)

**Analog:** `ocp_virt_vm/tasks/create_post_create_hook.yaml` -- copy as-is:
```yaml
---
- name: Post-create hook (no-op by default; override step to run custom logic after resources)
  ansible.builtin.debug:
    msg: "Post-create hook step (no-op). Override create_step_post_create_hook_override to run custom logic."
```

---

### `roles/windows_oci_vm/tasks/delete.yaml` (template-orchestrator, request-response)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete.yaml`

**Full pattern** (lines 1-45). CRITICAL: change all `name: osac.templates.ocp_virt_vm` to `name: osac.templates.windows_oci_vm`:

```yaml
# Delete flow: each step is overridable via delete_step_*_override (default: delete_step_*_default).
# Override points: pre_delete_hook, resources, post_delete_hook
# Variables: compute_instance, compute_instance_name, tenant_target_namespace,
# template_id, compute_instance_target_namespace.
---
- name: Include get remote cluster kubeconfig
  ansible.builtin.include_role:
    name: osac.service.common
    tasks_from: get_remote_cluster_kubeconfig

- name: Determine target namespace for VM resources
  ansible.builtin.set_fact:
    compute_instance_target_namespace: "{{ (compute_instance.metadata.annotations | default({})).get('osac.openshift.io/subnet-target-namespace', tenant_target_namespace) }}"

- name: Log namespace selection
  ansible.builtin.debug:
    msg: "VM will be deleted from namespace: {{ compute_instance_target_namespace }} (tenant namespace: {{ tenant_target_namespace }})"

- name: Set delete step defaults
  ansible.builtin.set_fact:
    delete_step_pre_delete_hook_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: delete_pre_delete_hook.yaml
    delete_step_resources_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: delete_resources.yaml
    delete_step_post_delete_hook_default:
      name: osac.templates.ocp_virt_vm
      tasks_from: delete_post_delete_hook.yaml

- name: Step - Pre-delete hook (no-op by default)
  ansible.builtin.include_role:
    name: "{{ (delete_step_pre_delete_hook_override | default(delete_step_pre_delete_hook_default)).name }}"
    tasks_from: "{{ (delete_step_pre_delete_hook_override | default(delete_step_pre_delete_hook_default)).tasks_from }}"

- name: Step - Delete resources (VirtualMachine, DataVolumes, Secrets)
  ansible.builtin.include_role:
    name: "{{ (delete_step_resources_override | default(delete_step_resources_default)).name }}"
    tasks_from: "{{ (delete_step_resources_override | default(delete_step_resources_default)).tasks_from }}"

- name: Step - Post-delete hook (no-op by default)
  ansible.builtin.include_role:
    name: "{{ (delete_step_post_delete_hook_override | default(delete_step_post_delete_hook_default)).name }}"
    tasks_from: "{{ (delete_step_post_delete_hook_override | default(delete_step_post_delete_hook_default)).tasks_from }}"
```

---

### `roles/windows_oci_vm/tasks/delete_resources.yaml` (template-task, CRUD)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/tasks/delete_resources.yaml`

**VM info lookup + existence check** (lines 1-18):
```yaml
---
- name: Get VirtualMachine info for floating IP cleanup
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
  register: vm_info

- name: Check if VM instance exists
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachineInstance
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
  register: vm_exists
```

**Graceful VM shutdown pattern** (lines 20-45):
```yaml
- name: Stop VirtualMachine
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    state: present
    definition:
      spec:
        runStrategy: Halted
  when: vm_exists.resources | length > 0

- name: Wait for VM to stop
  kubernetes.core.k8s_info:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    wait: true
    wait_condition:
      type: Ready
      status: "False"
    wait_timeout: 300
  when: vm_exists.resources | length > 0
```

**Resource deletion cascade** (lines 47-91) -- VM, load balancer service, root disk, additional disks:
```yaml
- name: Delete VirtualMachine
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: kubevirt.io/v1
    kind: VirtualMachine
    name: "{{ compute_instance_name }}"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
    wait: true
    wait_timeout: 300
```

**Safe secret deletion pattern** (lines 93-134) -- handles "not found" gracefully:
```yaml
- name: Delete user-data secret
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: v1
    kind: Secret
    name: "{{ compute_instance_name }}-user-data"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  register: delete_user_data_secret
  failed_when:
    - delete_user_data_secret.failed is defined
    - delete_user_data_secret.failed
    - "'not found' not in (delete_user_data_secret.msg | default(''))"
```

**Windows delta:** Additionally clean up any sysprep ConfigMap/Secret (e.g., `{{ compute_instance_name }}-sysprep`). Use the same `failed_when` soft-fail pattern.

---

### `roles/windows_oci_vm/tasks/delete_pre_delete_hook.yaml` and `delete_post_delete_hook.yaml` (template-hook)

**Analog:** Identical no-op hook files from `ocp_virt_vm`. Copy as-is.

```yaml
---
- name: Pre-delete hook (no-op by default; override step to run custom logic before resources)
  ansible.builtin.debug:
    msg: "Pre-delete hook step (no-op). Override delete_step_pre_delete_hook_override to run custom logic."
```

---

### `roles/windows_oci_vm/defaults/main.yaml` (config)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/defaults/main.yaml`

**Full pattern** (lines 1-19):
```yaml
---
default_vm_internal_network: "hypershift"
default_vm_storage_class: "nfs-client"
default_vm_labels: "{{ {compute_instance_label: compute_instance_name} }}"

# Setup the defaults described in the arg_specs.
default_arg_specs:
  exposed_ports: "22/tcp"

# Defaults for ComputeInstance spec fields.
default_spec:
  cores: 2
  memoryGiB: 2
  bootDisk:
    sizeGiB: 10
  image:
    sourceRef: "quay.io/containerdisks/fedora:latest"
  runStrategy: "Always"
```

**Windows version changes:**
- `exposed_ports`: `"3389/tcp"` (RDP instead of SSH)
- `default_spec.cores`: `2` (keep as minimum for Windows)
- `default_spec.memoryGiB`: `4` (Windows requires more RAM)
- `default_spec.bootDisk.sizeGiB`: `40` (Windows images are significantly larger)
- `default_spec.image.sourceRef`: a Windows OCI image reference (project-specific registry path)

---

### `roles/windows_oci_vm/meta/argument_specs.yaml` (config)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/argument_specs.yaml`

**Full pattern** (lines 1-45):
```yaml
argument_specs:
  main:
    options:
      compute_instance:
        type: dict
        required: true
        description: ComputeInstance configuration
      gpu_device_name:
        type: str
        required: false
        default: ""
        description: |
          The resource name of the GPU device to pass through to the virtual machine...
      template_parameters:
        type: dict
        description: VM configuration parameters
        options:
          exposed_ports:
            description: >
              Ports to expose on the VM for ingress traffic.
              The syntax is a comma-separated list of `<port>/<protocol>` pairs...
            type: str
            required: false
            default: "22/tcp"
```

**Windows changes:** Change `exposed_ports` default to `"3389/tcp"`. Update descriptions to reference Windows/RDP. Keep `gpu_device_name` (GPU passthrough is OS-agnostic).

---

### `roles/windows_oci_vm/meta/osac.yaml` (config)

**Analog:** `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/meta/osac.yaml`

**Full pattern** (lines 1-7):
```yaml
# Define the display name and description of the template
title: Simple ComputeInstance Template
description: >
  Simple ComputeInstance

# Specify this is a ComputeInstance template (not a cluster template)
template_type: compute_instance
```

**Windows version:**
```yaml
title: Windows OCI VM ComputeInstance Template
description: >
  Provisions Windows virtual machines from OCI container images
  with CloudBase-Init configuration and Hyper-V enlightenments.

template_type: compute_instance
```

The `template_type: compute_instance` field is critical -- it enables template discovery by `osac.service.enumerate_templates`.

---

### `tests/integration/fixtures/computeinstance-windows-test.yaml` (test-fixture)

**Analog:** `tests/integration/fixtures/computeinstance-test.yaml`

**Full pattern** (lines 1-18):
```yaml
---
apiVersion: osac.openshift.io/v1alpha1
kind: ComputeInstance
metadata:
  name: test-vm
  namespace: osac-system
spec:
  templateID: osac.templates.ocp_virt_vm
  cores: 2
  memoryGiB: 4
  bootDisk:
    sizeGiB: 20
  image:
    sourceType: registry
    sourceRef: "quay.io/containerdisks/fedora:latest"
  runStrategy: "Always"
status:
  desiredConfigVersion: "1"
```

**Windows version:**
- Change `templateID` to `osac.templates.windows_oci_vm`
- Change `metadata.name` to `test-windows-vm`
- Increase `memoryGiB` to `4`
- Increase `bootDisk.sizeGiB` to `40`
- Change `image.sourceRef` to a Windows OCI image

---

## Shared Patterns

### Remote Kubeconfig Access
**Source:** `collections/ansible_collections/osac/service/roles/common/tasks/get_remote_cluster_kubeconfig.yaml` (lines 1-6)
**Apply to:** `create.yaml`, `delete.yaml` (first step in both flows)
```yaml
- name: Get remote cluster kubeconfig
  ansible.builtin.set_fact:
    remote_cluster_kubeconfig: >-
      {{ lookup('env', 'OSAC_REMOTE_CLUSTER_KUBECONFIG') }}
  when: lookup('env', 'OSAC_REMOTE_CLUSTER_KUBECONFIG') | length > 0
```

### Namespace Resolution
**Source:** `ocp_virt_vm/tasks/create.yaml` (lines 12-14)
**Apply to:** `create.yaml`, `delete.yaml`
```yaml
- name: Determine target namespace for VM resources
  ansible.builtin.set_fact:
    compute_instance_target_namespace: "{{ (compute_instance.metadata.annotations | default({})).get('osac.openshift.io/subnet-target-namespace', tenant_target_namespace) }}"
```

### Override Pattern
**Source:** `ocp_virt_vm/tasks/create.yaml` (lines 20-54)
**Apply to:** All overrideable steps in `create.yaml` (6 steps) and `delete.yaml` (3 steps)
```yaml
# Define default with FQCN pointing to THIS role
create_step_{name}_default:
  name: osac.templates.windows_oci_vm
  tasks_from: create_{name}.yaml

# Invoke with override fallback
- name: Step - {Description}
  ansible.builtin.include_role:
    name: "{{ (create_step_{name}_override | default(create_step_{name}_default)).name }}"
    tasks_from: "{{ (create_step_{name}_override | default(create_step_{name}_default)).tasks_from }}"
```

### Kubernetes Resource Creation
**Source:** `ocp_virt_vm/tasks/create_resources.yaml` (lines 18-40, 89-106)
**Apply to:** `create_resources.yaml`, `create_secrets.yaml`
```yaml
- name: Create {ResourceKind}
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    apply: true
    definition:
      apiVersion: {api_version}
      kind: {Kind}
      metadata:
        name: "{{ compute_instance_name }}-{suffix}"
        labels: "{{ default_vm_labels }}"
        namespace: "{{ compute_instance_target_namespace }}"
      spec: {spec}
    state: present
```

### VM Spec Extension via Combine
**Source:** `ocp_virt_vm/tasks/create_build_spec.yaml` (lines 38-47), `create_secrets.yaml` (lines 35-51), `create_resources.yaml` (lines 69-87)
**Apply to:** `create_build_spec.yaml`, `create_secrets.yaml`, `create_resources.yaml` -- whenever modifying `vm_template_spec`
```yaml
- name: Add {component} to template spec
  ansible.builtin.set_fact:
    vm_template_spec: "{{ vm_template_spec | combine(patch_var, recursive=True, list_merge='append') }}"
  vars:
    patch_var:
      domain:
        devices:
          disks:
            - name: "{disk-name}"
              disk:
                bus: virtio
```

### Soft-Fail Delete Pattern
**Source:** `ocp_virt_vm/tasks/delete_resources.yaml` (lines 93-106)
**Apply to:** `delete_resources.yaml` for all optional resource cleanup
```yaml
- name: Delete {optional resource}
  kubernetes.core.k8s:
    kubeconfig: "{{ remote_cluster_kubeconfig | default(omit) }}"
    api_version: v1
    kind: Secret
    name: "{{ compute_instance_name }}-{suffix}"
    namespace: "{{ compute_instance_target_namespace }}"
    state: absent
  register: delete_result
  failed_when:
    - delete_result.failed is defined
    - delete_result.failed
    - "'not found' not in (delete_result.msg | default(''))"
```

### VM Labels (Global Variable)
**Source:** `ocp_virt_vm/defaults/main.yaml` (line 4) + `group_vars/all/osac_common_labels.yaml` (line 4)
**Apply to:** All resource creation tasks
```yaml
# defaults/main.yaml (reuse identical pattern)
default_vm_labels: "{{ {compute_instance_label: compute_instance_name} }}"

# group_vars/all/osac_common_labels.yaml (already defined, shared, no changes needed)
compute_instance_label: "osac.openshift.io/computeinstance"
compute_instance_osac_finalizer: "osac.openshift.io/computeinstance-aap"
```

### Workflow Dispatch (No Changes Needed)
**Source:** `playbook_osac_create_compute_instance.yml` (line 66), `collections/ansible_collections/osac/workflows/playbooks/compute_instance/create.yml` (line 95)
**Apply to:** No new files needed. Existing workflow dispatch uses `template_id` from `compute_instance.spec.templateID`, which will be `osac.templates.windows_oci_vm` for Windows VMs.
```yaml
- name: Call selected template
  ansible.builtin.include_role:
    name: "{{ template_id_override | default(template_id) }}"
    tasks_from: create
```

### Finalizer Pattern (No Changes Needed)
**Source:** `collections/ansible_collections/osac/service/roles/finalizer/tasks/main.yaml`
**Apply to:** Handled by workflow layer. Template role does not interact with finalizers directly.

### Integration Test Pattern
**Source:** `tests/integration/targets/compute_instance_create/tasks/baseline.yml` (lines 1-57)
**Apply to:** Future test for `windows_oci_vm`
```yaml
- name: Read ComputeInstance fixture
  ansible.builtin.set_fact:
    test_compute_instance: "{{ lookup('file', '../../../fixtures/computeinstance-windows-test.yaml') | from_yaml }}"

- name: Set test variables for baseline workflow
  ansible.builtin.set_fact:
    ansible_eda:
      event:
        payload: "{{ test_compute_instance }}"
    tenant_target_namespace: "computeinstance-test-vm-work"
    # Override resource creation to prevent actual VM/DataVolume creation
    create_step_resources_override:
      name: osac.workflows.workflow_helpers
      tasks_from: noop.yml
    # Override wait/annotate since there's no VM to wait for
    create_step_wait_annotate_override:
      name: osac.workflows.workflow_helpers
      tasks_from: noop.yml
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | -- | -- | All 17 files have exact analogs in `ocp_virt_vm` or `tests/integration/` |

**Note:** Windows-specific content (sysprep unattend.xml, CloudBase-Init user-data, enhanced Hyper-V enlightenments) represents data-level changes within existing file patterns, not new structural patterns. The CONTEXT.md Canonical References section identifies these as requiring web research for the specific YAML/XML content, but the Ansible task structure follows the existing `ocp_virt_vm` patterns exactly.

## Metadata

**Analog search scope:**
- `collections/ansible_collections/osac/templates/roles/ocp_virt_vm/` (primary -- all 16 role files read)
- `collections/ansible_collections/osac/templates/roles/cudn_net/meta/` (meta pattern comparison)
- `collections/ansible_collections/osac/templates/roles/ocp_4_17_small/meta/` (meta pattern comparison)
- `collections/ansible_collections/osac/templates/roles/metallb_l2/meta/` (meta pattern comparison)
- `collections/ansible_collections/osac/workflows/playbooks/compute_instance/` (create.yml, delete.yml)
- `collections/ansible_collections/osac/service/roles/` (common, finalizer, tenant_target_namespace, tenant_storage_class)
- `playbook_osac_create_compute_instance.yml`, `playbook_osac_delete_compute_instance.yml` (entry points)
- `group_vars/all/osac_common_labels.yaml` (shared constants)
- `tests/integration/fixtures/` and `tests/integration/targets/compute_instance_create/` (test patterns)
- `collections/ansible_collections/osac/templates/galaxy.yml` (collection metadata)

**Files scanned:** 42
**Pattern extraction date:** 2026-04-28
