#!/bin/sh
# Unattended run of /academic-job-search (launchd com.unarylab.academic-job-search, Mon/Wed/Fri
# at 20:00 local time, until the date in tools/end_date). Each fire uses the API key in
# tools/api_key; if that key is missing or fails a preflight call, only the Wednesday fire runs,
# on the subscription login.
#
# Claude runs the skill headless with a fixed tool allowlist and no git access; this
# script then commits entries.json and output/ and pushes to main, which triggers the
# GitHub Pages workflow that publishes the newest report, and emails the site link.
# SMTP credentials and recipient lists come from tools/mail.json (gitignored): smtp_host,
# smtp_port, use_ssl, username, password, from_addr, recipients [..], alert_to [..].
# tools/api_key (gitignored): line 1 the API key, line 2 the workspace ID (wrkspc_...,
# required for organization-scoped keys).
#
# Run by hand:  tools/weekly_run.sh
set -u

# launchd hands us a minimal PATH that omits Homebrew, conda, and ~/.local/bin.
PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/anaconda3/bin:$PATH"
export PATH

LABEL="com.unarylab.academic-job-search"
SITE="https://www.unarylab.com/academic-job-search/"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$HOME/Library/Logs/academic-job-search"
DATE=$(date +%Y-%m-%d)
LOG="$LOGDIR/$DATE.log"
mkdir -p "$LOGDIR"
exec >> "$LOG" 2>&1
echo "===== run $(date '+%Y-%m-%d %H:%M:%S') ====="

mail() {  # mail <recipients|alert_to> <subject> <body>
    /usr/bin/python3 - "$1" "$2" "$3" "$REPO/tools/mail.json" <<'EOF'
import json, smtplib, sys
from email.mime.text import MIMEText
key, subject, body, path = sys.argv[1:5]
cfg = json.load(open(path))
msg = MIMEText(body, "plain", "utf-8")
msg["Subject"], msg["From"], msg["To"] = subject, cfg["from_addr"], ", ".join(cfg[key])
port = int(cfg["smtp_port"])
if cfg.get("use_ssl", port == 465):
    server = smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=30)
else:
    server = smtplib.SMTP(cfg["smtp_host"], port, timeout=30)
    server.starttls()
try:
    server.login(cfg["username"], cfg["password"])
    server.sendmail(msg["From"], cfg[key], msg.as_string())
finally:
    server.quit()
print("mailed", cfg[key])
EOF
}

fail() {
    echo "FAILED: $1"
    mail alert_to "Faculty job search run FAILED $DATE" "$1

Log: $LOG"
    exit 1
}

END=$(tr -d - < "$REPO/tools/end_date" 2>/dev/null)   # YYYY-MM-DD; missing or empty file: run forever
if [ -n "$END" ] && [ "$(date +%Y%m%d)" -gt "$END" ]; then
    echo "past $END: removing $LABEL"
    rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
    launchctl bootout "gui/$(id -u)/$LABEL"
    exit 0
fi

cd "$REPO" || fail "repo not found at $REPO"

AUTH=subscription
if [ -r "$REPO/tools/api_key" ]; then
    export ANTHROPIC_API_KEY="$(sed -n 1p "$REPO/tools/api_key")"
    export ANTHROPIC_CUSTOM_HEADERS="anthropic-workspace-id: $(sed -n 2p "$REPO/tools/api_key")"
    if claude -p "reply with exactly: ok" --model opus >/dev/null 2>&1; then
        AUTH=api
    else
        echo "API key preflight failed"
        unset ANTHROPIC_API_KEY ANTHROPIC_CUSTOM_HEADERS
    fi
fi
if [ "$AUTH" != api ] && [ "$(date +%u)" -ne 3 ]; then
    echo "no working API key; next subscription run is Wednesday"; exit 0
fi
echo "auth=$AUTH"
git pull --ff-only origin main || fail "git pull failed"

PROMPT="/academic-job-search Run date: $DATE (use this date for --date, checked fields, and the report file name even if the clock passes midnight). This is an unattended run: nobody will answer questions, so apply the skill's rules and make the judgment calls yourself. Keep all scratch files in your scratchpad. Do not run git. If an agent fails on an API error, resume it once; if it fails again, record its lists as gaps and continue. Never end your turn while any agent is still running: this is a headless run and the process exits about 10 minutes after your last turn, so wait with exactly this Bash command, run with run_in_background (it works in zsh and bash): until [ \"\$(ls <run-dir>/<glob> 2>/dev/null | wc -l)\" -ge <N> ]; do sleep 60; done, where <run-dir> is the scratchpad run directory, <glob> matches only the agent JSON files, and <N> is the number of agents dispatched; then continue. Before your final message, make sure no background Bash task or Monitor is still running, and TaskStop any that remain, because a live background task keeps this headless session open. End your final message with one line exactly in the form: SUMMARY: <N> entries, <M> new, <G> gap universities"

# The log is appended per date: read only what this run writes, not an earlier same-day run.
start=$(wc -c < "$LOG")
claude -p "$PROMPT" --model opus --permission-mode dontAsk \
    --allowedTools Bash Read Write Edit Glob Grep Agent WebSearch WebFetch Skill SendMessage TaskStop ToolSearch &
pid=$!
# A leftover background task can keep claude alive after its SUMMARY line: give it 3 minutes, then kill it.
killed=0
passes=0  # cap: 2880 x 30 s = 24 h; a run that never prints SUMMARY must not block later weeks
while kill -0 "$pid" 2>/dev/null; do
    if [ "$passes" -ge 2880 ]; then
        echo "no SUMMARY after 24 h: killing $pid"
        pkill -P "$pid"; kill "$pid"; sleep 10; kill -9 "$pid" 2>/dev/null
        fail "claude -p ran 24 h without a SUMMARY line"
    fi
    passes=$((passes + 1))
    if tail -c +$((start + 1)) "$LOG" | grep -q 'SUMMARY: '; then
        n=0
        while kill -0 "$pid" 2>/dev/null && [ "$n" -lt 6 ]; do sleep 30; n=$((n + 1)); done
        if kill -0 "$pid" 2>/dev/null; then
            echo "SUMMARY printed but claude still running: killing $pid"
            pkill -P "$pid"
            kill "$pid"
            sleep 10
            kill -9 "$pid" 2>/dev/null
            killed=1
        fi
        break
    fi
    sleep 30
done
wait "$pid"
status=$?
echo "claude exit=$status"
[ "$status" -eq 0 ] || [ "$killed" -eq 1 ] || fail "claude -p exited with status $status"

SUMMARY=$(tail -c +$((start + 1)) "$LOG" | grep -o 'SUMMARY: .*' | tail -1 | sed 's/^SUMMARY: //')
[ -n "$SUMMARY" ] || fail "claude -p exited without a SUMMARY line (idled out with agents still running?)"
git add .claude/skills/academic-job-search/entries.json output/
if git diff --cached --quiet; then
    echo "no changes to commit"
    exit 0
fi
git commit -m "$DATE report: $SUMMARY" || fail "git commit failed"
git push origin main || fail "git push failed"

mail recipients "Faculty job report $DATE: $SUMMARY" "The faculty job search finished on $DATE (auth: $AUTH).

$SUMMARY

Report: $SITE
(The site updates a minute or two after this email.)"
echo "done"
