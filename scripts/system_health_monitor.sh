#!/bin/bash

# System Health Monitoring Script
# Monitors CPU, Memory, Disk, and Processes with alerts

# Configuration
THRESHOLD_CPU=80
THRESHOLD_MEM=85
THRESHOLD_DISK=90
THRESHOLD_LOAD=1.5
MAX_PROCESSES=500

# Alert files
ALERT_FILE="/var/log/system_alerts.log"
REPORT_FILE="/tmp/system_health_report.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize alert file
init_alert_file() {
     touch "$ALERT_FILE"
     chmod 644 "$ALERT_FILE"
}

# Log alert message
log_alert() {
    local message="$1"
    local level="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [$level] $message" |  tee -a "$ALERT_FILE" >/dev/null
}

# Get system information
get_system_info() {
    echo "=== SYSTEM INFORMATION ===" > "$REPORT_FILE"
    echo "Hostname: $(hostname)" >> "$REPORT_FILE"
    echo "Uptime: $(uptime -p)" >> "$REPORT_FILE"
    echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || uname -o)" >> "$REPORT_FILE"
    echo "Kernel: $(uname -r)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
}

# Check CPU usage
check_cpu() {
    echo -e "${BLUE}🔍 Checking CPU Usage...${NC}"
    
    # Get CPU usage (multiple methods for compatibility)
    local cpu_usage
    if command -v mpstat &> /dev/null; then
        cpu_usage=$(mpstat 1 1 | awk '$12 ~ /[0-9.]+/ {print 100 - $12}' | tail -1)
    else
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    fi
    
    local load_avg=$(awk '{print $1}' /proc/loadavg)
    local cpu_cores=$(nproc)
    
    echo "CPU Usage: ${cpu_usage}%"
    echo "Load Average: ${load_avg} (Cores: ${cpu_cores})"
    
    if (( $(echo "$cpu_usage > $THRESHOLD_CPU" | bc -l 2>/dev/null || echo "$cpu_usage > $THRESHOLD_CPU" ) )); then
        echo -e "${RED}🚨 ALERT: High CPU usage: ${cpu_usage}%${NC}"
        log_alert "High CPU usage: ${cpu_usage}%" "CRITICAL"
        return 1
    fi
    
    if (( $(echo "$load_avg > $cpu_cores * $THRESHOLD_LOAD" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${YELLOW}⚠️  WARNING: High load average: ${load_avg}${NC}"
        log_alert "High load average: ${load_avg}" "WARNING"
        return 2
    fi
    
    echo -e "${GREEN}✅ CPU usage normal${NC}"
    return 0
}

# Check Memory usage
check_memory() {
    echo -e "${BLUE}🔍 Checking Memory Usage...${NC}"
    
    local mem_info=$(free -m | grep Mem)
    local total_mem=$(echo "$mem_info" | awk '{print $2}')
    local used_mem=$(echo "$mem_info" | awk '{print $3}')
    local free_mem=$(echo "$mem_info" | awk '{print $4}')
    local mem_usage=$((used_mem * 100 / total_mem))
    
    local swap_info=$(free -m | grep Swap)
    local swap_used=$(echo "$swap_info" | awk '{print $3}')
    
    echo "Memory Usage: ${mem_usage}% (${used_mem}MB/${total_mem}MB used)"
    echo "Free Memory: ${free_mem}MB"
    echo "Swap Used: ${swap_used}MB"
    
    if [ "$mem_usage" -gt "$THRESHOLD_MEM" ]; then
        echo -e "${RED}🚨 ALERT: High Memory usage: ${mem_usage}%${NC}"
        log_alert "High Memory usage: ${mem_usage}%" "CRITICAL"
        return 1
    fi
    
    if [ "$free_mem" -lt 100 ]; then
        echo -e "${YELLOW}⚠️  WARNING: Low free memory: ${free_mem}MB${NC}"
        log_alert "Low free memory: ${free_mem}MB" "WARNING"
        return 2
    fi
    
    echo -e "${GREEN}✅ Memory usage normal${NC}"
    return 0
}

# Check Disk usage
check_disk() {
    echo -e "${BLUE}🔍 Checking Disk Usage...${NC}"
    
    local disk_issues=0
    
    # Check root filesystem
    local root_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local root_available=$(df / | awk 'NR==2 {print $4}')
    
    echo "Root (/) Usage: ${root_usage}%"
    echo "Available: ${root_available}KB"
    
    if [ "$root_usage" -gt "$THRESHOLD_DISK" ]; then
        echo -e "${RED}🚨 ALERT: High disk usage on /: ${root_usage}%${NC}"
        log_alert "High disk usage on /: ${root_usage}%" "CRITICAL"
        disk_issues=1
    fi
    
    # Check all mounted filesystems
    echo "Other filesystems:"
    df -h | awk 'NR>1 {print $6 " : " $5 " : " $4 " free"}' | while read line; do
        echo "  $line"
    done
    
    # Check inode usage
    local inode_usage=$(df -i / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$inode_usage" -gt 90 ]; then
        echo -e "${YELLOW}⚠️  WARNING: High inode usage: ${inode_usage}%${NC}"
        log_alert "High inode usage: ${inode_usage}%" "WARNING"
    fi
    
    if [ "$disk_issues" -eq 0 ]; then
        echo -e "${GREEN}✅ Disk usage normal${NC}"
    fi
    
    return $disk_issues
}

# Check Running Processes
check_processes() {
    echo -e "${BLUE}🔍 Checking Running Processes...${NC}"
    
    local total_processes=$(ps -e --no-headers | wc -l)
    local zombie_processes=$(ps -e -o stat --no-headers | grep -c Z)
    
    echo "Total Processes: $total_processes"
    echo "Zombie Processes: $zombie_processes"
    
    # Top 5 CPU consuming processes
    echo "Top 5 CPU-consuming processes:"
    ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -6
    
    if [ "$total_processes" -gt "$MAX_PROCESSES" ]; then
        echo -e "${YELLOW}⚠️  WARNING: High number of processes: $total_processes${NC}"
        log_alert "High number of processes: $total_processes" "WARNING"
        return 2
    fi
    
    if [ "$zombie_processes" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  WARNING: Zombie processes detected: $zombie_processes${NC}"
        log_alert "Zombie processes detected: $zombie_processes" "WARNING"
        return 2
    fi
    
    echo -e "${GREEN}✅ Process count normal${NC}"
    return 0
}

# Generate summary report
generate_report() {
    echo "" >> "$REPORT_FILE"
    echo "=== HEALTH CHECK SUMMARY ===" >> "$REPORT_FILE"
    echo "Timestamp: $(date)" >> "$REPORT_FILE"
    echo "Overall Status: $1" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    # Add recent alerts
    if [ -f "$ALERT_FILE" ]; then
        echo "Recent Alerts:" >> "$REPORT_FILE"
        tail -5 "$ALERT_FILE" >> "$REPORT_FILE" 2>/dev/null || echo "No alerts" >> "$REPORT_FILE"
    fi
}

# Main monitoring function
main_monitor() {
    echo "🖥️  SYSTEM HEALTH MONITOR"
    echo "================================"
    
    get_system_info
    
    local overall_status="HEALTHY"
    local exit_code=0
    
    # Run all checks
    check_cpu || exit_code=1
    echo "" >> "$REPORT_FILE"
    check_memory || exit_code=1
    echo "" >> "$REPORT_FILE"
    check_disk || exit_code=1
    echo "" >> "$REPORT_FILE"
    check_processes || [ $exit_code -eq 0 ] && exit_code=2
    
    # Determine overall status
    if [ $exit_code -eq 1 ]; then
        overall_status="CRITICAL"
        echo -e "\n${RED}🚨 SYSTEM STATUS: CRITICAL - Immediate attention needed${NC}"
    elif [ $exit_code -eq 2 ]; then
        overall_status="WARNING"
        echo -e "\n${YELLOW}⚠️  SYSTEM STATUS: WARNING - Monitor closely${NC}"
    else
        overall_status="HEALTHY"
        echo -e "\n${GREEN}✅ SYSTEM STATUS: HEALTHY${NC}"
    fi
    
    generate_report "$overall_status"
    
    # Display report location
    echo -e "\n${BLUE}📊 Detailed report saved to: $REPORT_FILE${NC}"
    if [ -f "$ALERT_FILE" ]; then
        echo -e "${BLUE}📋 Alert log: $ALERT_FILE${NC}"
    fi
    
    return $exit_code
}

# Handle command line arguments
case "${1:-}" in
    "report")
        if [ -f "$REPORT_FILE" ]; then
            cat "$REPORT_FILE"
        else
            echo "No report found. Run health check first."
        fi
        ;;
    "alerts")
        if [ -f "$ALERT_FILE" ]; then
             tail -20 "$ALERT_FILE"
        else
            echo "No alerts file found."
        fi
        ;;
    "continuous")
        echo "Starting continuous monitoring (Ctrl+C to stop)..."
        while true; do
            clear
            main_monitor
            sleep 60
        done
        ;;
    "install")
        echo "Installing system health monitor..."
         cp "$0" /usr/local/bin/system-health-monitor
         chmod +x /usr/local/bin/system-health-monitor
        echo "✅ Installed as system-health-monitor"
        ;;
    *)
        main_monitor
        ;;
esac