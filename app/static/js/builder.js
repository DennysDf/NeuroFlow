/* Form Builder runtime: SortableJS reorder + inspector panel */
(function () {
  const csrfToken = () =>
    document.querySelector('meta[name="csrf-token"]').getAttribute("content");

  function initSortable() {
    const list = document.getElementById("field-list");
    if (!list || list.dataset.sortableInit === "1") return;
    list.dataset.sortableInit = "1";
    new Sortable(list, {
      animation: 150,
      handle: ".cursor-move",
      onEnd: () => {
        const order = Array.from(list.querySelectorAll("li")).map(
          (li) => li.dataset.fieldId
        );
        const fd = new FormData();
        order.forEach((id) => fd.append("order[]", id));
        fetch(window.NEUROFLOW_FORM_BUILDER.reorderUrl, {
          method: "POST",
          headers: { "X-CSRFToken": csrfToken() },
          body: fd,
        });
      },
    });
  }

  document.body.addEventListener("htmx:afterSwap", initSortable);
  document.addEventListener("DOMContentLoaded", initSortable);

  const HAS_OPTIONS = new Set(["SINGLE_CHOICE", "MULTI_CHOICE", "DROPDOWN"]);

  window.NEUROFLOW_openInspector = function (
    fieldId,
    updateUrl,
    deleteUrl,
    type,
    label,
    helpText,
    required,
    options
  ) {
    const inspector = document.getElementById("inspector");
    const optionsBlock = HAS_OPTIONS.has(type)
      ? `<div>
           <div class="label">Opções</div>
           <div id="opts-${fieldId}" class="space-y-2">
             ${options
               .map(
                 (o) =>
                   `<input class="input" name="option_label" value="${escapeHtml(
                     o
                   )}"/>`
               )
               .join("")}
           </div>
           <button type="button" class="btn-secondary mt-2 text-xs" onclick="window.NEUROFLOW_addOption(${fieldId})">+ opção</button>
         </div>`
      : "";

    inspector.innerHTML = `
      <form hx-post="${updateUrl}" hx-target="#canvas" hx-swap="outerHTML" class="space-y-3">
        <input type="hidden" name="csrf_token" value="${csrfToken()}"/>
        <div>
          <label class="label">Rótulo</label>
          <input class="input" name="label" value="${escapeHtml(label)}" required/>
        </div>
        <div>
          <label class="label">Texto de ajuda</label>
          <input class="input" name="help_text" value="${escapeHtml(helpText || "")}"/>
        </div>
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" name="required" ${required ? "checked" : ""}/>
          Obrigatório
        </label>
        ${optionsBlock}
        <div class="flex gap-2 pt-2">
          <button class="btn-primary">Salvar</button>
          <button type="button" class="btn-danger" onclick="window.NEUROFLOW_deleteField('${deleteUrl}')">Excluir</button>
        </div>
      </form>
    `;
    if (window.htmx) window.htmx.process(inspector);
  };

  window.NEUROFLOW_addOption = function (fieldId) {
    const wrap = document.getElementById(`opts-${fieldId}`);
    if (!wrap) return;
    const input = document.createElement("input");
    input.className = "input";
    input.name = "option_label";
    input.placeholder = "Nova opção";
    wrap.appendChild(input);
    input.focus();
  };

  window.NEUROFLOW_deleteField = function (deleteUrl) {
    if (!confirm("Remover campo?")) return;
    const fd = new FormData();
    fetch(deleteUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken() },
      body: fd,
    }).then((r) => r.text()).then((html) => {
      const tmp = document.createElement("div");
      tmp.innerHTML = html;
      const newCanvas = tmp.querySelector("#canvas");
      const cur = document.getElementById("canvas");
      if (newCanvas && cur) cur.replaceWith(newCanvas);
      document.getElementById("inspector").innerHTML =
        "Selecione um campo no centro para editar suas propriedades.";
      initSortable();
    });
  };

  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
})();
