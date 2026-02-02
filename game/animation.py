"""
Piece animation system for smooth visual transitions.
"""
import pygame
from typing import Optional, Tuple
from game.types import Position


class PieceAnimation:
    """Handles smooth animation of a piece moving from one square to another."""
    
    def __init__(self, from_pos: Position, to_pos: Position, piece_image: pygame.Surface, 
                 square_size: int, duration_ms: int = 300):
        """
        Initialize a piece animation.
        
        Args:
            from_pos: Starting position
            to_pos: Ending position
            piece_image: Image of the piece being moved
            square_size: Size of each square in pixels
            duration_ms: Animation duration in milliseconds
        """
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.piece_image = piece_image
        self.square_size = square_size
        self.duration_ms = duration_ms
        
        # Calculate pixel positions
        self.start_x = from_pos.col * square_size
        self.start_y = from_pos.row * square_size
        self.end_x = to_pos.col * square_size
        self.end_y = to_pos.row * square_size
        
        # Animation state
        self.start_time = pygame.time.get_ticks()
        self.is_complete = False
    
    def update(self) -> Tuple[int, int]:
        """
        Update animation and return current pixel position.
        
        Returns:
            (x, y) pixel position of the piece
        """
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        if elapsed >= self.duration_ms:
            self.is_complete = True
            return (self.end_x, self.end_y)
        
        # Linear interpolation with easing
        progress = elapsed / self.duration_ms
        # Apply ease-out effect for smoother animation
        progress = 1 - (1 - progress) ** 3
        
        current_x = self.start_x + (self.end_x - self.start_x) * progress
        current_y = self.start_y + (self.end_y - self.start_y) * progress
        
        return (int(current_x), int(current_y))
    
    def draw(self, screen: pygame.Surface):
        """Draw the animated piece at its current position."""
        x, y = self.update()
        screen.blit(self.piece_image, (x, y))


class AnimationManager:
    """Manages piece animations and timing delays."""
    
    def __init__(self):
        """Initialize the animation manager."""
        self.current_animation: Optional[PieceAnimation] = None
        self.delay_end_time: Optional[int] = None
        self.is_delaying = False
    
    def start_animation(self, from_pos: Position, to_pos: Position, piece_image: pygame.Surface,
                       square_size: int, duration_ms: int = 300):
        """
        Start a new piece animation.
        
        Args:
            from_pos: Starting position
            to_pos: Ending position
            piece_image: Image of the piece
            square_size: Size of each square
            duration_ms: Animation duration in milliseconds
        """
        self.current_animation = PieceAnimation(from_pos, to_pos, piece_image, square_size, duration_ms)
    
    def start_delay(self, delay_ms: int):
        """
        Start a timing delay before next action.
        
        Args:
            delay_ms: Delay duration in milliseconds
        """
        self.is_delaying = True
        self.delay_end_time = pygame.time.get_ticks() + delay_ms
    
    def is_animating(self) -> bool:
        """Check if an animation is currently in progress."""
        return self.current_animation is not None and not self.current_animation.is_complete
    
    def is_delay_active(self) -> bool:
        """Check if a delay is currently active."""
        if not self.is_delaying:
            return False
        
        if pygame.time.get_ticks() >= self.delay_end_time:
            self.is_delaying = False
            return False
        
        return True
    
    def is_busy(self) -> bool:
        """Check if animation or delay is in progress."""
        return self.is_animating() or self.is_delay_active()
    
    def draw_animation(self, screen: pygame.Surface):
        """Draw the current animation if active."""
        if self.current_animation and not self.current_animation.is_complete:
            self.current_animation.draw(screen)
    
    def clear(self):
        """Clear current animation."""
        self.current_animation = None
