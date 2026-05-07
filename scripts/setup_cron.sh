#!/usr/bin/env bash
# Install cron jobs for DREAMCRM availability monitoring.
# Run once: bash scripts/setup_cron.sh
# Run with --remove to uninstall.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="${PROJECT_DIR}/.venv/bin/python"
PYTEST="${PROJECT_DIR}/.venv/bin/pytest"
LOG_DIR="${PROJECT_DIR}/logs"

MONITOR_CMD="cd \"${PROJECT_DIR}\" && \"${PYTHON}\" \"${SCRIPT_DIR}/availability_monitor.py\""
TESTS_CMD="cd \"${PROJECT_DIR}\" && \"${PYTEST}\" -m \"smoke or contract\" --tb=short -q"

# Cron schedule markers (used to identify our jobs on reinstall)
MONITOR_MARKER="dreamcrm-availability-monitor"
TESTS_MARKER="dreamcrm-daily-tests"

# Schedules:
#   Monitor — every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
#   Full tests — every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
MONITOR_CRON="0 */4 * * *"
TESTS_CRON="0 */6 * * *"

# -----------------------------------------------------------------------

remove_jobs() {
  echo "Removing DREAMCRM cron jobs..."
  (crontab -l 2>/dev/null | grep -v "$MONITOR_MARKER" | grep -v "$TESTS_MARKER") | crontab - || true
  echo "Done."
}

install_jobs() {
  mkdir -p "$LOG_DIR"
  echo "Installing cron jobs..."

  # Build the two new lines
  LINE_MONITOR="${MONITOR_CRON} ${MONITOR_CMD} >> \"${LOG_DIR}/availability.log\" 2>&1  # ${MONITOR_MARKER}"
  LINE_TESTS="${TESTS_CRON} ${TESTS_CMD} >> \"${LOG_DIR}/daily_tests.log\" 2>&1  # ${TESTS_MARKER}"

  # Strip old entries, append fresh ones
  (
    crontab -l 2>/dev/null | grep -v "$MONITOR_MARKER" | grep -v "$TESTS_MARKER"
    echo "$LINE_MONITOR"
    echo "$LINE_TESTS"
  ) | crontab -

  echo ""
  echo "Installed successfully:"
  echo "  [every 4 h]  availability_monitor.py  →  ${LOG_DIR}/availability.log"
  echo "  [every 6 h]  pytest smoke+contract    →  ${LOG_DIR}/daily_tests.log"
  echo ""
  echo "Current crontab (our jobs):"
  crontab -l | grep -E "$MONITOR_MARKER|$TESTS_MARKER"
  echo ""
  echo "Dashboard:  ${PROJECT_DIR}/reports/availability.html"
  echo ""
  echo "Run a probe right now:"
  echo "  cd \"${PROJECT_DIR}\" && \"${PYTHON}\" scripts/availability_monitor.py"
}

# -----------------------------------------------------------------------

case "${1:-}" in
  --remove) remove_jobs ;;
  *)        install_jobs ;;
esac
