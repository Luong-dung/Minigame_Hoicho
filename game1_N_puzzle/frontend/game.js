const $ = id => document.getElementById(id);
const imageSelect = $("imageSelect"), difficulty = $("difficulty"), board = $("board");
const message = $("message"), hintPreview = $("hintPreview"), hintButton = $("showHint");
let imageUrls = [], validationMap = {}, image = null, pieces = [], tiles = [];
let phase = "loading", moves = 0, hintsRemaining = 3, deadline = 0, startedAt = 0;
let timerId = null, hintTimerId = null, loadEpoch = 0, activeLevel = "easy";
let memoryDeadline = 0, lightUntil = 0;
const config = () => Puzzle.levels[activeLevel];
const formatTime = seconds => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
function setMessage(text, style = "") { message.textContent = text; message.className = style; }
function hideHint() {
  clearTimeout(hintTimerId); hintTimerId = null;
  lightUntil = 0;
  hintPreview.classList.remove("visible"); hintPreview.setAttribute("aria-hidden", "true");
}
function stopTimer() { clearInterval(timerId); timerId = null; }
function controls() {
  const playing = phase === "playing", busy = playing || phase === "memorizing", loading = phase === "loading";
  imageSelect.disabled = busy || !imageUrls.length;
  difficulty.disabled = busy || loading || !image;
  $("randomImage").disabled = busy || !imageUrls.length;
  $("newGame").disabled = loading || !image || phase === "unavailable";
  $("newGame").textContent = busy ? "Kết thúc / Chuẩn bị ván mới" : phase === "ready" ? "Bắt đầu" : "Chuẩn bị ván mới";
  $("surrender").disabled = !playing;
  hintButton.disabled = !playing || hintsRemaining === 0 || lightUntil > performance.now();
  hintButton.textContent = `${activeLevel === "blackout" ? "Bật đèn" : "Gợi ý"} (còn ${hintsRemaining})`;
}
function cropTiles() {
  const { rows, cols } = config();
  const canvas = document.createElement("canvas");
  canvas.width = 900; canvas.height = Math.max(1, Math.round(900 * image.naturalHeight / image.naturalWidth));
  canvas.getContext("2d").drawImage(image, 0, 0, canvas.width, canvas.height);
  pieces = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const piece = document.createElement("canvas");
    const left = Math.floor(c * canvas.width / cols), top = Math.floor(r * canvas.height / rows);
    piece.width = Math.floor((c + 1) * canvas.width / cols) - left;
    piece.height = Math.floor((r + 1) * canvas.height / rows) - top;
    piece.getContext("2d").drawImage(canvas, left, top, piece.width, piece.height, 0, 0, piece.width, piece.height);
    pieces.push(piece.toDataURL("image/png"));
  }
}
function render() {
  board.replaceChildren();
  const { rows, cols } = config();
  board.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  board.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
  board.style.setProperty("--board-ratio", image.naturalWidth / image.naturalHeight);
  const blank = tiles.indexOf(tiles.length - 1);
  const legal = Puzzle.neighbours(blank, rows, cols);
  tiles.forEach((tile, index) => {
    const button = document.createElement("button");
    const empty = tile === tiles.length - 1 && (phase === "playing" || phase === "memorizing");
    const covered = activeLevel === "blackout" && phase === "playing" && lightUntil <= performance.now() && !empty;
    button.className = `tile${empty ? " empty" : covered ? " covered" : ""}`;
    button.disabled = phase !== "playing" || !legal.includes(index);
    button.setAttribute("aria-label", empty ? "Ô trống" : covered ? `Mảnh úp tại ô ${index + 1}` : `Mảnh ${tile + 1}`);
    if (!empty && !covered) { const img = document.createElement("img"); img.src = pieces[tile]; img.alt = ""; button.append(img); }
    button.addEventListener("click", () => move(index)); board.append(button);
  });
}
function finish(text, style) {
  phase = "finished"; stopTimer(); hideHint();
  tiles = Puzzle.solved(config().rows, config().cols);
  render(); controls(); setMessage(text, style);
}
function tick() {
  const now = performance.now();
  if (phase === "memorizing") {
    const remaining = Math.max(0, Math.ceil((memoryDeadline - now) / 1000));
    $("timer").textContent = formatTime(remaining);
    if (remaining) return;
    phase = "playing"; startedAt = memoryDeadline; deadline = startedAt + config().seconds * 1000;
    render(); controls(); setMessage("Đèn đã tắt! Ghép bằng trí nhớ; bạn có 3 lần bật đèn, mỗi lần 2 giây.");
  }
  if (phase !== "playing") return;
  if (lightUntil && now >= lightUntil) { lightUntil = 0; render(); controls(); }
  const remaining = Math.max(0, Math.ceil((deadline - now) / 1000));
  $("timer").textContent = formatTime(remaining);
  if (!remaining) finish("HẾT GIỜ — thử lại ở ván sau nhé!", "surrendered");
}
function move(index) {
  tick();
  if (phase !== "playing") return;
  const { rows, cols } = config(), blank = tiles.indexOf(tiles.length - 1);
  if (!Puzzle.neighbours(blank, rows, cols).includes(index)) return;
  [tiles[blank], tiles[index]] = [tiles[index], tiles[blank]];
  $("moves").textContent = ++moves;
  if (tiles.every((tile, i) => tile === i)) {
    finish(`Hoàn thành trong ${moves} nước và ${formatTime(Math.floor((performance.now() - startedAt) / 1000))}!`, "success");
  } else render();
}
function prepare() {
  stopTimer(); hideHint(); activeLevel = difficulty.value;
  const { rows, cols, seconds } = config();
  cropTiles(); tiles = Puzzle.solved(rows, cols); moves = 0; hintsRemaining = 3; phase = "ready";
  $("moves").textContent = "0"; $("timer").textContent = formatTime(seconds);
  render(); controls(); setMessage(activeLevel === "blackout"
    ? "Bấm Bắt đầu để xem bàn đã trộn trong 10 giây. Sau đó ghép trong bóng tối: 90 giây, 3 lần bật đèn (2 giây/lần)."
    : `Ghi nhớ ảnh ${rows}×${cols}. Bấm Bắt đầu khi sẵn sàng; bạn có ${seconds} giây.`);
}
function start() {
  if (phase !== "ready") { if (image && phase !== "loading" && phase !== "unavailable") prepare(); return; }
  try { tiles = Puzzle.create(activeLevel); }
  catch { setMessage("Chưa tạo được bàn phù hợp. Bấm Bắt đầu để thử lại."); return; }
  if (activeLevel === "blackout") {
    phase = "memorizing"; memoryDeadline = performance.now() + config().memorySeconds * 1000;
    render(); controls(); setMessage("Ghi nhớ vị trí các mảnh! Sau 10 giây, đèn sẽ tắt và ván chơi bắt đầu.");
    tick(); timerId = setInterval(tick, 100); return;
  }
  phase = "playing"; render();
  startedAt = performance.now(); deadline = startedAt + config().seconds * 1000;
  controls(); tick(); timerId = setInterval(tick, 100);
  setMessage("Đưa các mảnh về đúng vị trí trước khi hết giờ!");
}
function loadSelectedImage() {
  if (!imageSelect.value) return;
  const epoch = ++loadEpoch, url = imageSelect.value, pending = new Image();
  stopTimer(); hideHint(); image = null; pieces = []; tiles = []; phase = "loading";
  board.replaceChildren(); $("moves").textContent = "0"; $("timer").textContent = "00:00";
  controls(); setMessage("Đang tải ảnh…");
  pending.onload = () => {
    if (epoch !== loadEpoch) return;
    image = pending;
    const name = decodeURIComponent(url.split("/").pop());
    const blocked = new Set(validationMap[name] || []);
    for (const option of difficulty.options) {
      const level = Puzzle.levels[option.value];
      option.disabled = blocked.has(`${level.rows}x${level.cols}`);
      option.title = option.disabled ? "Ảnh có các mảnh quá giống nhau ở kích thước này." : "";
    }
    if (difficulty.selectedOptions[0].disabled) {
      const available = [...difficulty.options].find(option => !option.disabled);
      if (!available) { phase = "unavailable"; controls(); setMessage("Ảnh không có mức hợp lệ. Hãy chọn ảnh khác."); return; }
      difficulty.value = available.value;
    }
    prepare();
  };
  pending.onerror = () => {
    if (epoch !== loadEpoch) return;
    phase = "unavailable"; controls(); setMessage("Không thể đọc ảnh. Hãy chọn ảnh khác.");
  };
  pending.src = url;
}
$("newGame").addEventListener("click", start);
$("randomImage").addEventListener("click", () => {
  if (phase === "playing" || phase === "memorizing") return;
  const alternatives = imageUrls.filter(url => url !== imageSelect.value);
  if (!alternatives.length) return;
  imageSelect.value = alternatives[Math.floor(Math.random() * alternatives.length)]; loadSelectedImage();
});
hintButton.addEventListener("click", () => {
  tick(); if (phase !== "playing" || !hintsRemaining) return;
  if (activeLevel === "blackout") {
    if (lightUntil > performance.now()) return;
    hintsRemaining--; lightUntil = performance.now() + config().lightSeconds * 1000;
    render(); controls(); return;
  }
  hideHint(); hintsRemaining--; $("hintImage").src = image.src;
  hintPreview.classList.add("visible"); hintPreview.setAttribute("aria-hidden", "false");
  hintTimerId = setTimeout(hideHint, 3000); controls();
});
$("surrender").addEventListener("click", () => { if (phase === "playing") finish("ĐÃ ĐẦU HÀNG", "surrendered"); });
imageSelect.addEventListener("change", () => { if (phase !== "playing" && phase !== "memorizing") loadSelectedImage(); });
difficulty.addEventListener("change", () => { if (image && phase !== "playing" && phase !== "memorizing" && phase !== "loading" && !difficulty.selectedOptions[0].disabled) prepare(); });
document.addEventListener("keydown", event => {
  if (phase !== "playing" || ["SELECT", "INPUT", "TEXTAREA"].includes(event.target.tagName)) return;
  const { rows, cols } = config(), blank = tiles.indexOf(tiles.length - 1);
  const target = { ArrowUp: blank - cols, ArrowDown: blank + cols, ArrowLeft: blank - 1, ArrowRight: blank + 1 }[event.key];
  if (target !== undefined) { event.preventDefault(); if (Puzzle.neighbours(blank, rows, cols).includes(target)) move(target); }
});
document.addEventListener("visibilitychange", tick);
controls();
Promise.all([fetch("/api/images"), fetch("/api/validation")])
  .then(async responses => {
    if (responses.some(response => !response.ok)) throw new Error("Không thể tải dữ liệu ảnh.");
    return Promise.all(responses.map(response => response.json()));
  })
  .then(([images, validation]) => {
    imageUrls = images; validationMap = validation;
    imageSelect.replaceChildren(...images.map(url => new Option(decodeURIComponent(url.split("/").pop()), url)));
    if (!images.length) throw new Error("Không tìm thấy ảnh trong thư mục image.");
    loadSelectedImage();
  })
  .catch(error => { phase = "unavailable"; controls(); setMessage(error.message); });
