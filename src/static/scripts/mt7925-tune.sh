#!/usr/bin/env bash
# MT7925 Wi-Fi performance tuning — enable/disable/status
#
# Applies (enable) or reverts (disable) a set of tweaks for the MediaTek
# MT7925 Wi-Fi 7 card, aimed at raising real-world throughput on a
# 6GHz/160MHz link. Built and measured on a ASUS ROG Zephyrus G16 GA605WV
# (CachyOS, kernel 7.2.4) against a local iperf3 server; your mileage will
# vary with AP, signal strength, and kernel version.
#
# Usage:
#   ./mt7925-tune.sh enable    # apply all tweaks
#   ./mt7925-tune.sh disable   # revert everything to stock
#   ./mt7925-tune.sh status    # show current state of each tweak
#
# Some tweaks are live (take effect immediately), others need a reboot
# because they're kernel module parameters read only at module load time.
# The script tells you which is which every time.

set -euo pipefail

MODPROBE_CONF="/etc/modprobe.d/mt7925e.conf"
NM_CONF="/etc/NetworkManager/conf.d/wifi-powersave.conf"

# AQL Best Effort (AC=2) queue limits: kernel default is 5000/12000 (us).
# Stock mac80211 default, used to revert.
AQL_STOCK_LOW=5000
AQL_STOCK_HIGH=12000
# Tuned value — raises the airtime budget so a single high-bitrate TCP
# stream doesn't starve between bursts. Trade-off: less headroom for
# low-latency traffic (calls, gaming) sharing the radio under load.
AQL_TUNED_LOW=20000
AQL_TUNED_HIGH=40000

# --- helpers -----------------------------------------------------------

wlan_iface() {
	iw dev | awk '/Interface/{print $2; exit}'
}

wlan_phy() {
	local iface phy_num
	iface="$(wlan_iface)"
	phy_num="$(iw dev "$iface" info | awk '/wiphy/{print $2; exit}')"
	echo "phy${phy_num}"
}

aql_path() {
	echo "/sys/kernel/debug/ieee80211/$(wlan_phy)/aql_txq_limit"
}

require_pkexec() {
	command -v pkexec >/dev/null 2>&1 || {
		echo "pkexec not found — this script needs it for the privileged steps." >&2
		exit 1
	}
}

# --- enable --------------------------------------------------------------

do_enable() {
	require_pkexec
	echo "=== Enabling MT7925 performance tuning ==="

	echo "[1/4] PCIe ASPM disable (mt7925e module param)"
	printf 'options mt7925e disable_aspm=1\n' | pkexec tee "$MODPROBE_CONF" >/dev/null
	echo "      -> written to $MODPROBE_CONF (needs reboot to take effect)"

	echo "[2/4] NetworkManager Wi-Fi power saving off"
	pkexec mkdir -p /etc/NetworkManager/conf.d
	printf '[connection]\nwifi.powersave = 2\n' | pkexec tee "$NM_CONF" >/dev/null
	pkexec systemctl restart NetworkManager
	echo "      -> live"

	echo "[3/4] Bluetooth off (shares the combo chip with Wi-Fi)"
	pkexec rfkill block bluetooth
	echo "      -> live"

	echo "[4/4] AQL Best Effort queue limit: ${AQL_STOCK_LOW}/${AQL_STOCK_HIGH} -> ${AQL_TUNED_LOW}/${AQL_TUNED_HIGH} us"
	local aql
	aql="$(aql_path)"
	if pkexec test -e "$aql" 2>/dev/null; then
		pkexec bash -c "echo '2 ${AQL_TUNED_LOW} ${AQL_TUNED_HIGH}' > '${aql}'"
		echo "      -> live (resets on reboot/module reload — this script re-applies it every run)"
	else
		echo "      -> $aql not found, skipped (debugfs not mounted? try: pkexec mount -t debugfs none /sys/kernel/debug)"
	fi

	echo ""
	echo "Done. LIVE now: NM powersave, Bluetooth, AQL."
	echo "REBOOT REQUIRED for: PCIe ASPM disable."
	echo "Run '$0 status' any time to check what's actually active."
}

# --- disable -------------------------------------------------------------

do_disable() {
	require_pkexec
	echo "=== Reverting to stock settings ==="

	echo "[1/4] Removing PCIe ASPM override"
	pkexec rm -f "$MODPROBE_CONF"
	echo "      -> removed (needs reboot to fully revert; module is already loaded with the tuned param)"

	echo "[2/4] Removing NetworkManager power saving override"
	pkexec rm -f "$NM_CONF"
	pkexec systemctl restart NetworkManager
	echo "      -> live"

	echo "[3/4] Bluetooth back on"
	pkexec rfkill unblock bluetooth
	echo "      -> live"

	echo "[4/4] AQL Best Effort queue limit: back to stock ${AQL_STOCK_LOW}/${AQL_STOCK_HIGH} us"
	local aql
	aql="$(aql_path)"
	if pkexec test -e "$aql" 2>/dev/null; then
		pkexec bash -c "echo '2 ${AQL_STOCK_LOW} ${AQL_STOCK_HIGH}' > '${aql}'"
		echo "      -> live"
	else
		echo "      -> $aql not found, skipped"
	fi

	echo ""
	echo "Done. REBOOT REQUIRED to fully clear the PCIe ASPM module param."
}

# --- status ---------------------------------------------------------------

do_status() {
	local iface phy aql
	iface="$(wlan_iface)"
	phy="$(wlan_phy)"
	aql="$(aql_path)"

	echo "=== MT7925 tuning status (iface: $iface, $phy) ==="
	echo ""

	echo "-- PCIe ASPM (module param, needs reboot to change) --"
	if [ -f "$MODPROBE_CONF" ]; then
		echo "config file: present ($MODPROBE_CONF)"
	else
		echo "config file: absent"
	fi
	pkexec dmesg 2>/dev/null | grep -i "mt7925e.*ASPM" | tail -1 || echo "dmesg: no ASPM line found"

	echo ""
	echo "-- NetworkManager Wi-Fi power saving --"
	if [ -f "$NM_CONF" ]; then
		echo "config file: present ($NM_CONF)"
	else
		echo "config file: absent"
	fi
	iw dev "$iface" get power_save 2>/dev/null

	echo ""
	echo "-- Bluetooth --"
	rfkill list bluetooth | grep -E "blocked"

	echo ""
	echo "-- AQL Best Effort queue limit --"
	if pkexec test -e "$aql" 2>/dev/null; then
		pkexec cat "$aql"
	else
		echo "$aql not found (debugfs not mounted?)"
	fi

	echo ""
	echo "-- Current link --"
	iw dev "$iface" link
}

# --- main -------------------------------------------------------------

case "${1:-}" in
enable) do_enable ;;
disable) do_disable ;;
status) do_status ;;
*)
	echo "Usage: $0 {enable|disable|status}" >&2
	exit 1
	;;
esac
