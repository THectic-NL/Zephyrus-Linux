/*
 * Navbar CachyOS/Bazzite switcher + distro-scoped sidebar.
 *
 * The docs split into docs/cachyos/** and docs/bazzite/** (mirrored file names)
 * plus shared sections. `<html data-distro>` is set before paint in
 * custom/head-end.html; this script wires the control and keeps the value in
 * sync.
 *
 *   - On a page under /docs/<distro>/…  the switch swaps the segment and
 *     navigates to the counterpart (same file name in the other tree).
 *   - On a shared page it stores the choice, updates <html data-distro> and
 *     re-filters the sidebar in place — no navigation.
 */
(function () {
  "use strict";

  var PREF_KEY = "zephyrus-distro";
  var DISTROS = ["cachyos", "bazzite"];
  var RE = /\/docs\/(cachyos|bazzite)\//;

  function read() {
    try {
      return localStorage.getItem(PREF_KEY);
    } catch (e) {
      return null;
    }
  }

  function store(distro) {
    try {
      localStorage.setItem(PREF_KEY, distro);
      /* Keep Hextra's synced tab groups in step: any {{< tabs >}} still named
         CachyOS/Bazzite on a shared page follows the same choice. */
      localStorage.setItem("hextra-tab-CachyOS%2CBazzite", String(DISTROS.indexOf(distro)));
    } catch (e) {
      /* private mode: the page still works, the choice just won't persist */
    }
  }

  function pageDistro() {
    var m = location.pathname.match(RE);
    return m ? m[1] : null;
  }

  function current() {
    return (
      pageDistro() ||
      (DISTROS.indexOf(read()) !== -1 ? read() : null) ||
      document.documentElement.getAttribute("data-distro") ||
      "cachyos"
    );
  }

  function choose(distro) {
    if (DISTROS.indexOf(distro) === -1 || distro === current()) {
      closeMenu();
      return;
    }
    store(distro);

    var here = pageDistro();
    if (here) {
      location.assign(location.pathname.replace(RE, "/docs/" + distro + "/"));
      return;
    }
    document.documentElement.setAttribute("data-distro", distro);
    decorate();
    closeMenu();
  }

  /* ---- sidebar: drop the non-active distro section on shared pages ---- */

  function filterSidebar(distro) {
    var other = distro === "cachyos" ? "bazzite" : "cachyos";
    document
      .querySelectorAll('.hextra-sidebar-container a[href*="/docs/' + other + '/"]')
      .forEach(function (a) {
        var li = a.closest("li");
        if (li) {
          li.hidden = true;
        }
      });
    document
      .querySelectorAll('.hextra-sidebar-container a[href*="/docs/' + distro + '/"]')
      .forEach(function (a) {
        var li = a.closest("li");
        if (li) {
          li.hidden = false;
        }
      });
  }

  /* ---- control state ---- */

  function decorate() {
    var cur = current();

    document.querySelectorAll("[data-distro-current]").forEach(function (el) {
      el.textContent = cur === "bazzite" ? "Bazzite" : "CachyOS";
    });
    document.querySelectorAll("[data-distro-switch] .distro-switch-option").forEach(function (btn) {
      var on = btn.getAttribute("data-distro") === cur;
      btn.classList.toggle("is-active", on);
      btn.setAttribute("aria-current", on ? "true" : "false");
    });
    document.querySelectorAll("[data-distro-note]").forEach(function (note) {
      note.classList.toggle("is-mismatch", note.getAttribute("data-distro-note") !== cur);
    });

    filterSidebar(cur);
  }

  /* ---- menu open/close ---- */

  function menu() {
    return document.querySelector("[data-distro-switch] .distro-switch-menu");
  }
  function toggleBtn() {
    return document.querySelector("[data-distro-switch] .distro-switch-toggle");
  }

  function openMenu() {
    var m = menu();
    if (!m) return;
    m.hidden = false;
    toggleBtn().setAttribute("aria-expanded", "true");
  }
  function closeMenu() {
    var m = menu();
    if (!m) return;
    m.hidden = true;
    var b = toggleBtn();
    if (b) b.setAttribute("aria-expanded", "false");
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t.closest && t.closest("[data-distro-switch] .distro-switch-option")) {
      e.preventDefault();
      choose(t.closest(".distro-switch-option").getAttribute("data-distro"));
      return;
    }
    if (t.closest && t.closest("[data-distro-switch] .distro-switch-toggle")) {
      e.preventDefault();
      var m = menu();
      if (m && m.hidden) openMenu();
      else closeMenu();
      return;
    }
    closeMenu();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeMenu();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
})();
