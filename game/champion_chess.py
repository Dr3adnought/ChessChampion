import copy
import random
import pygame



class ChessGame:
    def __init__(self):
        self.board = [
            ['b_rook', 'b_knight', 'b_bishop', 'b_queen', 'b_king', 'b_bishop', 'b_knight', 'b_rook'],
            ['b_pawn', 'b_pawn', 'b_pawn', 'b_pawn', 'b_pawn', 'b_pawn', 'b_pawn', 'b_pawn'],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            ['w_pawn', 'w_pawn', 'w_pawn', 'w_pawn', 'w_pawn', 'w_pawn', 'w_pawn', 'w_pawn'],
            ['w_rook', 'w_knight', 'w_bishop', 'w_queen', 'w_king', 'w_bishop', 'w_knight', 'w_rook']
        ]
        self.turn = 'white'
        self.selected_square = None
        self.selected_piece_type = None
        self.game_over = False

        self.white_king_moved = False
        self.black_king_moved = False
        self.white_kingside_rook_moved = False
        self.white_queenside_rook_moved = False
        self.black_kingside_rook_moved = False
        self.black_queenside_rook_moved = False

        self.last_pawn_double_move = None

    def handle_click(self, clicked_row, clicked_col, ai_player_color=None):
        if self.game_over:
            print("Game is over!")
            return

        if ai_player_color and self.turn == ai_player_color:
            return

        piece_on_clicked_square = self.board[clicked_row][clicked_col]

        if self.selected_square:
            start_row, start_col = self.selected_square
            if self.is_valid_move(start_row, start_col, clicked_row, clicked_col):
                self.move_piece(start_row, start_col, clicked_row, clicked_col)
                self.selected_square = None
                self.selected_piece_type = None
                self.check_game_end_conditions()
            else:
                print(f"Invalid move from {self.selected_square} to {(clicked_row, clicked_col)}")
                if piece_on_clicked_square and self.get_piece_color(piece_on_clicked_square) == self.turn:
                    self.selected_square = (clicked_row, clicked_col)
                    self.selected_piece_type = piece_on_clicked_square
                else:
                    self.selected_square = None
                    self.selected_piece_type = None
        else:
            if piece_on_clicked_square:
                if self.get_piece_color(piece_on_clicked_square) == self.turn:
                    self.selected_square = (clicked_row, clicked_col)
                    self.selected_piece_type = piece_on_clicked_square
                else:
                    print(f"It's {self.turn}'s turn. Cannot select opponent's piece.")

    def get_piece_color(self, piece_str):
        if piece_str:
            return 'white' if piece_str.startswith('w_') else 'black'
        return None

    def find_king_position(self, color, board_state):
        king_piece = f"{color[0]}_king"
        for r in range(8):
            for c in range(8):
                if board_state[r][c] == king_piece:
                    return (r, c)
        return None

    def is_king_in_check(self, color, current_board=None):
        board_to_check = current_board if current_board is not None else self.board
        king_pos = self.find_king_position(color, board_to_check)
        if king_pos is None:
            return False

        king_row, king_col = king_pos
        opponent_color = 'black' if color == 'white' else 'white'

        for r in range(8):
            for c in range(8):
                piece = board_to_check[r][c]
                if piece and self.get_piece_color(piece) == opponent_color:
                    if self._is_valid_move_internal(r, c, king_row, king_col, board_to_check, opponent_color):
                        return True
        return False

    def is_valid_castling(self, start_row, start_col, end_row, end_col):
        piece = self.board[start_row][start_col]
        if piece is None or piece[2:] != 'king' or abs(start_col - end_col) != 2 or start_row != end_row:
            return False

        king_color = self.get_piece_color(piece)

        if king_color == 'white' and self.white_king_moved:
            return False
        if king_color == 'black' and self.black_king_moved:
            return False


        kingside = end_col > start_col
        rook_start_col = 7 if kingside else 0
        rook_end_col = 5 if kingside else 3


        if king_color == 'white':
            if kingside and self.white_kingside_rook_moved:
                return False
            if not kingside and self.white_queenside_rook_moved:
                return False
        else:
            if kingside and self.black_kingside_rook_moved:
                return False
            if not kingside and self.black_queenside_rook_moved:
                return False

        # path_cols = []
        if kingside:
            path_cols = [start_col + 1, start_col + 2]
        else:
            path_cols = [start_col - 1, start_col - 2]

        for col in path_cols:
            if self.board[start_row][col] is not None:
                return False

        if kingside:
            for c in range (start_col + 1, rook_start_col + 1):
                if self.board[start_row][c] is not None and (c != rook_start_col or self.board[start_row][c] != f"{king_color[0]}_rook"):
                    if c != rook_start_col:
                        return False
                    elif self.board[start_row][c] != f"{king_color[0]}_rook":
                        return False
        else:
            for c in range(rook_start_col, start_col):
                if self.board[start_row][c] is not None and (
                        c != rook_start_col or self.board[start_row][c] != f"{king_color[0]}_rook"):
                    if c != rook_start_col:
                        return False
                    elif self.board[start_row][c] != f"{king_color[0]}_rook":
                        return False

        if self.is_king_in_check(king_color):
            print("Cannot castle: King is currently in check.")
            return False

        squares_to_check = [(start_row, start_col)]  # Start square
        if kingside:
            squares_to_check.extend([(start_row, start_col + 1), (start_row, start_col + 2)])
        else:
            squares_to_check.extend([(start_row, start_col - 1), (start_row, start_col - 2)])

        for r, c in squares_to_check:
            temp_board = copy.deepcopy(self.board)
            temp_board[r][c] = piece
            if (r, c) != (start_row, start_col):
                temp_board[start_row][start_col] = None

            if self.is_king_in_check(king_color, current_board=temp_board):
                print(f"Cannot castle: King passes through or lands on an attacked square ({(r, c)}).")
                return False

        return True

    def is_valid_move(self, start_row, start_col, end_row, end_col):
        piece = self.board[start_row][start_col]

        if piece and piece[2:] == 'king' and abs(start_col - end_col) == 2 and start_row == end_row:
            if self.is_valid_castling(start_row, start_col, end_row, end_col):
                return True

        if piece and piece[2:] == 'pawn':
            if abs(start_col - end_col) == 1 and self.board[end_row][end_col] is None:
                captured_pawn_row = start_row
                captured_pawn_col = end_col

                if self.last_pawn_double_move == (captured_pawn_row, captured_pawn_col):
                    opponent_pawn = self.board[captured_pawn_row][captured_pawn_col]
                    if opponent_pawn and opponent_pawn[2:] == 'pawn' and \
                        self.get_piece_color(opponent_pawn) != self.turn:

                        temp_board = copy.deepcopy(self.board)
                        temp_board[end_row][end_col] = piece
                        temp_board[start_row][start_col] = None
                        temp_board[captured_pawn_row][captured_pawn_col] = None

                        if not self.is_king_in_check(self.turn, current_board=temp_board):
                            return True

        if not self._is_valid_move_internal(start_row, start_col, end_row, end_col, self.board, self.turn):
            return False

        temp_board = copy.deepcopy(self.board)
        piece_to_move = temp_board[start_row][start_col]
        temp_board[end_row][end_col] = piece_to_move
        temp_board[start_row][start_col] = None

        if self.is_king_in_check(self.turn, current_board=temp_board):
            print(f"Move from {self.selected_square} to {(end_row, end_col)} is invalid: King would be in check.")
            return False

        return True

    # --- _is_valid_move_internal ---
    def _is_valid_move_internal(self, start_row, start_col, end_row, end_col, board_state, current_player_color):
        if not (0 <= start_row < 8 and 0 <= start_col < 8 and
                0 <= end_row < 8 and 0 <= end_col < 8):
            return False

        piece = board_state[start_row][start_col]
        if not piece:
            return False

        if self.get_piece_color(piece) != current_player_color:
            return False

        destination_piece = board_state[end_row][end_col]
        if destination_piece and self.get_piece_color(destination_piece) == current_player_color:
            return False

        piece_type = piece[2:]

        if piece_type == 'pawn':
            direction = -1 if current_player_color == 'white' else 1
            start_rank = 6 if current_player_color == 'white' else 1

            if start_col == end_col and end_row == start_row + direction:
                return board_state[end_row][end_col] is None

            if start_col == end_col and start_row == start_rank and end_row == start_row + 2 * direction:
                mid_row = start_row + direction
                return board_state[mid_row][end_col] is None and board_state[end_row][end_col] is None

            if abs(start_col - end_col) == 1 and end_row == start_row + direction:
                return board_state[end_row][end_col] is not None and self.get_piece_color(board_state[end_row][end_col]) != current_player_color

            return False

        elif piece_type == 'rook':
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for c in range(start_col + step, end_col, step):
                    if board_state[start_row][c] is not None:
                        return False
                return True
            elif start_col == end_col:
                step = 1 if end_row > start_row else -1
                for r in range(start_row + step, end_row, step):
                    if board_state[r][start_col] is not None:
                        return False
                return True
            return False

        elif piece_type == 'knight':
            dr = abs(start_row - end_row)
            dc = abs(start_col - end_col)
            return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)

        elif piece_type == 'bishop':
            if abs(start_row - end_row) == abs(start_col - end_col):
                row_step = 1 if end_row > start_row else -1
                col_step = 1 if end_col > start_col else -1
                r, c = start_row + row_step, start_col + col_step
                while r != end_row:
                    if board_state[r][c] is not None:
                        return False
                    r += row_step
                    c += col_step
                return True
            return False

        elif piece_type == 'queen':
            if start_row == end_row:
                step = 1 if end_col > start_col else -1
                for c in range(start_col + step, end_col, step):
                    if board_state[start_row][c] is not None:
                        return False
                return True
            elif start_col == end_col:
                step = 1 if end_row > start_row else -1
                for r in range(start_row + step, end_row, step):
                    if board_state[r][start_col] is not None:
                        return False
                return True
            elif abs(start_row - end_row) == abs(start_col - end_col):
                row_step = 1 if end_row > start_row else -1
                col_step = 1 if end_col > start_col else -1
                r, c = start_row + row_step, start_col + col_step
                while r != end_row:
                    if board_state[r][c] is not None:
                        return False
                    r += row_step
                    c += col_step
                return True
            return False

        elif piece_type == 'king':
            dr = abs(start_row - end_row)
            dc = abs(start_col - end_col)
            return (dr <= 1 and dc <= 1) and not (dr == 0 and dc == 0)

        return False

    def move_piece(self, start_row, start_col, end_row, end_col):
        piece_to_move = self.board[start_row][start_col]

        self.last_pawn_double_move = None

        if piece_to_move and piece_to_move[2:] == 'king' and abs(start_col - end_col) == 2 and start_row == end_row:
            kingside = end_col > start_col

            self.board[end_row][end_col] = piece_to_move
            self.board[start_row][start_col] = None

            if kingside:
                rook_start_col = 7
                rook_end_col = 5
            else:
                rook_start_col = 0
                rook_end_col = 3


            rook_piece = self.board[start_row][rook_start_col]
            self.board[start_row][rook_end_col] = rook_piece
            self.board[start_row][rook_start_col] = None
            print(f"Castling performed: {self.get_piece_color(piece_to_move)} {('kingside' if kingside else 'queenside')}.")

        elif piece_to_move and piece_to_move[2:] == 'pawn' and \
            abs(start_col - end_col) == 1 and self.board[end_row][end_col] is None:

            captured_pawn_row = start_row
            captured_pawn_col = end_col
            self.board[captured_pawn_row][captured_pawn_col] = None

            self.board[end_row][end_col] = piece_to_move
            self.board[start_row][start_col] = None
            print(f"En Passant capture by {self.get_piece_color(piece_to_move)} pawn!")

        else:
            self.board[end_row][end_col] = piece_to_move
            self.board[start_row][start_col] = None

            if piece_to_move and piece_to_move[2:] == 'pawn' and abs(start_row - end_row) == 2:
                self.last_pawn_double_move = (end_row, end_col)
                print(f"Pawn double move recorded at {self.last_pawn_double_move}.")

            if piece_to_move and piece_to_move[2:] == 'pawn':
                if (self.get_piece_color(piece_to_move) == 'white' and end_row == 0) or \
                   (self.get_piece_color(piece_to_move) == 'black' and end_row == 7):

                    promoted_piece = f"{self.get_piece_color(piece_to_move)[0]}_queen"
                    self.board[end_row][end_col] = promoted_piece
                    print(f"Pawn promoted to {promoted_piece.upper()}!")

        if piece_to_move == 'w_king':
            self.white_king_moved = True
        elif piece_to_move == 'b_king':
            self.black_king_moved = True
        elif piece_to_move == 'w_rook':
            if start_row == 7 and start_col == 7: self.white_kingside_rook_moved = True
            if start_row == 7 and start_col == 0: self.white_queenside_rook_moved = True
        elif piece_to_move == 'b_rook':
            if start_row == 0 and start_col == 7: self.black_kingside_rook_moved = True
            if start_row == 0 and start_col == 0: self.black_queenside_rook_moved = True

        self.turn = 'black' if self.turn == 'white' else 'white'
        print(f"Move made. It's now {self.turn}'s turn.")

    def get_all_legal_moves(self, color):
        legal_moves = []
        for start_row in range(8):
            for start_col in range(8):
                piece = self.board[start_row][start_col]
                if piece and self.get_piece_color(piece) == color:
                    for end_row in range(8):
                        for end_col in range(8):
                            if self.is_valid_move(start_row, start_col, end_row, end_col):
                                legal_moves.append(((start_row, start_col), (end_row,end_col)))
        return legal_moves

    def check_game_end_conditions(self):
        current_player_color = self.turn
        is_king_currently_in_check = self.is_king_in_check(current_player_color)

        all_possible_moves = self.get_all_legal_moves(current_player_color)

        if not all_possible_moves:
            if is_king_currently_in_check:
                print(f"\n!!! CHECKMATE !!! {current_player_color.upper()} KING IS CHECKMATED!")
                winning_color = 'white' if current_player_color == 'black' else 'black'
                print(f"{winning_color.upper()} WINS!")
                self.game_over = True
            else:
                print(f"\n!!! STALEMATE !!! No legal moves for {current_player_color.upper()}.")
                print("It's a DRAW!")
                self.game_over = True
        elif is_king_currently_in_check:
            print(f"!!! {current_player_color.upper()} KING IS IN CHECK !!!")

    def draw(self, screen, square_size, light_color, dark_color, highlight_color, pieces_images):
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    color = light_color
                else:
                    color = dark_color
                pygame.draw.rect(screen, color, (col * square_size, row * square_size, square_size, square_size))

                if self.selected_square and self.selected_square == (row, col):
                    s = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                    s.fill(highlight_color)
                    screen.blit(s, (col * square_size, row * square_size))

                piece_key = self.board[row][col]
                if piece_key:
                    piece_image = pieces_images.get(piece_key)
                    if piece_image:
                        screen.blit(piece_image, (col * square_size, row * square_size))