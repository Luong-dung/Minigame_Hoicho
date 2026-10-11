// Pure puzzle rules, shared by the browser and Node tests.
const Puzzle = (() => {
  const levels = {
    easy: { rows: 3, cols: 3, seconds: 60, min: 6, max: 10 },
    medium: { rows: 3, cols: 3, seconds: 90, min: 14, max: 18 },
    hard: { rows: 3, cols: 4, seconds: 120, steps: 30, min: 12 },
    "very-hard": { rows: 4, cols: 4, seconds: 180, steps: 50, min: 20 },
    blackout: { rows: 3, cols: 3, seconds: 90, min: 6, max: 10, memorySeconds: 10, lightSeconds: 2 }
  };
  const solved = (rows, cols) => Array.from({ length: rows * cols }, (_, i) => i);
  function neighbours(index, rows, cols) {
    const r = Math.floor(index / cols), c = index % cols, result = [];
    if (r > 0) result.push(index - cols);
    if (r < rows - 1) result.push(index + cols);
    if (c > 0) result.push(index - 1);
    if (c < cols - 1) result.push(index + 1);
    return result;
  }
  function manhattan(tiles, cols) {
    return tiles.reduce((sum, tile, index) => tile === tiles.length - 1 ? sum : sum
      + Math.abs(Math.floor(tile / cols) - Math.floor(index / cols))
      + Math.abs(tile % cols - index % cols), 0);
  }
  let buckets;
  function smallBoards() {
    if (buckets) return buckets;
    buckets = Array.from({ length: 19 }, () => []);
    const start = "012345678", seen = new Set([start]);
    buckets[0].push(start);
    for (let depth = 0; depth < 18; depth++) {
      for (const state of buckets[depth]) {
        const blank = state.indexOf("8");
        for (const target of neighbours(blank, 3, 3)) {
          const next = state.split("");
          [next[blank], next[target]] = [next[target], next[blank]];
          const key = next.join("");
          if (!seen.has(key)) { seen.add(key); buckets[depth + 1].push(key); }
        }
      }
    }
    return buckets;
  }
  function create(level, random = Math.random) {
    const config = levels[level];
    if (!config) throw new Error("Unknown difficulty");
    if (config.max) {
      const depth = config.min + Math.floor(random() * (config.max - config.min + 1));
      const options = smallBoards()[depth];
      return options[Math.floor(random() * options.length)].split("").map(Number);
    }
    // Legal walks guarantee a solution in at most `steps` moves. Manhattan
    // distance supplies a lower bound; it is not the exact solution length.
    for (let attempt = 0; attempt < 200; attempt++) {
      const tiles = solved(config.rows, config.cols);
      let blank = tiles.length - 1, previous = -1;
      for (let step = 0; step < config.steps; step++) {
        const options = neighbours(blank, config.rows, config.cols).filter(i => i !== previous);
        const target = options[Math.floor(random() * options.length)];
        [tiles[blank], tiles[target]] = [tiles[target], tiles[blank]];
        previous = blank; blank = target;
      }
      if (manhattan(tiles, config.cols) >= config.min) return tiles;
    }
    throw new Error("Cannot generate a board; please try again");
  }
  return { levels, solved, neighbours, manhattan, create };
})();
if (typeof module !== "undefined") module.exports = Puzzle;
