"""
Chess timer for time control management.
Tracks time for both players with increment support.
"""
import time
from typing import Optional, Tuple
from game.types import Color


class TimeControl:
    """Manages chess clock with time controls and increments."""
    
    def __init__(self, minutes: int, increment_seconds: int):
        """
        Initialize time control.
        
        Args:
            minutes: Starting time in minutes for each player (0 for untimed)
            increment_seconds: Seconds added after each move (Fischer increment)
        """
        self.base_time = minutes * 60  # Convert to seconds
        self.increment = increment_seconds
        self.is_timed = minutes > 0
        
        # Time remaining for each player (in seconds)
        self.white_time = float(self.base_time)
        self.black_time = float(self.base_time)
        
        # Track when current player's turn started
        self.turn_start_time: Optional[float] = None
        self.current_player: Optional[Color] = None
        self.is_paused = True
    
    def start_turn(self, color: Color):
        """Start timing for a player's turn."""
        if not self.is_timed:
            return
        
        self.current_player = color
        self.turn_start_time = time.time()
        self.is_paused = False
    
    def end_turn(self, color: Color, apply_increment: bool = True):
        """
        End timing for a player's turn and apply increment.
        
        Args:
            color: The player whose turn just ended
            apply_increment: Whether to add increment time (True after valid move)
        """
        if not self.is_timed or self.is_paused:
            return
        
        # Update time used
        self.update_time()
        
        # Apply increment if move was made
        if apply_increment:
            if color == Color.WHITE:
                self.white_time += self.increment
            else:
                self.black_time += self.increment
        
        self.is_paused = True
        self.turn_start_time = None
    
    def update_time(self):
        """Update the current player's time based on elapsed time."""
        if not self.is_timed or self.is_paused or self.turn_start_time is None:
            return
        
        elapsed = time.time() - self.turn_start_time
        self.turn_start_time = time.time()  # Reset for next update
        
        if self.current_player == Color.WHITE:
            self.white_time -= elapsed
        else:
            self.black_time -= elapsed
    
    def pause(self):
        """Pause the timer (e.g., during animations or AI thinking)."""
        if not self.is_timed or self.is_paused:
            return
        
        self.update_time()
        self.is_paused = True
    
    def resume(self):
        """Resume the timer."""
        if not self.is_timed or not self.is_paused:
            return
        
        self.turn_start_time = time.time()
        self.is_paused = False
    
    def get_time(self, color: Color) -> float:
        """
        Get remaining time for a player.
        
        Args:
            color: The player color
            
        Returns:
            Remaining time in seconds
        """
        if not self.is_timed:
            return float('inf')
        
        # If it's this player's turn, update their time first
        if not self.is_paused and self.current_player == color:
            self.update_time()
        
        return self.white_time if color == Color.WHITE else self.black_time
    
    def is_time_out(self, color: Color) -> bool:
        """
        Check if a player has run out of time.
        
        Args:
            color: The player color
            
        Returns:
            True if player's time is <= 0
        """
        if not self.is_timed:
            return False
        
        return self.get_time(color) <= 0
    
    def format_time(self, color: Color) -> str:
        """
        Format time as MM:SS or HH:MM:SS.
        
        Args:
            color: The player color
            
        Returns:
            Formatted time string
        """
        if not self.is_timed:
            return "∞"
        
        total_seconds = max(0, self.get_time(color))
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def get_display_color(self, color: Color) -> Tuple[int, int, int]:
        """
        Get RGB color for time display based on remaining time.
        
        Args:
            color: The player color
            
        Returns:
            RGB tuple (white, yellow < 20s, red < 10s)
        """
        if not self.is_timed:
            return (255, 255, 255)  # White
        
        remaining = self.get_time(color)
        
        if remaining <= 10:
            return (255, 50, 50)  # Red
        elif remaining <= 20:
            return (255, 200, 50)  # Yellow
        else:
            return (255, 255, 255)  # White
    
    def reset(self):
        """Reset timer to initial state."""
        self.white_time = float(self.base_time)
        self.black_time = float(self.base_time)
        self.turn_start_time = None
        self.current_player = None
        self.is_paused = True
