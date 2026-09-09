/*
 * Navbar CachyOS/Bazzite switcher.
 *
 * Hextra syncs same-named tab groups through localStorage: every distro tab on
 * the site is named "CachyOS" or "Bazzite" in that order, so the choice lives in
 * localStorage["hextra-tab-CachyOS%2CBazzite"] as "0" or "1". This writes that
 * key and reloads, which flips every synced tab on every page at once. The
 * companion "zephyrus-distro" key only exists so the control can show the right
 * option as active before any tab group has rendered.
 *
 * A page that belongs to one distribution sets <meta name="page-distro">. If it
 * also names its counterpart in <meta name="distro-page-cachyos|bazzite">, the
 * switch navigates there instead of reloading in place.
 */
(function () {
  "use strict";

  var TAB_KEY = "hextra-tab-CachyOS%2CBazzite";
  var PREF_KEY = "zephyrus-distro";
  var ORDER = ["cachyos", "bazzite"];

  function read(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function write(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {
      /* private mode, blocked storage: the tab default still applies */
    }
  }

  function currentDistro() {
    var idx = parseInt(read(TAB_KEY), 10);
    if (idx === 0 || idx === 1) {
      return ORDER[idx];
    }
    return read(PREF_KEY) === "bazzite" ? "bazzite" : "cachyos";
  }

  function meta(name) {
    var el = document.querySelector('meta[name="' + name + '"]');
    return el ? el.getAttribute("content") : null;
  }

  function choose(distro) {
    var idx = ORDER.indexOf(distro);
    if (idx < 0) {
      return;
    }
    write(TAB_KEY, String(idx));
    write(PREF_KEY, distro);

    var counterpart = meta("distro-page-" + distro);
    if (counterpart && counterpart !== location.pathname) {
      location.assign(counterpart);
    } else {
      location.reload();
    }
  }

  function decorate() {
    var current = currentDistro();

    document
      .querySelectorAll("[data-distro-switch] .distro-switch-option")
      .forEach(function (btn) {
        var active = btn.getAttribute("data-distro") === current;
        btn.setAttribute("aria-pressed", active ? "true" : "false");
        btn.classList.toggle("is-active", active);
      });

    var pageDistro = meta("page-distro");
    document.querySelectorAll("[data-distro-note]").forEach(function (note) {
      var noteFor = note.getAttribute("data-distro-note") || pageDistro;
      note.classList.toggle("is-mismatch", noteFor !== current);
    });
  }

  document.addEventListener("click", function (e) {
    var btn =
      e.target.closest &&
      e.target.closest("[data-distro-switch] .distro-switch-option");
    if (!btn) {
      return;
    }
    e.preventDefault();
    choose(btn.getAttribute("data-distro"));
  });

  document.addEventListener("keydown", function (e) {
    var btn =
      e.target.closest &&
      e.target.closest("[data-distro-switch] .distro-switch-option");
    if (!btn || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) {
      return;
    }
    e.preventDefault();
    choose(btn.getAttribute("data-distro") === "cachyos" ? "bazzite" : "cachyos");
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
})();
