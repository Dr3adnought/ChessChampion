"""
Pawn promotion dialog for selecting promotion piece.
"""
import pygame
from typing import Optional, Tuple

from game.types import PieceType, Color


class PromotionDialog:
    """Dialog for selecting pawn promotion piece."""
    
    def __init__(self, screen: pygame.Surface, piece_images: dict, color: Color):
        """
        Initialize the promotion dialog.
        
        Args:
            screen: Pygame screen surface
            piece_images: Dictionary of piece images
            color: Color of the promoting pawn
        """
        self.screen = screen
        self.piece_images = piece_images
        self.color = color
        self.selected_piece: Optional[PieceType] = None
        
        # Dialog dimensions
        self.dialog_width = 400
        self.dialog_height = 200
        self.dialog_x = (screen.get_width() - self.dialog_width) // 2
        self.dialog_y = (screen.get_height() - self.dialog_height) // 2
        
        # Piece options
        self.promotion_options = [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT
        ]
        
        # Create piece selection rectangles
        self.piece_rects = []
        piece_size = 80
        spacing = 20
        total_width = len(self.promotion_options) * piece_size + (len(self.promotion_options) - 1) * spacing
        start_x = self.dialog_x + (self.dialog_width - total_width) // 2
        start_y = self.dialog_y + 80
        
        for i, piece_type in enumerate(self.promotion_options):
            x = start_x + i * (piece_size + spacing)
            rect = pygame.Rect(x, start_y, piece_size, piece_size)
            self.piece_rects.append(rect)
        
        # Fonts
        self.title_font = pygame.font.Font(None, 42)
        self.label_font = pygame.font.Font(None, 24)
    
    def draw(self):
        """Draw the promotion dialog."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog background
        dialog_rect = pygame.Rect(self.dialog_x, self.dialog_y, self.dialog_width, self.dialog_height)
        pygame.draw.rect(self.screen, (60, 60, 60), dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 200), dialog_rect, width=3, border_radius=10)
        
        # Title
        title_text = self.title_font.render("Promote Pawn To:", True, (255, 255, 255))
        title_rect = title_text.get_rect(centerx=self.dialog_x + self.dialog_width // 2, y=self.dialog_y + 20)
        self.screen.blit(title_text, title_rect)
        
        # Draw piece options
        mouse_pos = pygame.mouse.get_pos()
        color_prefix = 'w' if self.color == Color.WHITE else 'b'
        
        for i, (piece_type, rect) in enumerate(zip(self.promotion_options, self.piece_rects)):
            # Highlight on hover
            is_hovering = rect.collidepoint(mouse_pos)
            
            if is_hovering:
                hover_color = (100, 150, 200)
                pygame.draw.rect(self.screen, hover_color, rect, border_radius=8)
            
            # Border
            border_color = (255, 215, 0) if is_hovering else (200, 200, 200)
            pygame.draw.rect(self.screen, border_color, rect, width=3, border_radius=8)
            
            # Draw piece image
            piece_name_map = {
                PieceType.QUEEN: 'queen',
                PieceType.ROOK: 'rook',
                PieceType.BISHOP: 'bishop',
                PieceType.KNIGHT: 'knight'
            }
            piece_key = f"{color_prefix}_{piece_name_map[piece_type]}"
            piece_image = self.piece_images.get(piece_key)
            
            if piece_image:
                # Scale piece to fit in rect
                scaled_image = pygame.transform.scale(piece_image, (rect.width, rect.height))
                self.screen.blit(scaled_image, rect.topleft)
            
            # Label below
            label_text = self.label_font.render(piece_type.value.capitalize(), True, (200, 200, 200))
            label_rect = label_text.get_rect(centerx=rect.centerx, y=rect.bottom + 5)
            self.screen.blit(label_text, label_rect)
    
    def handle_click(self, pos: Tuple[int, int]) -> Optional[PieceType]:
        """
        Handle mouse click on the dialog.
        
        Args:
            pos: Mouse position (x, y)
        
        Returns:
            Selected PieceType if a piece was clicked, None otherwise
        """
        for piece_type, rect in zip(self.promotion_options, self.piece_rects):
            if rect.collidepoint(pos):
                self.selected_piece = piece_type
                return piece_type
        
        return None
    
    def run(self) -> PieceType:
        """
        Run the promotion dialog and wait for user selection.
        
        Returns:
            Selected PieceType (defaults to Queen if dialog is closed)
        """
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Default to Queen if user quits
                    return PieceType.QUEEN
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    selected = self.handle_click(event.pos)
                    if selected:
                        return selected
                elif event.type == pygame.KEYDOWN:
                    # Keyboard shortcuts for quick selection
                    if event.key == pygame.K_q:
                        return PieceType.QUEEN
                    elif event.key == pygame.K_r:
                        return PieceType.ROOK
                    elif event.key == pygame.K_b:
                        return PieceType.BISHOP
                    elif event.key == pygame.K_n or event.key == pygame.K_k:
                        return PieceType.KNIGHT
                    elif event.key == pygame.K_ESCAPE:
                        # Default to Queen on ESC
                        return PieceType.QUEEN
            
            # Draw the dialog
            self.draw()
            pygame.display.flip()
            clock.tick(60)
