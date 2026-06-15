"""Playable implementations for Tic-Tac-Toe, Connect Four, Othello, and Gomoku."""

from copy import deepcopy

EMPTY = "."


def opponent(player):
    return "O" if player == "X" else "X"


class BoardGame:
    name = "board_game"
    rows = 0
    cols = 0

    def current_player(self, state):
        return state["turn"]

    def render_state(self, state):
        return [" ".join(row) for row in state["board"]]

    def _count_window(self, cells, player):
        other = opponent(player)
        if other in cells:
            return 0
        return cells.count(player)

    def _line_score(self, board, player, target):
        score = 0
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for r in range(len(board)):
            for c in range(len(board[0])):
                for dr, dc in directions:
                    cells = []
                    for i in range(target):
                        rr, cc = r + dr * i, c + dc * i
                        if 0 <= rr < len(board) and 0 <= cc < len(board[0]):
                            cells.append(board[rr][cc])
                    if len(cells) == target:
                        mine = self._count_window(cells, player)
                        theirs = self._count_window(cells, opponent(player))
                        if mine:
                            score += 10 ** mine
                        if theirs:
                            score -= 10 ** theirs
        return score


class TicTacToeGame(BoardGame):
    name = "tic_tac_toe"
    rows = 3
    cols = 3

    def initial_state(self):
        return {"board": [[EMPTY for _ in range(3)] for _ in range(3)], "turn": "X"}

    def legal_moves(self, state):
        return [(r, c) for r in range(3) for c in range(3) if state["board"][r][c] == EMPTY]

    def apply_move(self, state, move):
        r, c = move
        new_state = deepcopy(state)
        new_state["board"][r][c] = state["turn"]
        new_state["turn"] = opponent(state["turn"])
        return new_state

    def winner(self, board):
        lines = board + [list(col) for col in zip(*board)]
        lines.append([board[i][i] for i in range(3)])
        lines.append([board[i][2 - i] for i in range(3)])
        for line in lines:
            if line[0] != EMPTY and line.count(line[0]) == 3:
                return line[0]
        return None

    def is_terminal(self, state):
        return self.winner(state["board"]) is not None or not self.legal_moves(state)

    def utility(self, state, player):
        win = self.winner(state["board"])
        if win == player:
            return 1000
        if win == opponent(player):
            return -1000
        return 0

    def evaluate(self, state, player):
        return self.utility(state, player) or self._line_score(state["board"], player, 3)


class ConnectFourGame(BoardGame):
    name = "connect_four"
    rows = 6
    cols = 7

    def initial_state(self):
        return {"board": [[EMPTY for _ in range(7)] for _ in range(6)], "turn": "X"}

    def legal_moves(self, state):
        return [c for c in range(7) if state["board"][0][c] == EMPTY]

    def apply_move(self, state, move):
        new_state = deepcopy(state)
        for r in range(5, -1, -1):
            if new_state["board"][r][move] == EMPTY:
                new_state["board"][r][move] = state["turn"]
                break
        new_state["turn"] = opponent(state["turn"])
        return new_state

    def winner(self, board):
        for r in range(6):
            for c in range(7):
                if board[r][c] == EMPTY:
                    continue
                token = board[r][c]
                for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                    if all(0 <= r + dr * i < 6 and 0 <= c + dc * i < 7 and board[r + dr * i][c + dc * i] == token for i in range(4)):
                        return token
        return None

    def is_terminal(self, state):
        return self.winner(state["board"]) is not None or not self.legal_moves(state)

    def utility(self, state, player):
        win = self.winner(state["board"])
        if win == player:
            return 100000
        if win == opponent(player):
            return -100000
        return 0

    def evaluate(self, state, player):
        board = state["board"]
        center_bonus = [row[3] for row in board].count(player) * 6
        return self.utility(state, player) or self._line_score(board, player, 4) + center_bonus


