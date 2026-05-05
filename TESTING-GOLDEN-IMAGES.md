# Testing Windows Golden Images

This guide helps verify the `vm_enable_sysprep` fix for Windows golden image boot issues.

## Problem

Windows golden images (pre-configured, pre-sysprepped) failed to boot when the role unconditionally attached a sysprep disk, causing boot to hang at "Booting from hard disk" message.

## Solution

Added `vm_enable_sysprep` flag (default: `true`) to disable sysprep disk creation for golden images.

## Quick Test

### 1. Prepare test environment

```bash
# Set your kubeconfig
export KUBECONFIG=/path/to/your/kubeconfig

# Copy and customize test variables
cp tests/golden-image-vars.yml.example tests/golden-image-vars.yml
# Edit golden-image-vars.yml with your golden image reference
```

### 2. Run the test playbook

```bash
# From osac-aap-run-windows-vm directory
ansible-playbook tests/test-windows-golden-image.yml -e @tests/golden-image-vars.yml
```

### 3. Verify boot via VNC console

```bash
# Connect to VNC (requires virtctl)
virtctl vnc test-golden-windows -n test-golden-images

# Expected: Windows boots to desktop (not stuck at "Booting from hard disk")
```

### 4. Verify no sysprep disk attached

```bash
# Check volumes (should NOT include sysprep-disk)
kubectl get vm test-golden-windows -n test-golden-images \
  -o json | jq '.spec.template.spec.volumes[].name'

# Expected output: boot-disk, cloud-init-disk (if user-data provided)
# Should NOT include: sysprep-disk
```

## Manual Test (Without Playbook)

### Option A: Using the role directly

```yaml
- name: Deploy Windows golden image
  ansible.builtin.include_role:
    name: osac.templates.ocp_virt_vm
    tasks_from: create_compute_instance
  vars:
    vm_enable_sysprep: false  # Critical for golden images
    guest_os_family: windows
    compute_instance:
      metadata:
        name: "my-golden-vm"
        namespace: "my-namespace"
        annotations:
          osac.openshift.io/guest-os-family: "windows"
      spec:
        cores: 4
        memoryGiB: 8
        bootDisk:
          sizeGiB: 60
        image:
          sourceRef: "quay.io/jhernand/ci:latest"
```

### Option B: Via ComputeInstance CR

```yaml
apiVersion: osac.openshift.io/v1alpha1
kind: ComputeInstance
metadata:
  name: my-golden-vm
  namespace: my-namespace
  annotations:
    osac.openshift.io/guest-os-family: "windows"
    # Add this annotation to disable sysprep for golden images
    osac.openshift.io/vm-enable-sysprep: "false"
spec:
  cores: 4
  memoryGiB: 8
  bootDisk:
    sizeGiB: 60
  image:
    sourceRef: "quay.io/jhernand/ci:latest"
```

**Note:** If using CR approach, ensure the playbook/operator extracts the `vm-enable-sysprep` annotation and passes it to the role.

## Verification Checklist

- [ ] VM reaches `VirtualMachine.status.ready = True`
- [ ] VM boots past "Booting from hard disk" message
- [ ] Windows desktop or login screen appears in VNC console
- [ ] No `sysprep-disk` volume in VM spec
- [ ] No `sysprep-disk` ConfigMap in namespace

## Troubleshooting

### Boot still hangs at "Booting from hard disk"

1. **Check sysprep disk was actually disabled:**
   ```bash
   kubectl get cm -n <namespace> | grep sysprep
   # Should be empty for golden images
   ```

2. **Verify vm_enable_sysprep variable:**
   ```bash
   # Check role defaults
   grep vm_enable_sysprep collections/ansible_collections/osac/templates/roles/ocp_virt_vm/defaults/main.yaml
   ```

3. **Check VM volumes:**
   ```bash
   kubectl get vm <vm-name> -n <namespace> -o yaml | grep -A 10 volumes:
   ```

### VM boots but hostname is not set

Golden images may have pre-configured hostnames. If you need to set the hostname:

**Option 1:** Use CloudBase-Init user-data (recommended for golden images)
```yaml
spec:
  userDataSecretRef:
    name: "my-user-data-secret"
```

Create secret with CloudBase-Init configuration:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-user-data-secret
type: Opaque
stringData:
  userdata: |
    #cloud-config
    hostname: my-custom-hostname
```

**Option 2:** Enable sysprep (only for non-golden images)
```yaml
vars:
  vm_enable_sysprep: true  # Use only for fresh Windows images
```

## Cleanup

```bash
# Delete test VM
kubectl delete vm test-golden-windows -n test-golden-images

# Delete test namespace
kubectl delete namespace test-golden-images
```

## Related

- Debug session: `.planning/debug/windows-vm-boot-stuck.md`
- Sample payload: `samples/windows_golden_image_payload.json`
- Fix commit: `8835f3c` - fix(ocp_virt_vm): add vm_enable_sysprep flag for golden image support
