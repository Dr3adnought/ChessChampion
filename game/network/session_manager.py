"""In-process authoritative session manager for Online PvP Phase A."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import secrets
import string
from typing import Any
from uuid import uuid4

from game.champion_chess import ChessGame
from game.network.protocol_contract import PROTOCOL_VERSION, validate_envelope
from game.state_fingerprint import fingerprint_game_state
from game.types import Color, Move, PieceType, Position


@dataclass
class _PlayerState:
    player_id: str
    side: Color
    resume_token: str
    resume_token_expires_at: datetime
    last_sequence: int = -1
    seen_event_ids: set[str] = field(default_factory=set)


@dataclass
class _GameSession:
    game_id: str
    invite_code: str
    host_player_id: str
    game: ChessGame
    players: dict[str, _PlayerState]
    server_sequence: int = 0


class SessionManager:
    """Server-authoritative game/session manager for host/join flows."""

    def __init__(self, reconnect_ttl_minutes: int = 30):
        self._sessions_by_game_id: dict[str, _GameSession] = {}
        self._game_id_by_invite_code: dict[str, str] = {}
        self._reconnect_ttl = timedelta(minutes=reconnect_ttl_minutes)

    def process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Process one protocol envelope and return emitted server events."""
        valid, error = validate_envelope(message)
        if not valid:
            return {"ok": False, "error": error, "events": []}

        event_type = message["event_type"]
        if event_type == "host_create":
            return self._handle_host_create(message)
        if event_type == "join_request":
            return self._handle_join_request(message)
        if event_type == "move_intent":
            return self._handle_move_intent(message)
        if event_type == "state_resync_request":
            return self._handle_state_resync_request(message)
        if event_type == "reconnect_request":
            return self._handle_reconnect_request(message)

        return {"ok": False, "error": f"unsupported event_type for manager: {event_type}", "events": []}

    def _handle_host_create(self, message: dict[str, Any]) -> dict[str, Any]:
        payload = message["payload"]
        requested_side = payload.get("requested_side", "white")
        host_side = Color.WHITE if requested_side == "white" else Color.BLACK

        time_control = payload.get("time_control", {})
        minutes = int(time_control.get("minutes", 0))
        increment = int(time_control.get("increment", 0))

        game = ChessGame(minutes, increment)
        game_id = self._new_id("game")
        invite_code = self._generate_invite_code()
        host_player_id = self._new_id("player")

        host_player = self._new_player_state(host_player_id, host_side)
        session = _GameSession(
            game_id=game_id,
            invite_code=invite_code,
            host_player_id=host_player_id,
            game=game,
            players={host_player_id: host_player},
        )
        self._sessions_by_game_id[game_id] = session
        self._game_id_by_invite_code[invite_code] = game_id

        event = self._make_server_event(
            session,
            host_player_id,
            "host_created",
            {
                "invite_code": invite_code,
                "game_id": game_id,
                "host_side": host_side.value,
                "player_id": host_player_id,
                "resume_token": host_player.resume_token,
                "resume_token_expires_at_utc": self._iso(host_player.resume_token_expires_at),
                "time_control": {"minutes": minutes, "increment": increment},
            },
        )
        return {"ok": True, "events": [event]}

    def _handle_join_request(self, message: dict[str, Any]) -> dict[str, Any]:
        payload = message["payload"]
        invite_code = payload.get("invite_code")
        if not isinstance(invite_code, str) or invite_code not in self._game_id_by_invite_code:
            return {"ok": False, "error": "invalid invite code", "events": []}

        session = self._sessions_by_game_id[self._game_id_by_invite_code[invite_code]]
        if len(session.players) >= 2:
            return {"ok": False, "error": "session is full", "events": []}

        host_player = session.players[session.host_player_id]
        guest_side = host_player.side.opposite()
        guest_player_id = self._new_id("player")
        guest_player = self._new_player_state(guest_player_id, guest_side)
        session.players[guest_player_id] = guest_player

        white_player_id = self._find_player_by_side(session, Color.WHITE)
        black_player_id = self._find_player_by_side(session, Color.BLACK)

        guest_joined = self._make_server_event(
            session,
            guest_player_id,
            "join_accepted",
            {
                "game_id": session.game_id,
                "player_id": guest_player_id,
                "side": guest_side.value,
                "resume_token": guest_player.resume_token,
                "resume_token_expires_at_utc": self._iso(guest_player.resume_token_expires_at),
            },
        )

        game_start_payload = {
            "game_id": session.game_id,
            "white_player_id": white_player_id,
            "black_player_id": black_player_id,
            "initial_fen": "startpos",
            "halfmove": len(session.game.game_state.move_history),
            "position_hash": fingerprint_game_state(session.game),
            "state": self._state_snapshot(session.game),
            "time_control": {
                "minutes": int(session.game.timer.base_time // 60),
                "increment": session.game.timer.increment,
            },
            "server_clock": self._clock_snapshot(session.game),
        }

        start_events = [
            self._make_server_event(session, pid, "game_start", game_start_payload)
            for pid in session.players
        ]

        return {"ok": True, "events": [guest_joined, *start_events]}

    def _handle_move_intent(self, message: dict[str, Any]) -> dict[str, Any]:
        session, player_state, error = self._resolve_session_and_player(message)
        if error:
            return {"ok": False, "error": error, "events": []}

        seq_error = self._validate_sequence(message, player_state)
        if seq_error:
            return {"ok": False, "error": seq_error, "events": []}

        expected_halfmove = message["payload"].get("expected_halfmove")
        expected_hash = message["payload"].get("expected_position_hash")

        authoritative_halfmove = len(session.game.game_state.move_history)
        authoritative_hash = fingerprint_game_state(session.game)
        if expected_halfmove != authoritative_halfmove or expected_hash != authoritative_hash:
            event = self._make_server_event(
                session,
                player_state.player_id,
                "move_rejected",
                {
                    "reason": "state_desync",
                    "authoritative_halfmove": authoritative_halfmove,
                    "authoritative_position_hash": authoritative_hash,
                    "authoritative_fen": "not-implemented",
                    "authoritative_state": self._state_snapshot(session.game),
                },
            )
            return {"ok": True, "events": [event]}

        game_turn = session.game.game_state.current_turn
        if player_state.side != game_turn:
            event = self._make_server_event(
                session,
                player_state.player_id,
                "move_rejected",
                {
                    "reason": "not_your_turn",
                    "authoritative_halfmove": authoritative_halfmove,
                    "authoritative_position_hash": authoritative_hash,
                    "authoritative_fen": "not-implemented",
                    "authoritative_state": self._state_snapshot(session.game),
                },
            )
            return {"ok": True, "events": [event]}

        move_payload = message["payload"].get("move", {})
        move = self._resolve_legal_move(session.game, move_payload)
        if move is None:
            event = self._make_server_event(
                session,
                player_state.player_id,
                "move_rejected",
                {
                    "reason": "illegal_move",
                    "authoritative_halfmove": authoritative_halfmove,
                    "authoritative_position_hash": authoritative_hash,
                    "authoritative_fen": "not-implemented",
                    "authoritative_state": self._state_snapshot(session.game),
                },
            )
            return {"ok": True, "events": [event]}

        moving_piece = session.game.board.get_piece(move.from_pos)
        moving_piece_type = moving_piece.piece_type if moving_piece else PieceType.PAWN
        session.game.game_state.make_move(move)
        session.game.last_move = (move.from_pos, move.to_pos)

        accepted_payload = {
            "applied_halfmove": len(session.game.game_state.move_history),
            "move": {
                "from": move.from_pos.to_algebraic(),
                "to": move.to_pos.to_algebraic(),
                "promotion": move.promotion_piece.value if move.promotion_piece else None,
                "san": session.game.game_state.get_move_notation(move, moving_piece_type),
            },
            "position_fen": "not-implemented",
            "position_hash": fingerprint_game_state(session.game),
            "clock": self._clock_snapshot(session.game),
        }

        events = [
            self._make_server_event(session, pid, "move_accepted", accepted_payload)
            for pid in session.players
        ]
        return {"ok": True, "events": events}

    def _handle_state_resync_request(self, message: dict[str, Any]) -> dict[str, Any]:
        session, player_state, error = self._resolve_session_and_player(message)
        if error:
            return {"ok": False, "error": error, "events": []}

        state_payload = {
            "halfmove": len(session.game.game_state.move_history),
            "position_fen": "not-implemented",
            "position_hash": fingerprint_game_state(session.game),
            "clock": self._clock_snapshot(session.game),
            "state": self._state_snapshot(session.game),
            "last_event_id": "",
        }
        event = self._make_server_event(session, player_state.player_id, "state_resync", state_payload)
        return {"ok": True, "events": [event]}

    def _handle_reconnect_request(self, message: dict[str, Any]) -> dict[str, Any]:
        game_id = message.get("game_id")
        player_id = message.get("player_id")
        payload = message.get("payload", {})
        resume_token = payload.get("resume_token")

        session = self._sessions_by_game_id.get(str(game_id))
        if not session:
            return {"ok": False, "error": "unknown game", "events": []}

        player_state = session.players.get(str(player_id))
        if not player_state:
            return {"ok": False, "error": "unknown player", "events": []}

        now = datetime.now(timezone.utc)
        if resume_token != player_state.resume_token or now >= player_state.resume_token_expires_at:
            rejected = self._make_server_event(
                session,
                player_state.player_id,
                "reconnect_rejected",
                {"reason": "invalid_or_expired_token", "recoverable": False},
            )
            return {"ok": True, "events": [rejected]}

        player_state.resume_token = self._new_resume_token()
        player_state.resume_token_expires_at = now + self._reconnect_ttl

        accepted = self._make_server_event(
            session,
            player_state.player_id,
            "reconnect_accepted",
            {
                "game_id": session.game_id,
                "player_id": player_state.player_id,
                "new_resume_token": player_state.resume_token,
                "resume_token_expires_at_utc": self._iso(player_state.resume_token_expires_at),
                "state": {
                    "halfmove": len(session.game.game_state.move_history),
                    "position_fen": "not-implemented",
                    "position_hash": fingerprint_game_state(session.game),
                    "clock": self._clock_snapshot(session.game),
                    "state": self._state_snapshot(session.game),
                },
            },
        )
        return {"ok": True, "events": [accepted]}

    def _resolve_session_and_player(self, message: dict[str, Any]) -> tuple[_GameSession | None, _PlayerState | None, str | None]:
        game_id = str(message.get("game_id"))
        player_id = str(message.get("player_id"))
        session = self._sessions_by_game_id.get(game_id)
        if not session:
            return None, None, "unknown game"

        player_state = session.players.get(player_id)
        if not player_state:
            return None, None, "unknown player"

        return session, player_state, None

    def _validate_sequence(self, message: dict[str, Any], player_state: _PlayerState) -> str | None:
        event_id = str(message.get("event_id"))
        seq = int(message.get("sequence"))

        if event_id in player_state.seen_event_ids:
            return "duplicate event_id"
        if seq <= player_state.last_sequence:
            return "sequence regression"

        player_state.seen_event_ids.add(event_id)
        player_state.last_sequence = seq
        return None

    def _resolve_legal_move(self, game: ChessGame, move_payload: dict[str, Any]) -> Move | None:
        try:
            from_pos = Position.from_algebraic(str(move_payload["from"]))
            to_pos = Position.from_algebraic(str(move_payload["to"]))
        except Exception:
            return None

        promotion_name = move_payload.get("promotion")
        promotion_piece = PieceType(promotion_name) if isinstance(promotion_name, str) else None

        legal_moves = game.game_state.get_legal_moves_for_position(from_pos)
        for move in legal_moves:
            if move.to_pos != to_pos:
                continue
            if move.promotion_piece is None:
                if promotion_piece is None:
                    return move
            elif move.promotion_piece == promotion_piece:
                return move

        return None

    def _make_server_event(self, session: _GameSession, player_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        session.server_sequence += 1
        return {
            "protocol_version": PROTOCOL_VERSION,
            "event_type": event_type,
            "event_id": self._new_id("evt"),
            "sent_at_utc": self._iso(datetime.now(timezone.utc)),
            "game_id": session.game_id,
            "player_id": player_id,
            "sequence": session.server_sequence,
            "payload": payload,
        }

    def _new_player_state(self, player_id: str, side: Color) -> _PlayerState:
        now = datetime.now(timezone.utc)
        return _PlayerState(
            player_id=player_id,
            side=side,
            resume_token=self._new_resume_token(),
            resume_token_expires_at=now + self._reconnect_ttl,
        )

    def _find_player_by_side(self, session: _GameSession, side: Color) -> str:
        for player_id, player in session.players.items():
            if player.side == side:
                return player_id
        raise ValueError(f"missing player for side {side.value}")

    def _clock_snapshot(self, game: ChessGame) -> dict[str, Any]:
        active = game.timer.current_player.value if game.timer.current_player else game.game_state.current_turn.value
        return {
            "white_ms": int(game.timer.white_time * 1000),
            "black_ms": int(game.timer.black_time * 1000),
            "active": active,
        }

    def _state_snapshot(self, game: ChessGame) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "board": game.board.to_string_board(),
            "current_turn": game.game_state.current_turn.value,
            "castling_rights": str(game.board.castling_rights),
            "en_passant_target": game.board.en_passant_target.to_algebraic() if game.board.en_passant_target else None,
            "half_move_clock": game.game_state.half_move_clock,
            "full_move_number": game.game_state.full_move_number,
        }
        if game.last_move:
            snapshot["last_move"] = {
                "from": game.last_move[0].to_algebraic(),
                "to": game.last_move[1].to_algebraic(),
            }
        else:
            snapshot["last_move"] = None
        return snapshot

    def _generate_invite_code(self, length: int = 6) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(length))
            if code not in self._game_id_by_invite_code:
                return code

    def _new_resume_token(self) -> str:
        return f"rt_{secrets.token_urlsafe(24)}"

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _iso(value: datetime) -> str:
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