class GomokuGame(BoardGame):
    name = "gomoku"
    rows = 9
    cols = 9

    def initial_state(self):
        return {"board": [[EMPTY for _ in range(9)] for _ in range(9)], "turn": "X"}

    def legal_moves(self, state):
        moves = [(r, c) for r in range(9) for c in range(9) if state["board"][r][c] == EMPTY]
        occupied = [(r, c) for r in range(9) for c in range(9) if state["board"][r][c] != EMPTY]
        if not occupied:
            return [(4, 4)]
        nearby = []
        for r, c in moves:
            if any(abs(r - rr) <= 1 and abs(c - cc) <= 1 for rr, cc in occupied):
                nearby.append((r, c))
        return nearby or moves

    def apply_move(self, state, move):
        r, c = move
        new_state = deepcopy(state)
        new_state["board"][r][c] = state["turn"]
        new_state["turn"] = opponent(state["turn"])
        return new_state

    def winner(self, board):
        for r in range(9):
            for c in range(9):
                token = board[r][c]
                if token == EMPTY:
                    continue
                for dr, dc in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                    if all(0 <= r + dr * i < 9 and 0 <= c + dc * i < 9 and board[r + dr * i][c + dc * i] == token for i in range(5)):
                        return token
        return None

    def is_terminal(self, state):
        return self.winner(state["board"]) is not None or not self.legal_moves(state)

    def utility(self, state, player):
        win = self.winner(state["board"])
        if win == player:
            return 1000000
        if win == opponent(player):
            return -1000000
        return 0

    def evaluate(self, state, player):
        # הערה בעברית: בגומוקו חשוב לתגמל רצפים ארוכים גם לפני ניצחון.
        return self.utility(state, player) or self._line_score(state["board"], player, 5)


class OthelloGame(BoardGame):
    name = "othello"
    rows = 8
    cols = 8
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]

    def initial_state(self):
        board = [[EMPTY for _ in range(8)] for _ in range(8)]
        board[3][3] = "O"
        board[3][4] = "X"
        board[4][3] = "X"
        board[4][4] = "O"
        return {"board": board, "turn": "X", "passes": 0}

    def _captures(self, board, player, r, c):
        if board[r][c] != EMPTY:
            return []
        captured = []
        other = opponent(player)
        for dr, dc in self.directions:
            line = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == other:
                line.append((rr, cc))
                rr += dr
                cc += dc
            if line and 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == player:
                captured.extend(line)
        return captured

    def legal_moves(self, state):
        player = state["turn"]
        moves = [(r, c) for r in range(8) for c in range(8) if self._captures(state["board"], player, r, c)]
        return moves or ["pass"]

    def apply_move(self, state, move):
        new_state = deepcopy(state)
        player = state["turn"]
        if move == "pass":
            new_state["turn"] = opponent(player)
            new_state["passes"] = state.get("passes", 0) + 1
            return new_state
        r, c = move
        captures = self._captures(new_state["board"], player, r, c)
        new_state["board"][r][c] = player
        for rr, cc in captures:
            new_state["board"][rr][cc] = player
        new_state["turn"] = opponent(player)
        new_state["passes"] = 0
        return new_state

    def is_terminal(self, state):
        full = all(cell != EMPTY for row in state["board"] for cell in row)
        return full or state.get("passes", 0) >= 2

    def utility(self, state, player):
        board = state["board"]
        mine = sum(row.count(player) for row in board)
        theirs = sum(row.count(opponent(player)) for row in board)
        if self.is_terminal(state):
            if mine > theirs:
                return 100000 + mine - theirs
            if mine < theirs:
                return -100000 + mine - theirs
        return mine - theirs

    def evaluate(self, state, player):
        board = state["board"]
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        corner_score = sum(25 if board[r][c] == player else -25 if board[r][c] == opponent(player) else 0 for r, c in corners)
        mobility = len([m for m in self.legal_moves(state) if m != "pass"])
        return self.utility(state, player) + corner_score + mobility


def get_game(game_name):
    games = {
        "tic_tac_toe": TicTacToeGame,
        "connect_four": ConnectFourGame,
        "othello": OthelloGame,
        "gomoku": GomokuGame,
    }
    return games[game_name]()

