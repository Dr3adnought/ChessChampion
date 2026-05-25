# Network Protocol Phase A (Host/Join PvP)

This document defines the first versioned protocol envelope and baseline event set for remote player-vs-player games.

## Goals
- Enable direct host/join games with invite code.
- Keep game state authoritative on server.
- Prevent client-side rule divergence and clock desync.

## Authority Model
- Authority: server-authoritative.
- Clients send intent events only.
- Server validates turn, legality, and clock state before accepting move.

## Transport
- Recommended transport: WebSocket over TLS.
- Connection path: one socket per client session.
- All payloads are JSON objects.

## Envelope (V1)
Every message uses the same top-level envelope.

```json
{
  "protocol_version": "1.0",
  "event_type": "move_intent",
  "event_id": "01JX...",
  "sent_at_utc": "2026-05-25T21:05:00Z",
  "game_id": "game_01JX...",
  "player_id": "player_01JX...",
  "sequence": 14,
  "payload": {}
}
```

## Envelope Fields
- protocol_version: protocol contract version. Required.
- event_type: event discriminator string. Required.
- event_id: unique event identifier (ULID/UUID). Required.
- sent_at_utc: sender timestamp in UTC ISO-8601. Required.
- game_id: unique game session identifier. Required after host/join handshake.
- player_id: logical sender identity. Required.
- sequence: sender-local monotonic integer for ordering. Required.
- payload: event-specific data object. Required.

## Phase A Event Set
- host_create
- host_created
- join_request
- join_accepted
- join_rejected
- game_start
- reconnect_request
- reconnect_accepted
- reconnect_rejected
- move_intent
- move_accepted
- move_rejected
- state_resync_request
- state_resync
- draw_offer
- draw_response
- resign
- game_end
- heartbeat
- error

## Event Payload Contracts

### host_create
Client -> Server

```json
{
  "requested_side": "white",
  "time_control": { "minutes": 10, "increment": 5 }
}
```

### host_created
Server -> Host

```json
{
  "invite_code": "ABCD12",
  "game_id": "game_01JX...",
  "host_side": "white",
  "time_control": { "minutes": 10, "increment": 5 }
}
```

### join_request
Client -> Server

```json
{
  "invite_code": "ABCD12"
}
```

### game_start
Server -> Both

```json
{
  "game_id": "game_01JX...",
  "white_player_id": "player_01JX...",
  "black_player_id": "player_01JX...",
  "resume_token": "rt_01JX...",
  "resume_token_expires_at_utc": "2026-05-25T23:05:00Z",
  "initial_fen": "startpos",
  "time_control": { "minutes": 10, "increment": 5 },
  "state": {
    "board": [["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"], ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"], ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]],
    "current_turn": "white",
    "castling_rights": "KQkq",
    "en_passant_target": null,
    "half_move_clock": 0,
    "full_move_number": 1,
    "last_move": null
  },
  "server_clock": {
    "white_ms": 600000,
    "black_ms": 600000,
    "active": "white"
  }
}
```

### reconnect_request
Client -> Server

```json
{
  "game_id": "game_01JX...",
  "player_id": "player_01JX...",
  "resume_token": "rt_01JX...",
  "last_seen_event_id": "01JX..."
}
```

### reconnect_accepted
Server -> Client

```json
{
  "game_id": "game_01JX...",
  "player_id": "player_01JX...",
  "new_resume_token": "rt_01JX...",
  "resume_token_expires_at_utc": "2026-05-25T23:35:00Z",
  "state": {
    "halfmove": 8,
    "position_fen": "...",
    "position_hash": "sha256:...",
    "clock": {
      "white_ms": 420000,
      "black_ms": 419000,
      "active": "white"
    },
    "state": {
      "board": [["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"], ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"], ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]],
      "current_turn": "white",
      "castling_rights": "KQkq",
      "en_passant_target": null,
      "half_move_clock": 0,
      "full_move_number": 1,
      "last_move": null
    }
  }
}
```

### reconnect_rejected
Server -> Client

```json
{
  "reason": "invalid_or_expired_token",
  "recoverable": false
}
```

### move_intent
Client -> Server

```json
{
  "move": {
    "from": "e2",
    "to": "e4",
    "promotion": null
  },
  "expected_halfmove": 1,
  "expected_position_hash": "sha256:..."
}
```

### move_accepted
Server -> Both

