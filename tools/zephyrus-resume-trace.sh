#!/usr/bin/env bash
# Zephyrus G16 (GA605WV) resume-latency tracer.
#
#   sudo ./zephyrus-resume-trace.sh arm      # before you suspend
#   ... suspend, wait ~30s, wake, time how long the screen stays dark ...
#   sudo ./zephyrus-resume-trace.sh report   # once you are back
#
# 'arm' turns on the kernel's own PM timing output, which is off by default.
# 'report' reads the journal back and says where the time actually went: it
# separates the sleep itself from the resume, then splits the resume into the
# kernel's device work and whatever userspace did after that.
#
# The question it exists to answer: did the machine take 35 seconds to resume,
# or did it resume in 2 seconds and leave the panel dark for 33?

set -uo pipefail

# Test hook: point this at a captured journal instead of reading the live one.
JOURNAL_FILE="${JOURNAL_FILE:-}"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
note() { printf '   %s\n' "$*"; }

need_root() {
    [ "$(id -u)" -eq 0 ] && return 0
    echo "This needs root: re-run with sudo." >&2
    exit 1
}

arm() {
    need_root
    local armed=0
    for f in pm_print_times pm_debug_messages; do
        if [ -w "/sys/power/$f" ]; then
            echo 1 > "/sys/power/$f" && { note "enabled /sys/power/$f"; armed=1; }
        else
            note "MISSING /sys/power/$f (kernel built without PM debug?)"
        fi
    done
    if [ "$armed" -eq 1 ]; then
        say "Armed. Both settings reset themselves on reboot."
    else
        say "NOT armed: neither switch exists, so the report will lack the"
        note "per-device timings. The rest of it still works. Continue anyway:"
    fi
    cat <<'EOT'
   Now, in this order:

     1. Note the GPU mode you are testing (Integrated for the slow case).
     2. Suspend:  systemctl suspend
     3. Wait about 30 seconds.
     4. Wake it, and TIME IT with your phone: from pressing a key until
        the screen is actually on and usable.
     5. While the screen is still dark, type something blindly (a few
        letters into a terminal) and watch/listen: keyboard backlight,
        fans, disk. Anything that tells you the system is already alive.
     6. Back in a session:  sudo ./zephyrus-resume-trace.sh report
EOT
}

# Pull the journal for this boot as unix timestamps, which makes the gap
# arithmetic trivial. Kernel and userspace lines share one clock here, so a
# stall shows up on whichever side actually caused it.
read_journal() {
    if [ -n "$JOURNAL_FILE" ]; then
        cat "$JOURNAL_FILE"
    else
        journalctl -b -o short-unix --no-pager 2>/dev/null
    fi
}

