#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export SIMULATOR_UDID="${SIMULATOR_UDID:-3BBC1F5A-396B-4234-A4FF-445CAB30E516}"
mkdir -p reports
xcrun simctl boot "$SIMULATOR_UDID" 2>/dev/null || true
xcrun simctl bootstatus "$SIMULATOR_UDID" -b
xcodebuild -project tests/ios/TapTests.xcodeproj -scheme TapTests -destination "platform=iOS Simulator,id=$SIMULATOR_UDID" -derivedDataPath /tmp/psycho-ios-build -parallel-testing-enabled NO build-for-testing > reports/xcode-build.log 2>&1
xcrun simctl uninstall "$SIMULATOR_UDID" local.psycho.TapTests.xctrunner 2>/dev/null || true
xcrun simctl uninstall "$SIMULATOR_UDID" local.psycho.TrainerTestHost 2>/dev/null || true
xcodebuild -project tests/ios/TapTests.xcodeproj -scheme TapTests -destination "platform=iOS Simulator,id=$SIMULATOR_UDID" -derivedDataPath /tmp/psycho-ios-build -parallel-testing-enabled NO test-without-building > reports/xcode-touch.log 2>&1 &
touch_driver_pid=$!
trap 'kill "$touch_driver_pid" 2>/dev/null || true' EXIT
NATIVE_TAPS=1 python3 tests/iphone.py
wait "$touch_driver_pid"
