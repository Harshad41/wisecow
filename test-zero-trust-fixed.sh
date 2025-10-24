#!/bin/bash

echo "=================================================="
echo "Zero-Trust Security Policy Violation Test"
echo "=================================================="

# Get the zero-trust pod
POD_NAME=$(kubectl get pods -l app=zero-trust-nginx -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "Error: Zero-trust pod not found"
    echo "Available pods:"
    kubectl get pods
    exit 1
fi

echo "Testing pod: $POD_NAME"
echo ""

# Test 1: Try to run shell (should work but with restrictions)
echo "1. Testing shell access:"
kubectl exec -it $POD_NAME -- sh -c "echo 'Shell access test'" 2>&1
echo ""

# Test 2: Try to write to root filesystem (should fail)
echo "2. Testing read-only root filesystem:"
kubectl exec -it $POD_NAME -- sh -c "touch /test.txt && echo 'Write successful' || echo 'Write failed - READ ONLY FS'" 2>&1
echo ""

# Test 3: Check user permissions
echo "3. Testing user permissions:"
kubectl exec -it $POD_NAME -- sh -c "whoami && id" 2>&1
echo ""

# Test 4: Try privilege escalation
echo "4. Testing privilege escalation:"
kubectl exec -it $POD_NAME -- sh -c "sudo ls /root 2>&1 | head -3" 2>&1
echo ""

# Test 5: Check capabilities
echo "5. Testing dropped capabilities:"
kubectl exec -it $POD_NAME -- sh -c "cat /proc/1/status | grep Cap" 2>&1
echo ""

echo "=================================================="
echo "Zero-Trust Policy Tests Completed"
echo "=================================================="