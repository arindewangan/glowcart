/* GlowCart frontend: tabs, skin analysis flow, routine builder, try-on. */
(function () {
  "use strict";

  /* ---------- tabs ---------- */
  document.querySelectorAll(".tab").forEach(function (t) {
    t.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (x) { x.classList.remove("active"); });
      t.classList.add("active");
      document.getElementById("tab-skin").classList.toggle("hidden", t.dataset.tab !== "skin");
      document.getElementById("tab-tryon").classList.toggle("hidden", t.dataset.tab !== "tryon");
    });
  });

  /* ---------- mode banner ---------- */
  var modeBanner = document.getElementById("mode-banner");
  fetch("/api/health")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.mode === "demo") {
        modeBanner.textContent =
          "Demo mode — add a YouCam API key for live AI. Analysis and try-on here are simulated and clearly labelled.";
        modeBanner.classList.remove("hidden");
      }
    })
    .catch(function () {});

  /* ---------- skin analysis ---------- */
  var selfieInput = document.getElementById("selfie-input");
  var selfiePreview = document.getElementById("selfie-preview");
  var selfiePreviewWrap = document.getElementById("selfie-preview-wrap");
  var analyzeBtn = document.getElementById("analyze-btn");
  var analyzeError = document.getElementById("analyze-error");
  var analyzeProgress = document.getElementById("analyze-progress");
  var report = document.getElementById("report");
  var lastRecs = [];

  selfieInput.addEventListener("change", function () {
    var f = selfieInput.files[0];
    if (!f) return;
    var reader = new FileReader();
    reader.onload = function (e) {
      selfiePreview.src = e.target.result;
      selfiePreviewWrap.classList.remove("hidden");
      analyzeBtn.disabled = false;
      analyzeError.classList.add("hidden");
    };
    reader.readAsDataURL(f);
  });

  function stars(n) {
    var full = Math.round(n);
    var s = "";
    for (var i = 0; i < 5; i++) s += i < full ? "★" : "☆";
    return s;
  }

  function barColor(score) {
    if (score >= 75) return "#15803d";
    if (score >= 50) return "#e8a13c";
    return "#c2437e";
  }

  analyzeBtn.addEventListener("click", function () {
    var f = selfieInput.files[0];
    if (!f) return;
    analyzeError.classList.add("hidden");
    analyzeBtn.disabled = true;
    analyzeProgress.classList.remove("hidden");

    var fd = new FormData();
    fd.append("selfie", f);
    fetch("/api/analyze", { method: "POST", body: fd })
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, body: d }; }); })
      .then(function (res) {
        analyzeBtn.disabled = false;
        analyzeProgress.classList.add("hidden");
        if (res.status !== 200) {
          analyzeError.textContent = res.body.error || "Something went wrong.";
          analyzeError.classList.remove("hidden");
          return;
        }
        renderReport(res.body);
      })
      .catch(function () {
        analyzeBtn.disabled = false;
        analyzeProgress.classList.add("hidden");
        analyzeError.textContent = "Couldn't reach the server. Is it still running?";
        analyzeError.classList.remove("hidden");
      });
  });

  function renderReport(d) {
    var note = document.getElementById("report-demo-note");
    if (d.mode === "demo") {
      note.textContent = d.note || "Demo mode — simulated analysis, not a real AI scan.";
      note.classList.remove("hidden");
    } else {
      note.classList.add("hidden");
    }

    var scores = d.scores.slice().sort(function (a, b) { return a.score - b.score; });
    var avg = scores.reduce(function (s, x) { return s + x.score; }, 0) / Math.max(1, scores.length);
    document.getElementById("skin-score").textContent = Math.round(avg);
    document.getElementById("skin-score-note").textContent =
      avg >= 75 ? "Glowing — let's keep it that way." :
      avg >= 55 ? "Healthy overall, with a few things to work on." :
                  "A focused routine will make a real difference.";
    document.getElementById("skin-type").textContent = d.skin_type ? "Skin type: " + d.skin_type : "";

    var focus = document.getElementById("focus-list");
    focus.innerHTML = "";
    scores.slice(0, 3).forEach(function (s) { focus.appendChild(concernRow(s, true)); });

    var grid = document.getElementById("score-grid");
    grid.innerHTML = "";
    scores.forEach(function (s) { grid.appendChild(concernRow(s, false)); });

    lastRecs = d.recommendations || [];
    var pg = document.getElementById("product-grid");
    pg.innerHTML = "";
    lastRecs.forEach(function (p) {
      var div = document.createElement("div");
      div.className = "product";
      div.innerHTML =
        "<h4></h4>" +
        '<div class="price">₹' + p.price_inr + " · " + p.size + "</div>" +
        '<p class="blurb"></p>' +
        '<p class="match">Matches: ' + p.matched_concerns.join(", ") + "</p>" +
        '<label class="pick"><input type="checkbox" data-pid="' + p.id + '" checked> Add to my routine</label>';
      div.querySelector("h4").textContent = p.name;
      div.querySelector(".blurb").textContent = p.blurb;
      pg.appendChild(div);
    });

    renderRoutinePicker();
    document.getElementById("routine-out").classList.add("hidden");
    document.getElementById("upload-card").classList.add("hidden");
    report.classList.remove("hidden");
    report.scrollIntoView({ behavior: "smooth" });
  }

  function concernRow(s, focus) {
    var div = document.createElement("div");
    div.className = "concern-row";
    var name = document.createElement("div");
    name.innerHTML = '<div class="concern-name"></div><div class="stars"></div>';
    name.querySelector(".concern-name").textContent = s.label;
    name.querySelector(".stars").textContent = stars(s.stars);
    var right = document.createElement("div");
    right.innerHTML = '<span class="score-num"></span>';
    right.querySelector(".score-num").textContent = Math.round(s.score) + "/100";
    var bar = document.createElement("div");
    bar.className = "bar";
    var fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = Math.max(2, s.score) + "%";
    fill.style.background = barColor(s.score);
    bar.appendChild(fill);
    div.appendChild(name);
    div.appendChild(right);
    div.appendChild(bar);
    if (focus) {
      var sub = document.createElement("div");
      sub.className = "concern-sub";
      sub.textContent = "Priority focus — matched products below target this.";
      sub.style.gridColumn = "1 / -1";
      div.appendChild(sub);
    }
    return div;
  }

  function renderRoutinePicker() {
    var rp = document.getElementById("routine-picker");
    rp.innerHTML = "";
    lastRecs.forEach(function (p) {
      var lab = document.createElement("label");
      lab.className = "pick";
      lab.style.display = "flex";
      lab.style.gap = "0.5rem";
      lab.style.marginBottom = "0.4rem";
      lab.style.fontSize = "0.9rem";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = true;
      cb.dataset.pid = p.id;
      lab.appendChild(cb);
      var sp = document.createElement("span");
      sp.textContent = p.name + " (₹" + p.price_inr + ")";
      lab.appendChild(sp);
      rp.appendChild(lab);
    });
  }

  document.getElementById("routine-btn").addEventListener("click", function () {
    var ids = [];
    document.querySelectorAll("#routine-picker input[data-pid]:checked").forEach(function (cb) {
      ids.push(cb.dataset.pid);
    });
    fetch("/api/routine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_ids: ids })
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        function fill(olId, items) {
          var ol = document.getElementById(olId);
          ol.innerHTML = "";
          items.forEach(function (p) {
            var li = document.createElement("li");
            li.textContent = p.name;
            ol.appendChild(li);
          });
          if (!items.length) {
            var li = document.createElement("li");
            li.textContent = "—";
            ol.appendChild(li);
          }
        }
        fill("routine-am", d.am);
        fill("routine-pm", d.pm);
        document.getElementById("routine-total").textContent = "₹" + d.total_inr;
        document.getElementById("routine-out").classList.remove("hidden");
      });
  });

  document.getElementById("reset-btn").addEventListener("click", function () {
    report.classList.add("hidden");
    document.getElementById("upload-card").classList.remove("hidden");
    selfieInput.value = "";
    selfiePreviewWrap.classList.add("hidden");
    analyzeBtn.disabled = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ---------- try-on ---------- */
  var personInput = document.getElementById("person-input");
  var garmentInput = document.getElementById("garment-input");
  var personPreview = document.getElementById("person-preview");
  var garmentPreview = document.getElementById("garment-preview");
  var tryonBtn = document.getElementById("tryon-btn");
  var tryonError = document.getElementById("tryon-error");
  var tryonProgress = document.getElementById("tryon-progress");

  function bindPreview(input, img) {
    input.addEventListener("change", function () {
      var f = input.files[0];
      if (!f) return;
      var reader = new FileReader();
      reader.onload = function (e) {
        img.src = e.target.result;
        img.classList.remove("hidden");
        tryonBtn.disabled = !(personInput.files[0] && garmentInput.files[0]);
      };
      reader.readAsDataURL(f);
    });
  }
  bindPreview(personInput, personPreview);
  bindPreview(garmentInput, garmentPreview);

  tryonBtn.addEventListener("click", function () {
    tryonError.classList.add("hidden");
    tryonBtn.disabled = true;
    tryonProgress.classList.remove("hidden");
    document.getElementById("tryon-out").classList.add("hidden");

    var fd = new FormData();
    fd.append("person", personInput.files[0]);
    fd.append("garment", garmentInput.files[0]);
    fetch("/api/tryon", { method: "POST", body: fd })
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, body: d }; }); })
      .then(function (res) {
        tryonBtn.disabled = false;
        tryonProgress.classList.add("hidden");
        if (res.status !== 200) {
          tryonError.textContent = res.body.error || "Something went wrong.";
          tryonError.classList.remove("hidden");
          return;
        }
        var d = res.body;
        document.getElementById("tryon-out").classList.remove("hidden");
        var dn = document.getElementById("tryon-demo-note");
        var img = document.getElementById("tryon-result");
        if (d.mode === "demo") {
          dn.textContent = d.note;
          dn.classList.remove("hidden");
          img.classList.add("hidden");
          document.getElementById("tryon-note").textContent = "";
        } else {
          dn.classList.add("hidden");
          img.src = d.result_url;
          img.classList.remove("hidden");
          document.getElementById("tryon-note").textContent = d.note || "";
        }
      })
      .catch(function () {
        tryonBtn.disabled = false;
        tryonProgress.classList.add("hidden");
        tryonError.textContent = "Couldn't reach the server. Is it still running?";
        tryonError.classList.remove("hidden");
      });
  });
})();
