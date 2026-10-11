const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const Puzzle = require('./frontend/puzzle.js');

function setup() {
  let now = 0, crops = 0;
  class Element {
    constructor() {
      this.value = ''; this.children = []; this.disabled = false; this.tagName = 'DIV';
      this.style = { setProperty() {} }; this.classList = { add() {}, remove() {} };
      this.listeners = {}; this.options = [];
    }
    get selectedOptions() { return this.options.filter(option => option.value === this.value); }
    addEventListener(name, fn) { this.listeners[name] = fn; }
    setAttribute() {}
    append(child) { this.children.push(child); }
    replaceChildren(...children) { this.children = children; }
    getContext() { return { drawImage() { crops++; } }; }
    toDataURL() { return 'data:image/png;base64,test'; }
  }
  const elements = new Map(), images = [];
  const document = {
    getElementById(id) { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); },
    createElement() { return new Element(); }, addEventListener() {}
  };
  const difficulty = document.getElementById('difficulty');
  difficulty.options = Object.keys(Puzzle.levels).map(value => ({ value, disabled: false }));
  difficulty.value = 'easy';
  const context = vm.createContext({
    Puzzle, document, Image: class { constructor() { images.push(this); this.naturalWidth = 900; this.naturalHeight = 900; } },
    performance: { now: () => now }, fetch: () => new Promise(() => {}),
    setInterval: () => 1, clearInterval() {}, setTimeout: () => 1, clearTimeout() {}, Option: Element
  });
  vm.runInContext(fs.readFileSync(require.resolve('./frontend/game.js'), 'utf8'), context);
  const run = source => vm.runInContext(source, context);
  run('imageUrls = ["/image/a.png", "/image/b.png"]; imageSelect.value = imageUrls[0]; loadSelectedImage();');
  return { run, images, elements, setTime: value => { now = value; }, cropCount: () => crops };
}

test('preview does not start timer or allow moves; rendering reuses cropped pieces', () => {
  const app = setup(); app.images[0].onload();
  assert.equal(app.run('phase'), 'ready'); assert.equal(app.run('timerId'), null);
  app.run('move(7)'); assert.equal(app.run('moves'), 0);
  const crops = app.cropCount();
  app.run('start(); move(Puzzle.neighbours(tiles.indexOf(8), 3, 3)[0]);');
  assert.equal(app.run('moves'), 1); assert.equal(app.cropCount(), crops);
});

test('obsolete image success and failure cannot overwrite current selection', () => {
  const app = setup();
  app.run('imageSelect.value = imageUrls[1]; loadSelectedImage();');
  app.images[1].onload(); app.images[0].onload(); app.images[0].onerror();
  assert.equal(app.run('image.src'), '/image/b.png'); assert.equal(app.run('phase'), 'ready');
});

test('expired move is rejected even before the interval updates', () => {
  const app = setup(); app.images[0].onload(); app.run('start();');
  app.setTime(60000); app.run('move(Puzzle.neighbours(tiles.indexOf(8), 3, 3)[0]);');
  assert.equal(app.run('phase'), 'finished'); assert.equal(app.run('moves'), 0);
  assert.equal(app.elements.get('timer').textContent, '00:00');
  assert.equal(app.run('timerId'), null);
});

test('win, surrender and restart stop timers and restore preparation', () => {
  const app = setup(); app.images[0].onload(); app.run('start(); tiles = [0,1,2,3,4,5,6,8,7]; move(8);');
  assert.equal(app.run('phase'), 'finished'); assert.equal(app.run('timerId'), null);
  assert.match(app.elements.get('message').textContent, /Hoàn thành/);
  app.run('start();'); assert.equal(app.run('phase'), 'ready');
  app.run('start();'); app.elements.get('surrender').listeners.click();
  assert.equal(app.run('phase'), 'finished'); assert.equal(app.run('timerId'), null);
});

test('hint expiry check and image failures keep actions disabled', () => {
  const app = setup(); app.images[0].onerror();
  assert.equal(app.run('phase'), 'unavailable'); assert.equal(app.elements.get('newGame').disabled, true);
  app.run('loadSelectedImage();'); app.images[1].onload(); app.run('start();');
  app.setTime(60000); app.elements.get('showHint').listeners.click();
  assert.equal(app.run('phase'), 'finished'); assert.equal(app.run('hintsRemaining'), 3);
});

test('blackout memorizes the shuffled board, then hides identities and allows three brief lights', () => {
  const app = setup(); app.images[0].onload();
  app.run('difficulty.value = "blackout"; prepare(); start();');
  assert.equal(app.run('phase'), 'memorizing');
  app.run('move(Puzzle.neighbours(tiles.indexOf(8), 3, 3)[0]);');
  assert.equal(app.run('moves'), 0);
  const original = app.run('tiles.join(",")');
  app.setTime(10000); app.run('tick();');
  assert.equal(app.run('phase'), 'playing');
  assert.equal(app.run('tiles.join(",")'), original);
  const covered = () => app.elements.get('board').children.filter(button => button.className.includes('covered'));
  assert.equal(covered().length, 8);
  assert.ok(covered().every(button => button.children.length === 0));
  for (let i = 0; i < 3; i++) {
    app.elements.get('showHint').listeners.click();
    assert.equal(covered().length, 0);
    const remaining = app.run('hintsRemaining');
    app.elements.get('showHint').listeners.click();
    assert.equal(app.run('hintsRemaining'), remaining);
    app.setTime(12000 + i * 2000); app.run('tick();');
    assert.equal(covered().length, 8);
  }
  assert.equal(app.run('hintsRemaining'), 0);
  assert.equal(app.elements.get('showHint').disabled, true);
  app.elements.get('showHint').listeners.click();
  assert.equal(covered().length, 8);
});

test('blackout elapsed time survives a skipped memory phase and restart resets lights', () => {
  const app = setup(); app.images[0].onload();
  app.run('difficulty.value = "blackout"; prepare(); start();');
  app.setTime(45000); app.run('tick();');
  assert.equal(app.elements.get('timer').textContent, '00:55');
  app.elements.get('showHint').listeners.click();
  app.run('start();');
  assert.equal(app.run('phase'), 'ready'); assert.equal(app.run('lightUntil'), 0);
  app.run('start();'); app.setTime(145000); app.run('tick();');
  assert.equal(app.run('phase'), 'finished');
  assert.equal(app.run('timerId'), null);
  assert.ok(app.elements.get('board').children.every(button => !button.className.includes('covered')));
});
