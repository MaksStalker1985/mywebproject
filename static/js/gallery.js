/* Просмотр фотографий поверх страницы: ссылки a[data-gallery="группа"] на большую картинку.
 * Стрелки ←/→ и свайп листают фото группы, Esc или клик по фону закрывают.
 * Без JavaScript ссылка просто открывает картинку. */
(function () {
  "use strict";
  var box, img, caption, counter, items = [], index = 0, lastFocus = null, touchX = null;

  function build() {
    box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML =
      '<button type="button" class="lb-close" aria-label="Close">×</button>' +
      '<button type="button" class="lb-prev" aria-label="Previous">‹</button>' +
      '<figure><img alt=""><figcaption><span class="lb-caption"></span><span class="lb-counter"></span></figcaption></figure>' +
      '<button type="button" class="lb-next" aria-label="Next">›</button>';
    document.body.appendChild(box);
    img = box.querySelector("img");
    caption = box.querySelector(".lb-caption");
    counter = box.querySelector(".lb-counter");
    box.querySelector(".lb-close").onclick = close;
    box.querySelector(".lb-prev").onclick = function (e) { e.stopPropagation(); show(index - 1); };
    box.querySelector(".lb-next").onclick = function (e) { e.stopPropagation(); show(index + 1); };
    box.addEventListener("click", function (e) { if (e.target === box || e.target.tagName === "FIGURE") close(); });
    box.addEventListener("touchstart", function (e) { touchX = e.touches[0].clientX; }, { passive: true });
    box.addEventListener("touchend", function (e) {
      if (touchX === null) return;
      var dx = e.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    });
  }

  function show(i) {
    if (!items.length) return;
    index = (i + items.length) % items.length;
    var a = items[index], thumb = a.querySelector("img");
    img.src = a.href;
    img.alt = thumb ? thumb.alt : "";
    caption.textContent = a.getAttribute("data-caption") || "";
    counter.textContent = items.length > 1 ? (index + 1) + " / " + items.length : "";
    box.classList.toggle("lb-single", items.length < 2);
    // Подгружаем соседние фото заранее
    [index + 1, index - 1].forEach(function (j) {
      var n = items[(j + items.length) % items.length];
      if (n && n !== a) { var pre = new Image(); pre.src = n.href; }
    });
  }

  function open(a) {
    if (!box) build();
    var group = a.getAttribute("data-gallery");
    items = Array.prototype.slice.call(document.querySelectorAll('a[data-gallery="' + group + '"]'));
    lastFocus = document.activeElement;
    box.hidden = false;
    document.documentElement.classList.add("lb-open");
    show(items.indexOf(a));
    box.querySelector(".lb-close").focus();
  }

  function close() {
    box.hidden = true;
    img.removeAttribute("src");
    document.documentElement.classList.remove("lb-open");
    if (lastFocus) lastFocus.focus();
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-gallery]");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    open(a);
  });
  document.addEventListener("keydown", function (e) {
    if (!box || box.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(index + 1);
    else if (e.key === "ArrowLeft") show(index - 1);
  });
})();
