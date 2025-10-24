# test-zero-trust.ps1
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Zero-Trust Security Policy Violation Test" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Get the zero-trust pod
$POD_NAME = kubectl get pods -l app=zero-trust-nginx -o jsonpath='{.items[0].metadata.name}' 2>$null

if (-not $POD_NAME) {
    Write-Host "Error: Zero-trust pod not found" -ForegroundColor Red
    exit 1
}

Write-Host "Testing pod: $POD_NAME" -ForegroundColor Yellow
Write-Host ""

# Test 1: Try to run shell (should work but with restrictions)
Write-Host "1. Testing shell access:" -ForegroundColor Cyan
kubectl exec -it $POD_NAME -- sh -c "echo 'Shell access test'"
Write-Host ""

# Test 2: Try to write to root filesystem (should fail)
Write-Host "2. Testing read-only root filesystem:" -ForegroundColor Cyan
kubectl exec -it $POD_NAME -- sh -c "touch /test.txt && echo 'Write successful' || echo 'Write failed - READ ONLY FS'"
Write-Host ""

# Test 3: Check user permissions
Write-Host "3. Testing user permissions:" -ForegroundColor Cyan
kubectl exec -it $POD_NAME -- sh -c "whoami && id"
Write-Host ""

# Test 4: Try privilege escalation
Write-Host "4. Testing privilege escalation:" -ForegroundColor Cyan
kubectl exec -it $POD_NAME -- sh -c "sudo ls /root 2>&1 | head -3"
Write-Host ""

# Test 5: Check capabilities
Write-Host "5. Testing dropped capabilities:" -ForegroundColor Cyan
kubectl exec -it $POD_NAME -- sh -c "cat /proc/1/status | grep Cap"
Write-Host ""

Write-Host "==================================================" -ForegroundColor Green
Write-Host "Zero-Trust Policy Tests Completed" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green