analyse() {
    # Leads with the numbers the kernel measures itself (parsed out of its own
    # log lines) rather than with journal timestamp arithmetic. That matters:
    # while the console is suspended the kernel buffers its messages, so the
    # timestamps of lines inside the frozen window bunch up and a naive
    # "biggest gap is the sleep" guess mistakes a device stall for the sleep.
    awk '
    function numafter(s, key,   a, n, i) {
        n = split(s, a, /[ \t]+/)
        for (i = 1; i <= n; i++) if (a[i] == key) return a[i+1] + 0
        return -1
    }
    { line[NR] = $0; ts[NR] = ($1 + 0)
      if ($0 ~ /PM: suspend entry/) entry = NR
    }
    END {
        n = NR
        if (n == 0)   { print "   No journal lines read."; exit }
        if (!entry)   { print "   No \"PM: suspend entry\" in this boot -- did a suspend"
                        print "   actually happen since the last reboot?"; exit }

        slept = -1; devresume = -1; devsuspend = -1; exitn = 0; wake = 0
        for (i = entry + 1; i <= n; i++) {
            if (line[i] ~ /Timekeeping suspended for/)        slept = numafter(line[i], "for")
            if (line[i] ~ /resume of devices complete after/) devresume = numafter(line[i], "after")
            if (line[i] ~ /suspend devices took/)             devsuspend = numafter(line[i], "took")
            if (!exitn && line[i] ~ /PM: suspend exit/)       exitn = i
            if (!wake && line[i] ~ /(Waking up from system sleep|EC: interrupt unblocked|Low-power idle exit)/) wake = i
        }
        # Fall back to the largest gap only when no explicit wake marker exists.
        if (!wake) {
            best = -1
            for (i = entry + 1; i <= n; i++) { d = ts[i] - ts[i-1]; if (d > best) { best = d; wake = i } }
            fellback = 1
        }

        print  "   --- what the kernel measured (authoritative) ---"
        if (devsuspend >= 0) printf "   suspending devices  : %8.3f s\n", devsuspend
        if (slept >= 0)      printf "   actually asleep     : %8.3f s\n", slept
        if (devresume >= 0)  printf "   RESUMING DEVICES    : %8.3f s   <-- kernel side\n", devresume/1000
        else                 print  "   resuming devices    :  not logged (was \"arm\" run first?)"
        if (exitn && exitn < n) printf "   userspace after exit: %8.3f s   <-- everything after the kernel was done\n", ts[n] - ts[exitn]
        if (exitn) printf "   whole cycle         : %8.3f s  (suspend entry -> last line)\n", ts[n] - ts[entry]

        print ""
        print "   --- read it like this ---"
        print "   Compare the two arrows above against the time YOU measured with"
        print "   your phone, from keypress to a usable screen:"
        print "     * kernel side is big  -> a device is blocking on resume."
        print "     * both small, screen still dark for ~30s -> the machine was"
        print "       already up. That is a display/backlight bug, not a resume bug."
        print "     * userspace is big    -> a sleep hook or the session, see 4."

        print ""
        printf "   --- biggest journal gaps after the wake marker%s ---\n", (fellback ? " (INFERRED, treat with care)" : "")
        cnt = 0
        for (i = wake + 1; i <= n; i++) {
            d = ts[i] - ts[i-1]
            if (d >= 0.10) { gd[cnt] = d; gi[cnt] = i; cnt++ }
        }
        for (a = 0; a < cnt; a++) {
            b2 = a
            for (b = a + 1; b < cnt; b++) if (gd[b] > gd[b2]) b2 = b
            t = gd[a]; gd[a] = gd[b2]; gd[b2] = t
            t = gi[a]; gi[a] = gi[b2]; gi[b2] = t
        }
        if (cnt == 0) print "   (nothing over 100ms)"
        for (a = 0; a < cnt && a < 20; a++) {
            i = gi[a]; msg = line[i]; sub(/^[0-9.]+ /, "", msg)
            printf "   %7.3fs  +%6.3fs  %s\n", gd[a], ts[i] - ts[wake], substr(msg, 1, 150)
        }
        print "   (timestamps inside the frozen window are buffered and bunch up;"
        print "    section 2 below is the trustworthy per-device view)"

        print ""
        print "   --- PM milestones ---"
        for (i = entry; i <= n; i++) {
            if (line[i] ~ /(resume of devices complete|resume devices took|suspend devices took|Timekeeping suspended|Restarting tasks|suspend exit|suspend entry|Waking up from system sleep|Finishing wakeup)/) {
                msg = line[i]; sub(/^[0-9.]+ /, "", msg)
                off = ts[i] - ts[wake]
                printf "   %s%6.3fs  %s\n", (off < 0 ? "-" : "+"), (off < 0 ? -off : off), substr(msg, 1, 150)
            }
        }
    }'
}

slowest_devices() {
    # pm_print_times logs one line per device callback. Only resume-side
    # phases matter here, and only the slow ones.
    grep -E 'call .*returned .* after [0-9]+ usecs' \
        | awk '{
            for (i = 1; i <= NF; i++) if ($i == "after") { us = $(i+1) + 0; break }
            if (us >= 100000) printf "   %8.3fs  %s\n", us/1000000, substr($0, index($0, "call"), 140)
          }' \
        | sort -rn | head -25
}

