"""
AI player using minimax algorithm with alpha-beta pruning.
Refactored to work with the new architecture.
"""
import random
from typing import Optional, Tuple

from game.types import Color, Position, Move, PieceType
from game.game_state import GameState


class AIPlayer:
    """
    AI player that uses minimax with alpha-beta pruning to select moves.
    """
    
    def __init__(self, game_instance, ai_color: str, depth: int = 2):
        """
        Initialize the AI player.
        
        Args:
            game_instance: ChessGame instance
            ai_color: 'white' or 'black'
            depth: Search depth for minimax
        """
        self.game = game_instance
        self.ai_color_str = ai_color
        self.ai_color = Color.WHITE if ai_color == 'white' else Color.BLACK
        self.depth = depth
        
        # Piece values
        self.piece_values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000
        }
        
        # Position tables for piece-square evaluation (consolidated in dict)
        self.position_tables = {
            PieceType.PAWN: [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [0, 0, 0, 20, 20, 0, 0, 0],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            PieceType.KNIGHT: [
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            PieceType.BISHOP: [
                [-20, -10, -10, -10, -10, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 5, 10, 10, 5, 0, -10],
                [-10, 5, 5, 10, 10, 5, 5, -10],
                [-10, 0, 10, 10, 10, 10, 0, -10],
                [-10, 10, 10, 10, 10, 10, 10, -10],
                [-10, 5, 0, 0, 0, 0, 5, -10],
                [-20, -10, -10, -10, -10, -10, -10, -20]
            ],
            PieceType.ROOK: [
                [0, 0, 0, 5, 5, 0, 0, 0],
                [5, 10, 10, 10, 10, 10, 10, 5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [-5, 0, 0, 0, 0, 0, 0, -5],
                [0, 0, 0, 5, 5, 0, 0, 0]
            ],
            PieceType.QUEEN: [
                [-20, -10, -10, -5, -5, -10, -10, -20],
                [-10, 0, 0, 0, 0, 0, 0, -10],
                [-10, 0, 5, 5, 5, 5, 0, -10],
                [-5, 0, 5, 5, 5, 5, 0, -5],
                [0, 0, 5, 5, 5, 5, 0, -5],
                [-10, 5, 5, 5, 5, 5, 0, -10],
                [-10, 0, 5, 0, 0, 0, 0, -10],
                [-20, -10, -10, -5, -5, -10, -10, -20]
            ]
        }
        
        # King tables are separate for middlegame/endgame
        self.king_tables = {
            'middlegame': [
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-20, -30, -30, -40, -40, -30, -30, -20],
                [-10, -20, -20, -20, -20, -20, -20, -10],
                [20, 20, 0, 0, 0, 0, 20, 20],
                [20, 30, 10, 0, 0, 10, 30, 20]
            ],
            'endgame': [
                [-50, -40, -30, -20, -20, -30, -40, -50],
                [-30, -20, -10, 0, 0, -10, -20, -30],
                [-30, -10, 20, 30, 30, 20, -10, -30],
                [-30, -10, 30, 40, 40, 30, -10, -30],
                [-30, -10, 30, 40, 40, 30, -10, -30],
                [-30, -10, 20, 30, 30, 20, -10, -30],
                [-30, -30, 0, 0, 0, 0, -30, -30],
                [-50, -30, -30, -30, -30, -30, -30, -50]
            ]
        }
    
    def make_move(self):
        """Make the AI's move."""
        if self.game.game_state.is_game_over():
            return
        
        print(f"AI ({self.ai_color_str.upper()}) is thinking with depth {self.depth}...")
        
        # Get best move using minimax
        best_move = self._get_best_move()
        
        if not best_move:
            print(f"AI ({self.ai_color_str.upper()}) has no legal moves.")
            return
        
        # Execute the move
        print(f"AI chooses to move from {best_move.from_pos} to {best_move.to_pos}")
        
        if self.game.game_state.make_move(best_move):
            self.game.last_move = (best_move.from_pos, best_move.to_pos)
        else:
            print("AI move failed!")
    
    def _get_best_move(self) -> Optional[Move]:
        """Get the best move using minimax with alpha-beta pruning."""
        best_move, _ = self._minimax(
            self.game.game_state,
            self.depth,
            -float('inf'),
            float('inf'),
            True
        )
        
        # If minimax doesn't find a move, pick a random legal one
        if not best_move:
            legal_moves = self.game.game_state.get_all_legal_moves()
            if legal_moves:
                print("Minimax didn't find a best move, choosing randomly.")
                best_move = random.choice(legal_moves)
        
        return best_move
    
    def _minimax(self, game_state: GameState, depth: int, alpha: float, beta: float, 
                 is_maximizing: bool) -> Tuple[Optional[Move], float]:
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            game_state: Current game state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing: True if maximizing player (AI), False otherwise
        
        Returns:
            Tuple of (best_move, evaluation_score)
        """
        # Base case: depth reached or game over
        if depth == 0 or game_state.is_game_over():
            return None, self._evaluate_position(game_state)
        
        # Get legal moves for current player
        legal_moves = game_state.get_all_legal_moves()
        
        if not legal_moves:
            # No legal moves - checkmate or stalemate
            if game_state.validator.is_king_in_check(game_state.current_turn):
                # Checkmate - very bad if we're in check
                return None, -float('inf') if is_maximizing else float('inf')
            else:
                # Stalemate
                return None, 0
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in legal_moves:
                # Make move on copy
                new_state = game_state.copy()
                new_state.make_move(move)
                
                # Recursively evaluate
                _, eval_score = self._minimax(new_state, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                # Make move on copy
                new_state = game_state.copy()
                new_state.make_move(move)
                
                # Recursively evaluate
                _, eval_score = self._minimax(new_state, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return best_move, min_eval
    
    def _evaluate_position(self, game_state: GameState) -> float:
        """
        Evaluate the current position.
        Positive score favors AI, negative favors opponent.
        """
        score = 0.0
        
        # Count pieces on board for endgame detection
        piece_count = len(game_state.board.get_all_pieces())
        is_endgame = piece_count <= 10
        
        # Evaluate each piece
        for position, piece in game_state.board.get_all_pieces():
            # Material value
            piece_value = self.piece_values[piece.piece_type]
            
            # Position value
            position_value = self._get_position_value(piece.piece_type, position, piece.color, is_endgame)
            
            total_value = piece_value + position_value
            
            # Add to score (positive for AI, negative for opponent)
            if piece.color == self.ai_color:
                score += total_value
            else:
                score -= total_value
        
        return score
    
    def _get_position_value(self, piece_type: PieceType, position: Position, 
                           color: Color, is_endgame: bool) -> float:
        """Get the positional value of a piece."""
        row = position.row
        col = position.col
        
        # Flip row for black pieces (tables are from white's perspective)
        if color == Color.BLACK:
            row = 7 - row
        
        # Get value from appropriate table
        if piece_type == PieceType.KING:
            # King has special handling for middlegame/endgame
            table_key = 'endgame' if is_endgame else 'middlegame'
            return self.king_tables[table_key][row][col]
        else:
            # All other pieces use the consolidated table
            table = self.position_tables.get(piece_type)
            return table[row][col] if table else 0.0
