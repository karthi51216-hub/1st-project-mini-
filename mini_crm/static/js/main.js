

// 4) navbar style on scroll
window.addEventListener("scroll", () => {
  const nav = document.getElementById("topNav");
  if (!nav) return;
  if (window.scrollY > 10) nav.classList.add("nav-scrolled");
  else nav.classList.remove("nav-scrolled");
});

// 10) custom alert/toast notification system
function showToast(msg, type="info"){
  const host = document.getElementById("toastHost");
  if(!host) return;

  const el = document.createElement("div");
  el.className = `toast align-items-center text-bg-${type} border-0 mb-2`;
  el.setAttribute("role","alert");
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  host.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: 2400 });
  t.show();
  el.addEventListener("hidden.bs.toast", ()=> el.remove());
}

if (window.__FLASH__) {
  window.__FLASH__.forEach(([cat, msg]) => {
    const map = {success:"success", danger:"danger", warning:"warning", info:"info"};
    showToast(msg, map[cat] || "info");
  });
}

// 2) show/hide password
document.addEventListener("click", (e) => {
  if (e.target.matches("[data-toggle='password']")) {
    const id = e.target.getAttribute("data-target");
    const inp = document.querySelector(id);
    if (!inp) return;
    inp.type = inp.type === "password" ? "text" : "password";
    e.target.textContent = inp.type === "password" ? "Show" : "Hide";
  }
});

// 1) Bootstrap client-side validation
(() => {
  const forms = document.querySelectorAll(".needs-validation");
  Array.from(forms).forEach(form => {
    form.addEventListener("submit", event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        showToast("Please fix validation errors", "warning");
      }
      form.classList.add("was-validated");
    }, false);
  });
})();

// 8) table sorting (simple)
function sortTable(tableId, colIndex){
  const table = document.getElementById(tableId);
  if(!table) return;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const asc = table.getAttribute("data-sort") !== "asc";
  rows.sort((a,b)=>{
    const A = a.cells[colIndex].innerText.trim().toLowerCase();
    const B = b.cells[colIndex].innerText.trim().toLowerCase();
    return asc ? A.localeCompare(B) : B.localeCompare(A);
  });
  rows.forEach(r=>tbody.appendChild(r));
  table.setAttribute("data-sort", asc ? "asc" : "desc");
}

// 9) realtime filter for product cards
function filterCards(inputId, cardSelector){
  const inp = document.getElementById(inputId);
  if(!inp) return;
  inp.addEventListener("input", ()=>{
    const q = inp.value.toLowerCase();
    document.querySelectorAll(cardSelector).forEach(card=>{
      card.style.display = card.innerText.toLowerCase().includes(q) ? "" : "none";
    });
  });
}
filterCards("productSearch", ".product-card");