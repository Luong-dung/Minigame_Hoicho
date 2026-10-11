const test = require('node:test');
const assert = require('node:assert/strict');
const Puzzle = require('./frontend/puzzle.js');

test('3x3 boards match independently calculated optimal distances', () => {
  const distances = new Map([['012345678', 0]]), queue = ['012345678'];
  for (let head = 0; head < queue.length; head++) {
    const state = queue[head], depth = distances.get(state);
    if (depth === 18) continue;
    const blank = state.indexOf('8');
    for (let target = 0; target < 9; target++) {
      if (Math.abs(Math.floor(blank / 3) - Math.floor(target / 3)) + Math.abs(blank % 3 - target % 3) !== 1) continue;
      const next = state.split(''); [next[blank], next[target]] = [next[target], next[blank]];
      const key = next.join('');
      if (!distances.has(key)) { distances.set(key, depth + 1); queue.push(key); }
    }
  }
  for (const level of ['easy', 'medium', 'blackout']) for (let i = 0; i < 100; i++) {
    const depth = distances.get(Puzzle.create(level).join(''));
    assert.ok(depth >= Puzzle.levels[level].min && depth <= Puzzle.levels[level].max);
  }
});

test('large boards have valid permutations, solvable parity and minimum displacement', () => {
  for (const level of ['hard', 'very-hard']) for (let i = 0; i < 100; i++) {
    const config = Puzzle.levels[level], tiles = Puzzle.create(level);
    assert.deepEqual([...tiles].sort((a, b) => a - b), Puzzle.solved(config.rows, config.cols));
    let inversions = 0;
    const numbered = tiles.filter(tile => tile !== tiles.length - 1);
    for (let a = 0; a < numbered.length; a++) for (let b = a + 1; b < numbered.length; b++) {
      if (numbered[a] > numbered[b]) inversions++;
    }
    const blankRowFromBottom = config.rows - Math.floor(tiles.indexOf(tiles.length - 1) / config.cols);
    assert.equal((inversions + blankRowFromBottom) % 2, 1);
    assert.ok(Puzzle.manhattan(tiles, config.cols) >= config.min);
  }
});

test('neighbours never wrap at row boundaries', () => {
  assert.deepEqual(Puzzle.neighbours(3, 3, 4), [7, 2]);
  assert.throws(() => Puzzle.create('invalid'));
});
