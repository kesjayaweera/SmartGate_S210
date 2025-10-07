#!/bin/bash

# SmartGate Camera Fix & Diagnostic Script
# Comprehensive camera fixing, testing, and debugging for ArduCam cameras
# Based on NVIDIA forum solutions for IMX219/IMX477 camera issues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_CAMERAS=4
TEST_DURATION=10
CAPTURE_COUNT=5
LOG_FILE="/tmp/camera_fix_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for fix operations
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo) for fix operations"
        exit 1
    fi
}

# =============================================================================
# CAMERA FIX FUNCTIONS
# =============================================================================

fix_camera_headers() {
    log "=== FIXING CAMERA HEADER ISSUES ==="
    
    # Step 1: Stop all camera-related services
    log "Stopping camera services..."
    systemctl stop nvargus-daemon 2>/dev/null || true
    pkill -f nvargus 2>/dev/null || true
    pkill -f gst-launch 2>/dev/null || true
    sleep 2
    
    # Step 2: Reset camera modules
    log "Resetting camera modules..."
    modprobe -r tegra-camera-platform 2>/dev/null || true
    modprobe -r tegra-camera-rpc 2>/dev/null || true
    modprobe -r tegra-camera-common 2>/dev/null || true
    sleep 2
    
    # Step 3: Reload camera modules
    log "Reloading camera modules..."
    modprobe tegra-camera-common
    modprobe tegra-camera-rpc
    modprobe tegra-camera-platform
    sleep 2
    
    # Step 4: Restart nvargus daemon
    log "Restarting nvargus daemon..."
    systemctl restart nvargus-daemon
    sleep 3
    
    # Step 5: Check if nvargus daemon is running
    if systemctl is-active --quiet nvargus-daemon; then
        log_success "nvargus daemon restarted successfully"
    else
        log_warning "nvargus daemon may not be running properly"
    fi
    
    log "Camera header fix completed"
    echo
}

fix_camera_drivers() {
    log "=== FIXING CAMERA DRIVERS ==="
    
    # Step 1: Check for I2C errors
    log "Checking for I2C errors..."
    local i2c_errors=$(dmesg | grep -i "i2c.*error" | wc -l)
    if [ "$i2c_errors" -gt 0 ]; then
        log_warning "Found $i2c_errors I2C errors in dmesg"
        log "Recent I2C errors:"
        dmesg | grep -i "i2c.*error" | tail -5 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No I2C errors found"
    fi
    
    # Step 2: Check for video device errors
    log "Checking for video device errors..."
    local video_errors=$(dmesg | grep -i "video.*error" | wc -l)
    if [ "$video_errors" -gt 0 ]; then
        log_warning "Found $video_errors video device errors in dmesg"
        log "Recent video errors:"
        dmesg | grep -i "video.*error" | tail -5 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No video device errors found"
    fi
    
    # Step 3: Reset video devices
    log "Resetting video devices..."
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            log "Resetting /dev/video$i..."
            echo 1 > /sys/class/video4linux/video$i/device/reset 2>/dev/null || true
        fi
    done
    
    log "Camera driver fix completed"
    echo
}

# =============================================================================
# DIAGNOSTIC FUNCTIONS
# =============================================================================

diagnose_system_info() {
    log "=== SYSTEM DIAGNOSTICS ==="
    log "Hostname: $(hostname)"
    log "Kernel: $(uname -r)"
    log "Architecture: $(uname -m)"
    log "Uptime: $(uptime)"
    log "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    log "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
    log "Temperature: $(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000 "°C"}' || echo "N/A")"
    echo
}

diagnose_camera_modules() {
    log "=== CAMERA MODULE DIAGNOSTICS ==="
    
    # Check loaded camera modules
    log "Loaded camera modules:"
    lsmod | grep -E "(camera|nvargus|tegra)" | while read -r line; do
        log "  $line"
    done
    
    # Check nvargus daemon status
    log "nvargus daemon status:"
    if systemctl is-active --quiet nvargus-daemon; then
        log_success "  nvargus-daemon: Active"
    else
        log_error "  nvargus-daemon: Inactive"
    fi
    
    # Check for IMX camera errors
    log "IMX camera errors in dmesg:"
    local imx_errors=$(dmesg | grep -i imx | wc -l)
    if [ "$imx_errors" -gt 0 ]; then
        log_warning "Found $imx_errors IMX-related messages"
        dmesg | grep -i imx | tail -10 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No IMX-related messages found"
    fi
    
    # Check for video device errors
    log "Video device errors in dmesg:"
    local video_errors=$(dmesg | grep -i "vi.*error" | wc -l)
    if [ "$video_errors" -gt 0 ]; then
        log_warning "Found $video_errors video device errors"
        dmesg | grep -i "vi.*error" | tail -5 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No video device errors found"
    fi
    echo
}

