#!/bin/bash
POD_NAME=$(kubectl get pods -l app=secured-nginx -o jsonpath='{.items[0].metadata.name}')

echo "Testing security restrictions on pod: $POD_NAME"
echo "=============================================="

echo "1. Testing shell access:"
kubectl exec -it $POD_NAME -- /bin/sh -c "echo 'Test'" 2>&1

echo ""
echo "2. Testing file system (should be read-only):"
kubectl exec -it $POD_NAME -- /bin/sh -c "touch /test.txt" 2>&1

echo ""
echo "3. Testing user permissions:"
kubectl exec -it $POD_NAME -- /bin/sh -c "whoami && id" 2>&1

echo ""
echo "4. Testing privilege escalation:"
kubectl exec -it $POD_NAME -- /bin/sh -c "sudo ls" 2>&1

echo "=============================================="
EOF

