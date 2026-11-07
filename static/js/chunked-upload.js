/* Загрузка больших файлов по частям с индикатором прогресса, паузой и возобновлением.
 * Подключается к форме с атрибутом data-chunked-upload (адрес API, см. dashboard/uploads.py):
 * файл из поля name="file" отправляется частями, а в скрытое поле upload_id записывается id
 * готовой загрузки — при сохранении формы сервер прикрепляет файл к продукту.
 * Без JavaScript поле «файл» работает как обычно. */
(function () {
  "use strict";
  var form = document.querySelector("form[data-chunked-upload]");
  if (!form || !window.XMLHttpRequest || !window.Blob || !Blob.prototype.slice) return;
  var input = form.querySelector('input[type="file"][name="file"]');
  var hidden = form.querySelector('input[name="upload_id"]');
  if (!input || !hidden) return;

  var T = {};
  try { T = JSON.parse(document.getElementById("upload-i18n").textContent); } catch (e) {}
  function t(key, fallback) { return T[key] || fallback; }

  var base = form.getAttribute("data-chunked-upload");
  var csrf = (form.querySelector('input[name="csrfmiddlewaretoken"]') || {}).value || "";

  // --- Интерфейс ---
  var panel = document.createElement("div");
  panel.className = "upload-panel";
  panel.hidden = true;
  panel.innerHTML =
    '<div class="upload-head"><strong class="upload-name"></strong><span class="upload-state muted small"></span></div>' +
    '<div class="upload-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
    '<div class="upload-fill"></div></div>' +
    '<div class="upload-meta small"><span class="upload-numbers"></span><span class="upload-actions">' +
    '<button type="button" class="link-btn neutral upload-pause"></button>' +
    '<button type="button" class="link-btn upload-cancel"></button></span></div>';
  input.insertAdjacentElement("afterend", panel);
  var el = {
    name: panel.querySelector(".upload-name"), state: panel.querySelector(".upload-state"),
    bar: panel.querySelector(".upload-bar"), fill: panel.querySelector(".upload-fill"),
    numbers: panel.querySelector(".upload-numbers"),
    pause: panel.querySelector(".upload-pause"), cancel: panel.querySelector(".upload-cancel")
  };
  el.cancel.textContent = t("cancel", "Отменить");

  // --- Состояние ---
  var file = null, upload = null, xhr = null, status = "idle"; // idle|uploading|paused|retry|done|error
  var retryDelay = 1000, retryTimer = null, samples = [];

  function fmtBytes(n) {
    var u = [t("b", "Б"), t("kb", "КБ"), t("mb", "МБ"), t("gb", "ГБ")], i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return (i ? n.toFixed(n < 10 ? 2 : 1) : n) + " " + u[i];
  }
  function fmtTime(s) {
    if (!isFinite(s) || s <= 0) return "";
    if (s < 60) return Math.ceil(s) + " " + t("sec", "с");
    if (s < 3600) return Math.ceil(s / 60) + " " + t("min", "мин");
    return Math.floor(s / 3600) + " " + t("hour", "ч") + " " + Math.ceil((s % 3600) / 60) + " " + t("min", "мин");
  }
  function speed() {
    if (samples.length < 2) return 0;
    var a = samples[0], b = samples[samples.length - 1];
    return b.t > a.t ? (b.bytes - a.bytes) / ((b.t - a.t) / 1000) : 0;
  }
  function render(sent) {
    var total = file ? file.size : 0, pct = total ? Math.min(100, sent / total * 100) : 0;
    el.fill.style.width = pct.toFixed(2) + "%";
    el.bar.setAttribute("aria-valuenow", Math.round(pct));
    panel.dataset.status = status;
    var parts = [fmtBytes(sent) + " / " + fmtBytes(total) + " · " + Math.floor(pct) + "%"];
    if (status === "uploading") {
      var v = speed();
      if (v > 0) {
        parts.push(fmtBytes(v) + "/" + t("sec", "с"));
        var left = fmtTime((total - sent) / v);
        if (left) parts.push(t("left", "осталось") + " " + left);
      }
    }
    el.numbers.textContent = parts.join(" · ");
    el.state.textContent = {
      uploading: t("uploading", "Загрузка…"), paused: t("paused", "Пауза"),
      retry: t("retry", "Нет связи — повтор…"), done: t("done", "Загружено. Нажмите «Сохранить»."),
      error: ""
    }[status] || "";
    el.pause.hidden = status === "done" || status === "error";
    el.pause.textContent = status === "paused" ? t("resume", "Продолжить") : t("pause", "Пауза");
  }
  function track(sent) {
    var now = Date.now();
    samples.push({ t: now, bytes: sent });
    while (samples.length > 2 && now - samples[0].t > 5000) samples.shift();
  }
  function fail(message) {
    status = "error";
    el.state.textContent = "";
    panel.dataset.status = status;
    el.numbers.textContent = message;
    el.pause.hidden = true;
  }

  function request(method, url, body, headers) {
    return new Promise(function (resolve, reject) {
      var r = new XMLHttpRequest();
      r.open(method, url);
      r.setRequestHeader("X-CSRFToken", csrf);
      r.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      Object.keys(headers || {}).forEach(function (k) { r.setRequestHeader(k, headers[k]); });
      r.onload = function () {
        var data = {};
        try { data = JSON.parse(r.responseText); } catch (e) {}
        resolve({ status: r.status, data: data });
      };
      r.onerror = r.ontimeout = function () { reject(new Error("network")); };
      r.onabort = function () { reject(new Error("abort")); };
      if (method === "POST" && body instanceof Blob) {
        xhr = r;
        r.upload.onprogress = function (e) {
          if (status === "uploading") { var sent = upload.received + e.loaded; track(sent); render(sent); }
        };
      }
      r.send(body || null);
    });
  }

  function storageKey(f) { return "upload:" + base + ":" + f.name + ":" + f.size + ":" + f.lastModified; }
  function remember(f, id) { try { localStorage.setItem(storageKey(f), id); } catch (e) {} }
  function forget(f) { try { localStorage.removeItem(storageKey(f)); } catch (e) {} }
  function remembered(f) { try { return localStorage.getItem(storageKey(f)); } catch (e) { return null; } }

  function begin() {
    // Тот же файл уже начинали загружать (например, до перезагрузки страницы) — продолжаем
    var id = remembered(file);
    var resume = id ? request("GET", base + id + "/").then(function (r) {
      return r.status === 200 && r.data.size === file.size ? r.data : null;
    }) : Promise.resolve(null);
    return resume.then(function (existing) {
      if (existing) return existing;
      return request("POST", base, JSON.stringify({ filename: file.name, size: file.size }),
        { "Content-Type": "application/json" }).then(function (r) {
        if (r.status !== 201) throw { message: r.data.error || t("failed", "Не удалось начать загрузку.") };
        remember(file, r.data.id);
        return r.data;
      });
    });
  }

  function loop() {
    if (status !== "uploading") return;
    if (upload.received >= file.size) return finish();
    var end = Math.min(upload.received + upload.chunk_size, file.size);
    request("POST", base + upload.id + "/chunk/", file.slice(upload.received, end),
      { "Content-Type": "application/octet-stream", "X-Upload-Offset": String(upload.received) })
      .then(function (r) {
        xhr = null;
        if (r.status === 200 || r.status === 409) {
          // 409: сервер уже на другом смещении (повтор после обрыва) — продолжаем с него
          upload.received = r.data.received;
          retryDelay = 1000;
          track(upload.received); render(upload.received);
          return loop();
        }
        if (r.status >= 500 || r.status === 0 || r.status === 400 && typeof r.data.received === "number") {
          if (typeof r.data.received === "number") upload.received = r.data.received;
          return retry();
        }
        throw { message: r.data.error || (t("http", "Ошибка сервера") + " " + r.status) };
      })
      .catch(function (err) {
        xhr = null;
        if (err && err.message === "abort") return;
        if (err && err.message === "network") return retry();
        fail(err && err.message || t("failed", "Не удалось загрузить файл."));
      });
  }

  function retry() {
    if (status !== "uploading" && status !== "retry") return;
    status = "retry"; render(upload.received);
    clearTimeout(retryTimer);
    retryTimer = setTimeout(function () {
      // Узнаём у сервера, сколько байт он реально получил, и продолжаем
      request("GET", base + upload.id + "/").then(function (r) {
        if (status !== "retry") return;
        if (r.status === 200) { upload.received = r.data.received; status = "uploading"; samples = []; loop(); }
        else if (r.status === 404) fail(t("lost", "Загрузка не найдена на сервере — выберите файл ещё раз."));
        else retry();
      }, function () { retry(); });
    }, retryDelay);
    retryDelay = Math.min(retryDelay * 2, 30000);
  }

  function finish() {
    status = "done";
    hidden.value = upload.id;
    forget(file);
    render(file.size);
  }

  function start(f) {
    stop();
    // Выбрали другой файл — прежнюю (незавершённую или ещё не сохранённую) загрузку удаляем с сервера
    if (upload && file && storageKey(file) !== storageKey(f)) {
      request("DELETE", base + upload.id + "/").catch(function () {});
      forget(file);
    }
    file = f; upload = null; status = "uploading"; samples = []; retryDelay = 1000;
    hidden.value = "";
    // Сам файл не должен уйти в обычной отправке формы — он загружается частями
    input.value = "";
    panel.hidden = false;
    el.name.textContent = f.name;
    render(0);
    begin().then(function (u) {
      if (status !== "uploading") return;
      upload = u; track(u.received); render(u.received); loop();
    }, function (err) {
      if (err && err.message === "network") { fail(t("offline", "Нет связи с сервером.")); return; }
      fail(err && err.message || t("failed", "Не удалось начать загрузку."));
    });
  }

  function stop() {
    clearTimeout(retryTimer);
    if (xhr) { var r = xhr; xhr = null; r.abort(); }
  }

  input.addEventListener("change", function () {
    if (input.files && input.files[0]) start(input.files[0]);
  });

  el.pause.addEventListener("click", function () {
    if (!upload) return;
    if (status === "uploading" || status === "retry") {
      status = "paused"; stop(); render(upload.received);
    } else if (status === "paused") {
      status = "retry"; retryDelay = 0; retry();
    }
  });

  el.cancel.addEventListener("click", function () {
    stop();
    // Удаляем и уже загруженный, но ещё не сохранённый в продукте файл
    if (upload) request("DELETE", base + upload.id + "/").catch(function () {});
    if (file) forget(file);
    status = "idle"; upload = null; file = null; hidden.value = "";
    panel.hidden = true;
  });

  form.addEventListener("submit", function (e) {
    if (status === "uploading" || status === "retry" || status === "paused") {
      e.preventDefault();
      alert(t("wait", "Файл ещё загружается. Дождитесь окончания загрузки и нажмите «Сохранить»."));
    }
  });

  window.addEventListener("beforeunload", function (e) {
    if (status === "uploading" || status === "retry") { e.preventDefault(); e.returnValue = ""; }
  });
})();
