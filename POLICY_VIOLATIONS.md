# Zero-Trust Policy Violations Demonstrated

## Policy 1: Read-Only Root Filesystem
**Violation Attempt**: Writing to root filesystem
**Command**: `touch /test.txt`
**Expected Result**: Operation not permitted
**Security Impact**: Prevents malware from modifying system files

## Policy 2: Non-Root User Execution  
**Violation Attempt**: Running as root user
**Command**: `whoami`
**Expected Result**: Shows non-root user (1000)
**Security Impact**: Limits damage from container breaches

## Policy 3: No Privilege Escalation
**Violation Attempt**: Using sudo
**Command**: `sudo ls`
**Expected Result**: sudo not found or permission denied
**Security Impact**: Prevents elevation to root privileges

## Policy 4: Dropped Capabilities
**Violation Attempt**: Using privileged operations
**Command**: Check /proc/1/status
**Expected Result**: Limited capabilities shown
**Security Impact**: Reduces attack surface

## Policy 5: Network Restrictions
**Violation Attempt**: Unauthorized network access
**Command**: Various network calls
**Expected Result**: Blocked by network policies
**Security Impact**: Contains breaches within pod

## Verification Screenshots Taken
1. Pod running with security context
2. Network policies applied
3. Resource quotas enforced
4. Policy violation attempts being blocked