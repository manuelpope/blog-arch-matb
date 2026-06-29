// Mermaid: enable fullscreen + client-side fallback for non-rendered diagrams
document.addEventListener("DOMContentLoaded", function () {
  setupFullscreen();
  setupFallbackRender();
});

function setupFullscreen() {
  const modal = ensureModal();

  document.querySelectorAll(".mermaid-diagram").forEach(function (diagram) {
    diagram.addEventListener("click", function () {
      const svg = diagram.querySelector("svg");
      if (!svg) return;
      const clone = svg.cloneNode(true);
      clone.style.cssText = "";
      modal.querySelector(".modal-content").innerHTML = "";
      modal.querySelector(".modal-content").appendChild(clone);
      modal.classList.add("active");
      document.body.style.overflow = "hidden";
    });
  });

  modal.addEventListener("click", function (e) {
    if (e.target === modal || e.target.classList.contains("mermaid-modal-close")) {
      closeModal(modal);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("active")) {
      closeModal(modal);
    }
  });
}

function ensureModal() {
  let modal = document.querySelector(".mermaid-modal");
  if (modal) return modal;
  modal = document.createElement("div");
  modal.className = "mermaid-modal";
  modal.innerHTML =
    '<button class="mermaid-modal-close" aria-label="Close">×</button>' +
    '<div class="modal-content"></div>';
  document.body.appendChild(modal);
  return modal;
}

function closeModal(modal) {
  modal.classList.remove("active");
  document.body.style.overflow = "";
}

function setupFallbackRender() {
  // Only if there's a fallback (un-rendered) mermaid diagram
  if (typeof mermaid === "undefined") return;
  const fallback = document.querySelector('.mermaid-diagram[data-fallback="true"]');
  if (!fallback) return;

  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "loose",
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    themeVariables: {
      primaryColor: "#27272a",
      primaryTextColor: "#fafafa",
      primaryBorderColor: "#3f3f46",
      lineColor: "#a1a1aa",
      secondaryColor: "#1f1f23",
      tertiaryColor: "#1a1a1a",
    },
  });

  const pre = fallback.querySelector("pre.mermaid");
  if (!pre) return;
  const code = pre.textContent;
  mermaid
    .render("mermaid-fallback", code)
    .then(function (result) {
      fallback.innerHTML = result.svg;
      fallback.removeAttribute("data-fallback");
    })
    .catch(function () {
      // Leave as-is
    });
}
