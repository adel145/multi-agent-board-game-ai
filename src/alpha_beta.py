"""Minimax with alpha-beta cutoff for all supported board games."""

from math import inf


def alpha_beta_cutoff_search(game, state, depth_limit, player=None):
    """Return ``(best_move, score)`` using alpha-beta pruning.

    The function works only through the common game interface, so every game
    can be swapped in without changing the search code.
    """
    root_player = player or game.current_player(state)
    if game.is_terminal(state):
        return None, game.utility(state, root_player)
    moves = list(game.legal_moves(state))
    if not moves:
        return None, game.utility(state, root_player)

    def cutoff(current_state, depth):
        # הערה בעברית: עוצרים בעומק שהמשתמש בחר או במצב סופי של המשחק.
        return depth >= depth_limit or game.is_terminal(current_state)

    def max_value(current_state, alpha, beta, depth):
        if game.is_terminal(current_state):
            return game.utility(current_state, root_player)
        if cutoff(current_state, depth):
            return game.evaluate(current_state, root_player)
        value = -inf
        for move in game.legal_moves(current_state):
            value = max(value, min_value(game.apply_move(current_state, move), alpha, beta, depth + 1))
            if value >= beta:
                return value
            alpha = max(alpha, value)
        return value

    def min_value(current_state, alpha, beta, depth):
        if game.is_terminal(current_state):
            return game.utility(current_state, root_player)
        if cutoff(current_state, depth):
            return game.evaluate(current_state, root_player)
        value = inf
        for move in game.legal_moves(current_state):
            value = min(value, max_value(game.apply_move(current_state, move), alpha, beta, depth + 1))
            if value <= alpha:
                return value
            beta = min(beta, value)
        return value

    best_move = moves[0]
    best_score = -inf
    alpha = -inf
    beta = inf
    for move in moves:
        score = min_value(game.apply_move(state, move), alpha, beta, 1)
        if score > best_score:
            best_move = move
            best_score = score
        alpha = max(alpha, best_score)
    return best_move, best_score
