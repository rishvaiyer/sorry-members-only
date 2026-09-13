const navigationTargets = [...document.querySelectorAll("[data-nav-target]")];
const pageLinks = [...document.querySelectorAll(".page-nav a")];
const sections = [...document.querySelectorAll(".doc-section, .page-header")];
const navigationAliases = { "system-overview": "overview" };

function setActive(targetId) {
  const navigationTarget = navigationAliases[targetId] || targetId;
  navigationTargets.forEach((link) => {
    const active = link.dataset.navTarget === navigationTarget;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });

  pageLinks.forEach((link) => {
    link.classList.toggle("is-current", link.getAttribute("href") === `#${targetId}`);
  });
}

const observer = new IntersectionObserver((entries) => {
  const visible = entries
    .filter((entry) => entry.isIntersecting)
    .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
  if (visible[0]) setActive(visible[0].target.id);
}, { rootMargin: "-12% 0px -70% 0px", threshold: [0, 1] });

sections.forEach((section) => observer.observe(section));

window.addEventListener("hashchange", () => {
  const target = document.getElementById(window.location.hash.slice(1));
  if (target) setActive(target.id);
});

navigationTargets.forEach((link) => {
  link.addEventListener("click", () => setActive(link.dataset.navTarget));
});

setActive(window.location.hash.slice(1) || "overview");
