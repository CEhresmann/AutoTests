#!/usr/bin/env bash
# One-command server setup for DREAMCRM dashboard.
# Tested on Ubuntu 22.04 / Debian 12.
#
# Usage:
#   bash scripts/install_server.sh [--project-dir /srv/dreamcrm-tests]
#
# What it does:
#   1. Installs python3.11, python3.11-venv, nginx, git (if missing)
#   2. Creates project directory and sets up Python venv
#   3. Installs Python dependencies
#   4. Creates logs/ directory
#   5. Configures nginx (copies the config, enables the site)
#   6. Installs cron jobs (4h availability probe + 6h pytest)
#   7. Runs the first availability probe to generate reports/
#   8. Prints the dashboard URL

set -euo pipefail

# -----------------------------------------------------------------------
# Defaults
# -----------------------------------------------------------------------
PROJECT_DIR="/srv/dreamcrm-tests"
NGINX_CONF_NAME="dreamcrm-dashboard"

# -----------------------------------------------------------------------
# Arg parsing
# -----------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------
info()  { echo "[INFO]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
fatal() { echo "[ERROR] $*" >&2; exit 1; }

require_root() {
  [[ $EUID -eq 0 ]] || fatal "This step requires root. Run with sudo or as root."
}

# -----------------------------------------------------------------------
# Step 1 — System packages
# -----------------------------------------------------------------------
info "Checking system packages..."
if command -v apt-get &>/dev/null; then
  MISSING=()
  for pkg in python3.11 python3.11-venv nginx git; do
    dpkg -s "$pkg" &>/dev/null 2>&1 || MISSING+=("$pkg")
  done
  if [[ ${#MISSING[@]} -gt 0 ]]; then
    info "Installing: ${MISSING[*]}"
    require_root
    apt-get update -qq
    apt-get install -y -qq "${MISSING[@]}"
    ok "Packages installed."
  else
    ok "All system packages already present."
  fi
else
  warn "apt-get not found — skipping system package install. Ensure python3.11, nginx, git are available."
fi

# -----------------------------------------------------------------------
# Step 2 — Project directory
# -----------------------------------------------------------------------
if [[ "$PROJECT_DIR" != "$SOURCE_DIR" ]]; then
  info "Setting up project at $PROJECT_DIR..."
  mkdir -p "$PROJECT_DIR"
  if [[ -d "$SOURCE_DIR/.git" ]]; then
    rsync -a --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
          "$SOURCE_DIR/" "$PROJECT_DIR/"
    ok "Project files synced to $PROJECT_DIR."
  else
    warn "Source is not a git repo — copy files manually to $PROJECT_DIR and re-run."
  fi
else
  info "Using current directory as project dir: $PROJECT_DIR"
fi

# -----------------------------------------------------------------------
# Step 3 — Python venv + dependencies
# -----------------------------------------------------------------------
PYTHON="${PROJECT_DIR}/.venv/bin/python"
PIP="${PROJECT_DIR}/.venv/bin/pip"

if [[ ! -f "$PYTHON" ]]; then
  info "Creating Python venv..."
  python3.11 -m venv "${PROJECT_DIR}/.venv"
  ok "Venv created."
fi

info "Installing Python dependencies..."
"$PIP" install --quiet -e "${PROJECT_DIR}[dev]" 2>/dev/null \
  || "$PIP" install --quiet -r "${PROJECT_DIR}/requirements.txt" 2>/dev/null \
  || "$PIP" install --quiet \
       "jsonschema>=4.23.0,<5.0.0" \
       "pytest>=8.3.0,<9.0.0" \
       "python-dotenv>=1.0.1,<2.0.0" \
       "pyyaml>=6.0,<7.0" \
       "requests>=2.32.0,<3.0.0"
ok "Python dependencies installed."

# -----------------------------------------------------------------------
# Step 4 — .env file
# -----------------------------------------------------------------------
ENV_FILE="${PROJECT_DIR}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "${PROJECT_DIR}/.env.example" ]]; then
    cp "${PROJECT_DIR}/.env.example" "$ENV_FILE"
    warn ".env created from .env.example — fill in API keys before running tests!"
  else
    warn ".env not found — create it manually at $ENV_FILE"
  fi
else
  ok ".env already exists."
fi
chmod 600 "$ENV_FILE" 2>/dev/null || true

# -----------------------------------------------------------------------
# Step 5 — Logs directory
# -----------------------------------------------------------------------
mkdir -p "${PROJECT_DIR}/logs"
ok "Logs directory ready: ${PROJECT_DIR}/logs"

# -----------------------------------------------------------------------
# Step 6 — nginx
# -----------------------------------------------------------------------
NGINX_CONF_SRC="${PROJECT_DIR}/nginx/dreamcrm-dashboard.conf"
NGINX_AVAILABLE="/etc/nginx/sites-available/${NGINX_CONF_NAME}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${NGINX_CONF_NAME}"

if command -v nginx &>/dev/null; then
  info "Configuring nginx..."

  # Patch the root path in the config to the actual project dir
  TMP_CONF="$(mktemp)"
  sed "s|/srv/dreamcrm-tests|${PROJECT_DIR}|g" "$NGINX_CONF_SRC" > "$TMP_CONF"

  if [[ $EUID -eq 0 ]]; then
    cp "$TMP_CONF" "$NGINX_AVAILABLE"
    ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
    # Remove default nginx site if it conflicts on port 80
    [[ -f /etc/nginx/sites-enabled/default ]] && rm -f /etc/nginx/sites-enabled/default && warn "Removed default nginx site."
    nginx -t && systemctl reload nginx
    ok "nginx configured and reloaded."
  else
    warn "Not running as root — cannot configure nginx automatically."
    warn "Run manually:"
    warn "  sudo cp $TMP_CONF $NGINX_AVAILABLE"
    warn "  sudo ln -s $NGINX_AVAILABLE $NGINX_ENABLED"
    warn "  sudo nginx -t && sudo systemctl reload nginx"
  fi
  rm -f "$TMP_CONF"
else
  warn "nginx not found — skipping web server setup."
fi

# -----------------------------------------------------------------------
# Step 7 — Cron jobs
# -----------------------------------------------------------------------
info "Installing cron jobs..."
bash "${PROJECT_DIR}/scripts/setup_cron.sh"
ok "Cron jobs installed."

# -----------------------------------------------------------------------
# Step 8 — First probe run
# -----------------------------------------------------------------------
info "Running first availability probe..."
cd "$PROJECT_DIR"
"$PYTHON" scripts/availability_monitor.py || warn "Some services may be down — check output above."
ok "First probe complete. Reports generated in ${PROJECT_DIR}/reports/"

# -----------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  DREAMCRM Dashboard installed successfully!"
echo ""

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<server-ip>")
echo "  Dashboard URL:     http://${SERVER_IP}/"
echo "  Coverage report:   http://${SERVER_IP}/index.html"
echo ""
echo "  Project dir:  ${PROJECT_DIR}"
echo "  Reports dir:  ${PROJECT_DIR}/reports/"
echo "  Logs:         ${PROJECT_DIR}/logs/"
echo ""
echo "  Next steps:"
echo "    1. Fill in API keys in ${ENV_FILE}"
echo "    2. Set DREAMCRM_RUN_FULL_OPENAPI_TESTS=1 in .env"
echo "    3. Run: $PYTHON scripts/availability_monitor.py"
echo "    4. Run: ${PROJECT_DIR}/.venv/bin/pytest -m smoke"
if command -v certbot &>/dev/null; then
  echo "    5. HTTPS: sudo certbot --nginx -d your-domain.ru"
fi
echo "============================================================"