diagnose_video_devices() {
    log "=== VIDEO DEVICE DIAGNOSTICS ==="
    
    local found_devices=()
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            found_devices+=($i)
            log "Found video device: /dev/video$i"
            
            # Get device info
            if command -v v4l2-ctl >/dev/null 2>&1; then
                local driver=$(v4l2-ctl --device="/dev/video$i" --info 2>/dev/null | grep "Driver name" | cut -d: -f2 | xargs || echo "Unknown")
                local card=$(v4l2-ctl --device="/dev/video$i" --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs || echo "Unknown")
                log "  Driver: $driver"
                log "  Card: $card"
                
                # List supported formats
                log "  Supported formats:"
                v4l2-ctl --device="/dev/video$i" --list-formats-ext 2>/dev/null | grep -E "(Index|Type|Size|Pixel") | head -10 | while read -r line; do
                    log "    $line"
                done
            fi
        fi
    done
    
    if [ ${#found_devices[@]} -eq 0 ]; then
        log_error "No video devices found!"
        return 1
    else
        log_success "Found ${#found_devices[@]} video device(s): ${found_devices[*]}"
    fi
    echo
}

# =============================================================================
# QUICK DIAGNOSTIC COMMANDS
# =============================================================================

quick_diagnostic() {
    log "=== QUICK DIAGNOSTIC COMMANDS ==="
    
    # Restart nvargus daemon
    log "Restarting nvargus daemon..."
    sudo systemctl restart nvargus-daemon
    sleep 2
    
    # Test nvarguscamerasrc with overlay
    log "Testing nvarguscamerasrc with overlay..."
    if command -v gst-launch-1.0 >/dev/null 2>&1; then
        timeout 5 gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink >/dev/null 2>&1 && log_success "nvarguscamerasrc overlay test passed" || log_warning "nvarguscamerasrc overlay test failed"
    else
        log_warning "gst-launch-1.0 not available"
    fi
    
    # Capture test frame
    log "Capturing test frame..."
    if command -v gst-launch-1.0 >/dev/null 2>&1; then
        if gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! jpegenc ! filesink location=test.jpg >/dev/null 2>&1; then
            log_success "Test frame captured: test.jpg"
            if command -v xdg-open >/dev/null 2>&1; then
                log "Opening test image..."
                xdg-open test.jpg >/dev/null 2>&1 &
            fi
        else
            log_warning "Failed to capture test frame"
        fi
    else
        log_warning "gst-launch-1.0 not available"
    fi
    
    # Check IMX errors
    log "Checking IMX errors in dmesg..."
    local imx_errors=$(dmesg | grep -i imx | wc -l)
    if [ "$imx_errors" -gt 0 ]; then
        log_warning "Found $imx_errors IMX-related messages"
        dmesg | grep -i imx | tail -5 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No IMX-related messages found"
    fi
    
    # Check video device errors
    log "Checking video device errors in dmesg..."
    local video_errors=$(dmesg | grep -i "vi.*error" | wc -l)
    if [ "$video_errors" -gt 0 ]; then
        log_warning "Found $video_errors video device errors"
        dmesg | grep -i "vi.*error" | tail -5 | while read -r line; do
            log "  $line"
        done
    else
        log_success "No video device errors found"
    fi
    
    # Test GStreamer pipeline
    log "Testing GStreamer pipeline..."
    if command -v gst-launch-1.0 >/dev/null 2>&1; then
        timeout 5 gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=640,height=480,framerate=30/1' ! nvvidconv ! videoconvert ! autovideosink sync=false >/dev/null 2>&1 && log_success "GStreamer pipeline test passed" || log_warning "GStreamer pipeline test failed"
    else
        log_warning "gst-launch-1.0 not available"
    fi
    
    echo
}

# =============================================================================
# COMPREHENSIVE TESTING FUNCTIONS
# =============================================================================

test_camera_capture() {
    log "=== CAMERA CAPTURE TESTING ==="
    
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            log "Testing capture for /dev/video$i:"
            
            # Test with v4l2-ctl
            if command -v v4l2-ctl >/dev/null 2>&1; then
                log "  Testing v4l2-ctl capture..."
                local test_file="/tmp/test_capture_$i.raw"
                if timeout 5 v4l2-ctl --device="/dev/video$i" --stream-to="$test_file" --stream-count=1 >/dev/null 2>&1; then
                    local file_size=$(stat -c%s "$test_file" 2>/dev/null || echo "0")
                    if [ "$file_size" -gt 1000 ]; then
                        log_success "  v4l2-ctl capture successful (${file_size} bytes)"
                    else
                        log_warning "  v4l2-ctl capture too small (${file_size} bytes)"
                    fi
                    rm -f "$test_file"
                else
                    log_warning "  v4l2-ctl capture failed"
                fi
            fi
            
            # Test with OpenCV (if available)
            if command -v python3 >/dev/null 2>&1; then
                log "  Testing OpenCV capture..."
                local python_test="
import cv2
import sys
try:
    cap = cv2.VideoCapture($i, cv2.CAP_V4L2)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print('SUCCESS: OpenCV V4L2 capture successful')
        else:
            print('WARNING: OpenCV V4L2 read failed')
        cap.release()
    else:
        print('WARNING: OpenCV V4L2 open failed')
except Exception as e:
    print(f'ERROR: OpenCV test failed: {e}')
"
                local result=$(echo "$python_test" | python3 2>/dev/null || echo "ERROR: Python test failed")
                log "  $result"
            fi
            echo
        fi
    done
}

test_gstreamer_pipelines() {
    log "=== GSTREAMER PIPELINE TESTING ==="
    
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            log "Testing GStreamer pipeline for camera $i:"
            
            # Test nvarguscamerasrc pipeline
            local pipeline="nvarguscamerasrc sensor-id=$i ! video/x-raw(memory:NVMM),width=640,height=480,format=NV12,framerate=15/1 ! nvvidconv ! video/x-raw,width=640,height=480,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! appsink"
            
            if command -v gst-launch-1.0 >/dev/null 2>&1; then
                log "  Testing nvarguscamerasrc pipeline..."
                if timeout 5 gst-launch-1.0 $pipeline --quiet >/dev/null 2>&1; then
                    log_success "  nvarguscamerasrc pipeline successful"
                else
                    log_warning "  nvarguscamerasrc pipeline failed"
                fi
            else
                log_warning "  gst-launch-1.0 not available"
            fi
            
            # Test v4l2src pipeline
            local v4l2_pipeline="v4l2src device=/dev/video$i ! video/x-raw,width=640,height=480,format=YUY2 ! videoconvert ! video/x-raw,format=BGR ! appsink"
            
            if command -v gst-launch-1.0 >/dev/null 2>&1; then
                log "  Testing v4l2src pipeline..."
                if timeout 5 gst-launch-1.0 $v4l2_pipeline --quiet >/dev/null 2>&1; then
                    log_success "  v4l2src pipeline successful"
                else
                    log_warning "  v4l2src pipeline failed"
                fi
            fi
            echo
        fi
    done
}

test_camera_streaming() {
    log "=== CAMERA STREAMING TEST ==="
    
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            log "Testing streaming for camera $i (${TEST_DURATION} seconds):"
            
            # Test with OpenCV
            if command -v python3 >/dev/null 2>&1; then
                local python_stream_test="
import cv2
import time
import sys

try:
    cap = cv2.VideoCapture($i, cv2.CAP_V4L2)
    if not cap.isOpened():
        print('ERROR: Cannot open camera $i')
        sys.exit(1)
    
    frame_count = 0
    start_time = time.time()
    
    while time.time() - start_time < $TEST_DURATION:
        ret, frame = cap.read()
        if ret:
            frame_count += 1
        else:
            print(f'WARNING: Failed to read frame {frame_count}')
        time.sleep(0.1)
    
    cap.release()
    fps = frame_count / $TEST_DURATION
    print(f'SUCCESS: Captured {frame_count} frames in $TEST_DURATION seconds (FPS: {fps:.1f})')
    
except Exception as e:
    print(f'ERROR: Streaming test failed: {e}')
"
                local result=$(echo "$python_stream_test" | python3 2>/dev/null || echo "ERROR: Python streaming test failed")
                log "  $result"
            fi
            echo
        fi
    done
}

test_camera_captures() {
    log "=== CAMERA CAPTURE TEST ==="
    
    local capture_dir="/tmp/camera_captures_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$capture_dir"
    
    for i in $(seq 0 $((MAX_CAMERAS-1))); do
        if [ -e "/dev/video$i" ]; then
            log "Capturing $CAPTURE_COUNT frames from camera $i:"
            
            if command -v python3 >/dev/null 2>&1; then
                local python_capture_test="
import cv2
import os

try:
    cap = cv2.VideoCapture($i, cv2.CAP_V4L2)
    if not cap.isOpened():
        print('ERROR: Cannot open camera $i')
        exit(1)
    
    captured = 0
    for i in range($CAPTURE_COUNT):
        ret, frame = cap.read()
        if ret:
            filename = '$capture_dir/camera_$i_frame_{i+1}.jpg'
            cv2.imwrite(filename, frame)
            captured += 1
        time.sleep(0.5)
    
    cap.release()
    print(f'SUCCESS: Captured {captured}/$CAPTURE_COUNT frames')
    
except Exception as e:
    print(f'ERROR: Capture test failed: {e}')
"
                local result=$(echo "$python_capture_test" | python3 2>/dev/null || echo "ERROR: Python capture test failed")
                log "  $result"
            fi
            echo
        fi
    done
    
    # List captured files
    if [ -d "$capture_dir" ]; then
        local file_count=$(find "$capture_dir" -name "*.jpg" | wc -l)
        if [ "$file_count" -gt 0 ]; then
            log_success "Captured $file_count test images in $capture_dir"
            log "Files: $(ls -la "$capture_dir"/*.jpg 2>/dev/null | wc -l) images"
        else
            log_warning "No images captured"
        fi
    fi
    echo
}

# =============================================================================
# JETSON-IO CONFIGURATION
# =============================================================================

configure_jetson_io() {
    log "=== JETSON-IO CONFIGURATION ==="
    log "Opening Jetson-IO configuration tool..."
    log "Note: You can use this to disable camera interfaces if needed"
    log "But you cannot disable individual cameras (cam0, cam1) - only the entire camera interface"
    
    if [ -f "/opt/nvidia/jetson-io/jetson-io.py" ]; then
        log "Starting Jetson-IO configuration..."
        sudo /opt/nvidia/jetson-io/jetson-io.py
    else
        log_error "Jetson-IO configuration tool not found at /opt/nvidia/jetson-io/jetson-io.py"
    fi
    echo
}

# =============================================================================
# MAIN EXECUTION FUNCTIONS
# =============================================================================

run_fix_mode() {
    log "=== RUNNING CAMERA FIX MODE ==="
    check_root
    fix_camera_headers
    fix_camera_drivers
    quick_diagnostic
    log_success "Camera fix mode completed"
}

run_diagnostic_mode() {
    log "=== RUNNING DIAGNOSTIC MODE ==="
    diagnose_system_info
    diagnose_camera_modules
    diagnose_video_devices
    quick_diagnostic
    log_success "Diagnostic mode completed"
}

run_test_mode() {
    log "=== RUNNING COMPREHENSIVE TEST MODE ==="
    test_camera_capture
    test_gstreamer_pipelines
    test_camera_streaming
    test_camera_captures
    log_success "Comprehensive test mode completed"
}

run_full_mode() {
    log "=== RUNNING FULL MODE (FIX + DIAGNOSTIC + TEST) ==="
    check_root
    fix_camera_headers
    fix_camera_drivers
    diagnose_system_info
    diagnose_camera_modules
    diagnose_video_devices
    quick_diagnostic
    test_camera_capture
    test_gstreamer_pipelines
    test_camera_streaming
    test_camera_captures
    log_success "Full mode completed"
}

generate_test_report() {
    log "=== TEST REPORT GENERATION ==="
    
    local report_file="/tmp/camera_fix_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "SmartGate Camera Fix & Diagnostic Report"
        echo "Generated: $(date)"
        echo "Hostname: $(hostname)"
        echo "Kernel: $(uname -r)"
        echo "=================================="
        echo
        
        echo "Video Devices:"
        for i in $(seq 0 $((MAX_CAMERAS-1))); do
            if [ -e "/dev/video$i" ]; then
                echo "  /dev/video$i: Available"
                if command -v v4l2-ctl >/dev/null 2>&1; then
                    local driver=$(v4l2-ctl --device="/dev/video$i" --info 2>/dev/null | grep "Driver name" | cut -d: -f2 | xargs || echo "Unknown")
                    local card=$(v4l2-ctl --device="/dev/video$i" --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs || echo "Unknown")
                    echo "    Driver: $driver"
                    echo "    Card: $card"
                fi
            else
                echo "  /dev/video$i: Not available"
            fi
        done
        echo
        
        echo "System Information:"
        echo "  Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
        echo "  Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
        echo "  Temperature: $(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1 | awk '{print $1/1000 "°C"}' || echo "N/A")"
        echo
        
        echo "Recent Errors:"
        echo "  IMX errors: $(dmesg | grep -i imx | wc -l)"
        echo "  Video errors: $(dmesg | grep -i "vi.*error" | wc -l)"
        echo "  I2C errors: $(dmesg | grep -i "i2c.*error" | wc -l)"
        echo
        
        echo "Test Results:"
        echo "  Log file: $LOG_FILE"
        echo "  Test duration: $(date -d@$(($(date +%s) - $(stat -c %Y "$LOG_FILE" 2>/dev/null || echo $(date +%s)))) -u +%H:%M:%S 2>/dev/null || echo "Unknown")"
        echo
        
    } > "$report_file"
    
    log_success "Test report generated: $report_file"
    echo
}