```json
{
  "applied_halfmove": 1,
  "move": {
    "from": "e2",
    "to": "e4",
    "promotion": null,
    "san": "e4"
  },
  "position_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
  "position_hash": "sha256:...",
  "clock": {
    "white_ms": 599300,
    "black_ms": 600000,
    "active": "black"
  }
}
```

### move_rejected
Server -> Sender

```json
{
  "reason": "illegal_move",
  "authoritative_halfmove": 0,
  "authoritative_position_hash": "sha256:...",
  "authoritative_fen": "...",
  "authoritative_state": {
    "board": [["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"], ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"], ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]],
    "current_turn": "white",
    "castling_rights": "KQkq",
    "en_passant_target": null,
    "half_move_clock": 0,
    "full_move_number": 1,
    "last_move": null
  }
}
```

### state_resync
Server -> Client

```json
{
  "halfmove": 8,
  "position_fen": "...",
  "position_hash": "sha256:...",
  "clock": {
    "white_ms": 420000,
    "black_ms": 419000,
    "active": "white"
  },
  "state": {
    "board": [["br", "bn", "bb", "bq", "bk", "bb", "bn", "br"], ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], [null, null, null, null, null, null, null, null], ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"], ["wr", "wn", "wb", "wq", "wk", "wb", "wn", "wr"]],
    "current_turn": "white",
    "castling_rights": "KQkq",
    "en_passant_target": null,
    "half_move_clock": 0,
    "full_move_number": 1,
    "last_move": null
  },
  "last_event_id": "01JX..."
}
```

### game_end
Server -> Both

```json
{
  "result": "1-0",
  "reason": "checkmate",
  "final_fen": "..."
}
```

### heartbeat
Server -> Both

```json
{
  "server_time_utc": "2026-05-25T21:10:00Z",
  "clock": {
    "white_ms": 418500,
    "black_ms": 419000,
    "active": "white"
  },
  "halfmove": 8,
  "position_hash": "sha256:..."
}
```

## Validation Rules
- Reject envelope if required fields are missing.
- Reject unsupported protocol_version.
- Reject duplicate event_id from same player.
- Reject sequence regression from same player.
- Reject move_intent when not sender turn.
- Reject move_intent whose move is illegal in authoritative position.

## Desync Guardrails
- Every `move_intent` must include `expected_halfmove` and `expected_position_hash`.
- Server compares expected values with authoritative state before move validation.
- On mismatch, server returns `move_rejected` with authoritative halfmove/hash/FEN.
- Clients must immediately trigger `state_resync_request` after desync rejection.
- Server emits `state_resync` containing full authoritative state snapshot.
- Clients treat `state_resync` as source of truth and overwrite local board/clock/move counters.
- Heartbeat messages include `halfmove` and `position_hash` to detect silent drift.
- If drift is detected without a move, client requests resync and blocks local move submission until resynced.

## Reconnect Baseline
- Client reconnects with `reconnect_request` including `game_id`, `player_id`, and `resume_token`.
- Server validates token ownership, expiry, and game membership.
- If valid, server rotates token and returns `reconnect_accepted` with full authoritative state.
- If invalid or expired, server returns `reconnect_rejected`; client must return to menu.
- Client replaces local state with authoritative state and resumes from server sequence.

## Resume Token Policy
- Token type: opaque random string (minimum 128-bit entropy).
- Issuance: per player at game start; rotate on successful reconnect.
- Scope: valid only for one `game_id` + `player_id` pair.
- Expiry: short TTL (recommended 30 minutes) after disconnect.
- Storage: client keeps in memory only for Phase A (no persistent account storage yet).
- Revocation: server invalidates previous token immediately after rotation.

## Clock Policy
- Clock state is authoritative on server.
- Clients display server-provided clock snapshots.
- Clients never decide timeout outcome.

## Authoritative Clock Sync (Timed Games)
- Server stores authoritative `white_ms`, `black_ms`, and `active` player.
- Server updates clock on each accepted move and on periodic heartbeat (recommended every 1s).
- Client renders a smoothed countdown between heartbeats but clamps to latest server values.
- If client-clock drift exceeds 250ms from server snapshot, client snaps to server value.
- Timeout decisions are server-only; server emits `game_end` with `reason: timeout` when flag falls.
- During reconnect, `reconnect_accepted.state.clock` replaces any local clock state.

## Versioning Strategy
- Minor changes that are backward compatible: 1.0 -> 1.1
- Breaking changes: 1.x -> 2.0
- Client must advertise supported versions during handshake in future phase.

## Phase A Non-Goals
- Matchmaking queue
- Friends/social graph
- Spectator mode
- Tournament brackets
- Persistent account auth
