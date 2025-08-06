

import random
import copy




class AIPlayer:
    def __init__(self, game_instance, ai_color, depth=2):
        self.game = game_instance
        self.ai_color = ai_color
        self.depth = depth
        self.piece_values = {
            'pawn': 100, 'knight': 320, 'bishop': 330, 'rook': 500, 'queen': 900, 'king': 20000
        }

        self.pawn_table = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        self.knight_table = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 0, 0, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 20, 20, 15, 0, -30],
            [-30, 5, 10, 15, 15, 10, 5, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]
        self.bishop_table = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 5, 10, 10, 5, 5, -10],
            [-10, 0, 10, 10, 10, 10, 0, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]
        self.rook_table = [
            [0, 0, 0, 5, 5, 0, 0, 0],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [0, 0, 0, 5, 5, 0, 0, 0]
        ]
        self.queen_table = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [0, 0, 5, 5, 5, 5, 0, -5],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20]
        ]
        self.king_table_middle_game = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20]
        ]
        self.king_table_end_game = [
            [-50, -40, -30, -20, -20, -30, -40, -50],
            [-30, -20, -10, 0, 0, -10, -20, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -30, 0, 0, 0, 0, -30, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]

    def make_move(self):
        if self.game.game_over:
            return

        print(f"AI ({self.ai_color.upper()}) is thinking with a depth of {self.depth}...")

        best_move, _ = self._minimax(self.game, self.depth, -float('inf'), float('inf'), self.ai_color)

        if not best_move:
            legal_moves = self.game.get_all_legal_moves(self.ai_color)
            if legal_moves:
                print("Minmax could not find a best move, choosing a random one.")
                best_move = random.choice(legal_moves)
            else:
                print(f"AI ({self.ai_color.upper()}) has no legal moves.")
                return

        start_pos, end_pos = best_move
        start_row, start_col = start_pos
        end_row, end_col = end_pos

        print(
            f"AI chooses to move from {chr(ord('a') + start_col)}{8 - start_row} to {chr(ord('a') + end_col)}{8 - end_row}")


        self.game.move_piece(start_row, start_col, end_row, end_col)
        self.game.check_game_end_conditions()


    def _evaluate_board(self, game_state):
        score = 0

        for r in range(8):
            for c in range(8):
                piece = game_state.board[r][c]
                if piece:
                    piece_color = game_state.get_piece_color(piece)
                    piece_type = piece[2:]

                    value = self.piece_values.get(piece_type, 0)
                    position_score = self._get_piece_position_score(piece_type, r, c, game_state.board)

                    if piece_type in ['knight', 'bishop'] and (
                            (piece_color == 'white' and r == 7) or (piece_color == 'black' and r == 0)):
                        position_score -= 50

                    if piece_color == self.ai_color:
                        score += value + position_score
                    else:
                        score -= value + position_score

        return score

    def _get_piece_position_score(self, piece_type, row, col, board_state):
        piece_on_board = board_state[row][col]
        piece_color = self.game.get_piece_color(piece_on_board)

        if piece_color == 'black':
            row = 7 - row

        if piece_type == 'pawn':
            return self.pawn_table[row][col]
        if piece_type == 'knight':
            return self.knight_table[row][col]
        if piece_type == 'bishop':
            return self.bishop_table[row][col]
        if piece_type == 'rook':
            return self.rook_table[row][col]
        if piece_type == 'queen':
            return self.queen_table[row][col]

        num_pieces = sum(1 for r in board_state for p in r if p is not None)
        if num_pieces > 10:
            return self.king_table_middle_game[row][col]
        else:
            return self.king_table_end_game[row][col]

        return 0

    def _minimax(self, game_state, depth, alpha, beta, player_color):
        if depth == 0 or game_state.game_over:
            return None, self._evaluate_board(game_state)

        legal_moves = game_state.get_all_legal_moves(player_color)

        is_king_in_check = game_state.is_king_in_check(player_color, game_state.board)
        if not legal_moves:
            if is_king_in_check:
                return None, -float('inf') if player_color == self.ai_color else float('inf')
            else:
                return None, 0  # Stalemate

        best_move = None

        if player_color == self.ai_color:
            max_eval = -float('inf')
            for move in legal_moves:
                start_pos, end_pos = move
                start_row, start_col = start_pos
                end_row, end_col = end_pos

                temp_game = copy.deepcopy(game_state)
                temp_game.move_piece(start_row, start_col, end_row, end_col)
                temp_game.check_game_end_conditions()

                _, eval = self._minimax(temp_game, depth - 1, alpha, beta,
                                        'white' if self.ai_color == 'black' else 'black')

                if eval > max_eval:
                    max_eval = eval
                    best_move = move

                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return best_move, max_eval

        else:
            min_eval = float('inf')
            for move in legal_moves:
                start_pos, end_pos = move
                start_row, start_col = start_pos
                end_row, end_col = end_pos

                temp_game = copy.deepcopy(game_state)
                temp_game.move_piece(start_row, start_col, end_row, end_col)
                temp_game.check_game_end_conditions()

                _, eval = self._minimax(temp_game, depth - 1, alpha, beta, self.ai_color)

                if eval < min_eval:
                    min_eval = eval
                    best_move = move

                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return best_move, min_eval