# Help function
show_help() {
    echo "SmartGate Camera Fix & Diagnostic Script"
    echo "Usage: $0 [MODE] [OPTIONS]"
    echo
    echo "Modes:"
    echo "  fix                 Fix camera header issues and restart services"
    echo "  diagnostic          Run diagnostic checks only"
    echo "  test                Run comprehensive camera tests"
    echo "  full                Run fix + diagnostic + test (default)"
    echo "  jetson-io           Open Jetson-IO configuration tool"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -c, --cameras N     Maximum number of cameras to test (default: 4)"
    echo "  -d, --duration N    Test duration in seconds (default: 10)"
    echo "  -n, --captures N    Number of test captures (default: 5)"
    echo "  -l, --log FILE      Log file path (default: auto-generated)"
    echo
    echo "Examples:"
    echo "  $0                  # Run full mode with defaults"
    echo "  $0 fix              # Fix camera issues only"
    echo "  $0 diagnostic       # Run diagnostics only"
    echo "  $0 test -c 2 -d 5  # Test 2 cameras for 5 seconds"
    echo "  $0 jetson-io        # Open Jetson-IO configuration"
    echo
    echo "Quick Diagnostic Commands:"
    echo "  sudo systemctl restart nvargus-daemon"
    echo "  gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink"
    echo "  gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! jpegenc ! filesink location=test.jpg"
    echo "  xdg-open test.jpg"
    echo "  dmesg | grep imx"
    echo "  dmesg | grep vi"
    echo "  sudo /opt/nvidia/jetson-io/jetson-io.py"
}

# Main execution
main() {
    local mode="full"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--cameras)
                MAX_CAMERAS="$2"
                shift 2
                ;;
            -d|--duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            -n|--captures)
                CAPTURE_COUNT="$2"
                shift 2
                ;;
            -l|--log)
                LOG_FILE="$2"
                shift 2
                ;;
            fix|diagnostic|test|full|jetson-io)
                mode="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log "SmartGate Camera Fix & Diagnostic Script Started"
    log "Mode: $mode"
    log "Log file: $LOG_FILE"
    log "Max cameras to test: $MAX_CAMERAS"
    echo
    
    # Run selected mode
    case $mode in
        "fix")
            run_fix_mode
            ;;
        "diagnostic")
            run_diagnostic_mode
            ;;
        "test")
            run_test_mode
            ;;
        "full")
            run_full_mode
            ;;
        "jetson-io")
            configure_jetson_io
            ;;
        *)
            log_error "Unknown mode: $mode"
            show_help
            exit 1
            ;;
    esac
    
    generate_test_report
    
    log "SmartGate Camera Fix & Diagnostic Script Completed"
    log "Check log file for detailed results: $LOG_FILE"
}

# Run main function
main "$@"