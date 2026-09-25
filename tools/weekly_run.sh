#!/bin/sh
# Weekly unattended run of /academic-job-search (launchd com.unarylab.academic-job-search,
# Wednesdays 23:59 local time, until 2027-01-31).
#
# Claude runs the skill headless with a fixed tool allowlist and no git access; this
# script then commits entries.json and output/ and pushes to main, which triggers the
# GitHub Pages workflow that publishes the newest report, and emails the site link.
# Mail goes through the SMTP config of the paper-reminder workflow (remind.send_email).
#
# Run by hand:  tools/weekly_run.sh
set -u

# launchd hands us a minimal PATH that omits Homebrew, conda, and ~/.local/bin.
PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/anaconda3/bin:$PATH"
export PATH

LABEL="com.unarylab.academic-job-search"
SITE="https://www.unarylab.com/academic-job-search/"
MAILER="$HOME/Projects/unarylab-claude-marketplace/unarylab-research/skills/paper-reminder/workflow"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$HOME/Library/Logs/academic-job-search"
DATE=$(date +%Y-%m-%d)
LOG="$LOGDIR/$DATE.log"
mkdir -p "$LOGDIR"
exec >> "$LOG" 2>&1
echo "===== run $(date '+%Y-%m-%d %H:%M:%S') ====="

mail() {  # mail <comma-separated recipients> <subject> <body>
    /usr/bin/python3 - "$1" "$2" "$3" "$MAILER" <<'EOF'
import sys
to, subject, body, mailer = sys.argv[1:5]
sys.path.insert(0, mailer)
from remind import load_config, send_email
cfg, err = load_config()
if cfg is None:
    sys.exit("mail skipped: " + err)
print("mailed", send_email(cfg, subject, body, [a.strip() for a in to.split(",")]))
EOF
}

fail() {
    echo "FAILED: $1"
    mail "$ALERT_TO" "Faculty job search run FAILED $DATE" "$1

Log: $LOG"
    exit 1
}

if [ "$(date +%Y%m%d)" -gt 20270131 ]; then
    echo "past 2027-01-31: removing $LABEL"
    rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
    launchctl bootout "gui/$(id -u)/$LABEL"
    exit 0
fi

cd "$REPO" || fail "repo not found at $REPO"
git pull --ff-only origin main || fail "git pull failed"

PROMPT="/academic-job-search Run date: $DATE (use this date for --date, checked fields, and the report file name even if the clock passes midnight). This is an unattended run: nobody will answer questions, so apply the skill's rules and make the judgment calls yourself. Keep all scratch files in your scratchpad. Do not run git. If an agent fails on an API error, resume it once; if it fails again, record its lists as gaps and continue. End your final message with one line exactly in the form: SUMMARY: <N> entries, <M> new, <G> gap universities"

claude -p "$PROMPT" --model opus --permission-mode dontAsk \
    --allowedTools Bash Read Write Edit Glob Grep Agent WebSearch WebFetch Skill SendMessage TaskStop ToolSearch
status=$?
echo "claude exit=$status"
[ "$status" -eq 0 ] || fail "claude -p exited with status $status"

SUMMARY=$(grep -o 'SUMMARY: .*' "$LOG" | tail -1 | sed 's/^SUMMARY: //')
[ -n "$SUMMARY" ] || SUMMARY="weekly run"
git add .claude/skills/academic-job-search/entries.json output/
if git diff --cached --quiet; then
    echo "no changes to commit"
    exit 0
fi
git commit -m "$DATE report: $SUMMARY" || fail "git commit failed"
git push origin main || fail "git push failed"

mail "$RECIPIENTS" "Faculty job report $DATE: $SUMMARY" "The weekly faculty job search finished on $DATE.

$SUMMARY

Report: $SITE
(The site updates a minute or two after this email.)"
echo "done"