report() {
    local jf; jf="$(mktemp)"
    read_journal > "$jf"
    if [ ! -s "$jf" ]; then
        echo "Could not read the journal. Re-run with sudo." >&2
        rm -f "$jf"; exit 1
    fi

    say "1. Where the time went"
    analyse < "$jf"

    say "2. Slowest device resume callbacks (>100ms)"
    local slow; slow="$(slowest_devices < "$jf")"
    if [ -n "$slow" ]; then
        printf '%s\n' "$slow"
    else
        note "(none, or pm_print_times was not armed before the suspend)"
    fi

    say "3. Display / PCI / ACPI complaints this boot"
    local moans
    moans="$(grep -EI 'flip_done|[Dd][Mm][Uu][Bb]|DMCUB|[Pp][Ss][Rr][ _-]|[Rr]eplay|\<IPS\>|link training|DP AUX|[Aa][Uu][Xx].*timeout|atombios|amdgpu.*([Ee]rror|timeout|timed out|failed)|pcieport.*(link|not set|timeout)|Data Link Layer|ACPI.*([Ee]rror|timeout|failed)|nvidia.*([Ee]rror|timeout)' "$jf" \
        | sed 's/^[0-9.]* /   /' | tail -40)"
    if [ -n "$moans" ]; then printf '%s\n' "$moans"; else note "(clean)"; fi

    say "4. Userspace sleep hooks"
    if [ -n "$JOURNAL_FILE" ]; then
        note "(skipped: reading from a file)"
    else
        journalctl -b -u systemd-suspend.service -o short-unix --no-pager 2>/dev/null \
            | sed 's/^[0-9.]* /   /' | tail -25 || note "(none)"
        note ""
        note "sleep hook scripts present:"
        ls -1 /usr/lib/systemd/system-sleep/ /etc/systemd/system-sleep/ 2>/dev/null | sed 's/^/     /'
    fi

    say "5. Machine state"
    note "kernel      : $(uname -r)"
    note "product     : $(cat /sys/class/dmi/id/product_name 2>/dev/null)"
    note "mem_sleep   : $(cat /sys/power/mem_sleep 2>/dev/null)"
    note "cmdline     : $(cat /proc/cmdline 2>/dev/null)"
    local a=/sys/class/firmware-attributes/asus-armoury/attributes
    note "dgpu_disable: $(cat $a/dgpu_disable/current_value 2>/dev/null || echo n/a)"
    note "gpu_mux_mode: $(cat $a/gpu_mux_mode/current_value 2>/dev/null || echo n/a)"
    note "backlights  : $(ls /sys/class/backlight/ 2>/dev/null | tr '\n' ' ')"
    note "GPUs on bus :"
    lspci -nn 2>/dev/null | grep -Ei 'vga|3d controller|display' | sed 's/^/     /' \
        || note "     (lspci unavailable)"
    note "modules     : $(lsmod 2>/dev/null | awk '/^(nvidia|amdgpu|nvidia_wmi_ec_backlight|asus_wmi|asus_nb_wmi|asus_armoury)/ {print $1}' | tr '\n' ' ')"

    say "6. Suspend statistics"
    for f in /sys/power/suspend_stats/*; do
        [ -f "$f" ] && note "$(basename "$f"): $(cat "$f" 2>/dev/null | head -1)"
    done
    if [ -r /sys/kernel/debug/amd_pmc/s0ix_stats ]; then
        note "amd_pmc s0ix_stats:"
        sed 's/^/     /' /sys/kernel/debug/amd_pmc/s0ix_stats 2>/dev/null
    else
        note "amd_pmc s0ix_stats: not readable (need root, or debugfs not mounted)"
    fi

    rm -f "$jf"
    say "Done. Paste sections 1-3 back and we can read it together."
}

case "${1:-report}" in
    arm)    arm ;;
    report) report ;;
    *)      echo "usage: $0 {arm|report}" >&2; exit 2 ;;
esac
