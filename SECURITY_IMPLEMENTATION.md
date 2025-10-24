# Zero-Trust Security Implementation

## KubeArmor Policy
- Created zero-trust policy blocking shell access, network tools, and sensitive files
- Policy applied but KubeArmor daemonset incompatible with Minikube environment

## Native Kubernetes Security
- Implemented securityContext with readOnlyRootFilesystem
- Dropped all capabilities
- Run as non-root user
- Resource limits enforced
- Seccomp and AppArmor annotations

## Files Created
- `kubearmor-minikube.yaml` - KubeArmor installation attempt
- `zero-trust-policy.yaml` - KubeArmor zero-trust policy
- `native-security-policy.yaml` - Native Kubernetes security implementation
- `test-workload.yaml` - Test deployment
- `test-security.sh` - Security testing script