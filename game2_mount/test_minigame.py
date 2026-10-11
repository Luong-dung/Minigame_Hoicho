import unittest
from collections import deque
from unittest.mock import patch

from minigame import Game, HUNTER_PATTERNS


def shortest_strategy(count, pattern=(1,)):
    """Search all knowledge states using an independent movement model."""
    start = (frozenset(range(count)), 0)
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        (positions, phase), path = queue.popleft()
        for cup in range(count):
            remaining = positions - {cup}
            if not remaining:
                return path + [cup]
            following = set()
            for position in remaining:
                for direction in (-1, 1):
                    target = position + direction * pattern[phase]
                    if target < 0:
                        target = -target
                    if target >= count:
                        target = 2 * (count - 1) - target
                    following.add(target)
            state = (frozenset(following), (phase + 1) % len(pattern))
            if state not in seen:
                seen.add(state)
                queue.append((state, path + [cup]))
    raise AssertionError("No winning strategy")


class GameTests(unittest.TestCase):
    def test_fixed_levels_and_validation(self):
        game = Game()
        for level, cups, moves in [(1, 5, 4), (2, 8, 12), (3, 8, 13), (4, 8, 14)]:
            game.reset(level)
            self.assertEqual((game.cup_count, game.max_moves), (cups, moves))
            self.assertIsNone(game.state()["mouse_position"])
        for invalid in (0, 6, True, "4", 4.0):
            with self.assertRaises(ValueError):
                game.reset(invalid)

    def test_smart_levels_have_winning_strategies_within_limit(self):
        game = Game()
        for level in (2, 3, 4):
            game.reset(level)
            strategy = shortest_strategy(game.cup_count, game.movement_pattern)
            self.assertEqual(len(strategy), game.max_moves)
            for cup in strategy:
                result = game.open_cup(cup)
            self.assertTrue(result["won"])
            self.assertEqual(result["mouse_position"], strategy[-1])
            with self.assertRaises(ValueError):
                game.open_cup(0)

    def test_boss_reflection_and_rhythm(self):
        game = Game()
        game.reset(3)
        self.assertEqual(game._destinations(0, 2), {2})
        self.assertEqual(game._destinations(1, 2), {1, 3})
        self.assertEqual(game._destinations(7, 2), {5})
        for expected in (2, 1, 2, 1):
            result = game.open_cup(0)
            self.assertEqual(result["next_step"], expected)
            self.assertIsNone(result["mouse_position"])

    def test_super_boss_reflection_and_rhythm(self):
        game = Game()
        game.reset(4)
        self.assertEqual(game._destinations(0, 3), {3})
        self.assertEqual(game._destinations(1, 3), {2, 4})
        self.assertEqual(game._destinations(7, 3), {4})
        for expected in (2, 3, 1, 2, 3, 1):
            result = game.open_cup(0)
            self.assertEqual(result["next_step"], expected)
            self.assertIsNone(result["mouse_position"])

    def test_loss_at_limit_and_no_extra_moves(self):
        for level in (1, 2, 3, 4):
            game = Game()
            game.reset(level)
            game.mouse_position = 2
            with patch("minigame.random.choice", side_effect=lambda values: max(values)):
                for _ in range(game.max_moves):
                    result = game.open_cup(0)
            self.assertTrue(result["finished"])
            self.assertFalse(result["won"])
            self.assertNotEqual(result["mouse_position"], 0)
            self.assertIsNone(result["next_step"])
            with self.assertRaises(ValueError):
                game.open_cup(0)
            self.assertEqual(game.moves, game.max_moves)

    def test_random_win_and_invalid_cup(self):
        game = Game()
        for invalid in (-1, 5, True, "1"):
            with self.assertRaises(ValueError):
                game.open_cup(invalid)
        self.assertEqual(game.moves, 0)
        result = game.open_cup(game.mouse_position)
        self.assertTrue(result["won"])



class EscapeTests(unittest.TestCase):
    def game(self, branch):
        game = Game()
        with patch("minigame.random.randrange", side_effect=[0, branch]):
            game.reset(5)
        self.assertEqual((game.cup_count, game.max_moves), (7, 10))
        self.assertEqual(game.hunter_strategy, branch)
        self.assertNotIn("hunter_strategy", game.state())
        return game

    def test_all_four_patterns_capture_every_possible_path(self):
        for pattern in HUNTER_PATTERNS:
            positions = set(range(7))
            self.assertEqual(len(pattern), 10)
            for cup in pattern:
                remaining = positions - {cup}
                positions = {n for p in remaining for n in (p-1, p+1) if 0 <= n < 7}
            self.assertEqual(positions, set())

    def test_fixed_branch_never_rerolls_and_ignores_actual_position(self):
        for branch, pattern in enumerate(HUNTER_PATTERNS):
            for start in range(7):
                game = self.game(branch)
                game.escape_action("choose", start)
                with patch("minigame.random.randrange", side_effect=AssertionError("Rerolled fixed strategy")):
                    while not game.finished:
                        result = game.escape_action("hunt")
                        self.assertEqual(result["hunter_cup"], pattern[game.moves-1])
                        if not result["finished"]:
                            game.escape_action("move", result["legal_moves"][0])
                self.assertFalse(game.won)
                self.assertLessEqual(game.moves, 10)

    def test_random_branch_can_survive_and_capture_on_last_turn(self):
        game = self.game(4)
        game.escape_action("choose", 6)
        for _ in range(10):
            with patch("minigame.random.randrange", return_value=0) as draw:
                result = game.escape_action("hunt")
                draw.assert_called_once_with(7)
            if not result["finished"]:
                game.escape_action("move", 5 if game.mouse_position == 6 else 6)
        self.assertTrue(result["won"])
        self.assertEqual(result["moves"], 10)
        with self.assertRaises(ValueError):
            game.escape_action("hunt")
        game = self.game(4)
        game.escape_action("choose", 6)
        game.moves = 9
        with patch("minigame.random.randrange", return_value=6):
            result = game.escape_action("hunt")
        self.assertTrue(result["finished"])
        self.assertFalse(result["won"])

    def test_illegal_actions_leave_game_unchanged(self):
        game = self.game(0)
        with self.assertRaises(ValueError):
            game.escape_action("hunt")
        for position in (7, -1, True, "1"):
            with self.assertRaises(ValueError):
                game.escape_action("choose", position)
        game.escape_action("choose", 6)
        with self.assertRaises(ValueError):
            game.open_cup(0)
        result = game.escape_action("hunt")
        self.assertEqual(result["legal_moves"], [5])
        for action, position in (("hunt", None), ("move", 6), ("move", 4), ("choose", 0)):
            with self.assertRaises(ValueError):
                game.escape_action(action, position)
        self.assertEqual(game.moves, 1)
        game.escape_action("move", 5)
        self.assertEqual(game.escape_phase, "hunt")


if __name__ == "__main__":
    unittest.main()
