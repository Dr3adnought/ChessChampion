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
  "initial_fen": "startpos",
  "time_control": { "minutes": 10, "increment": 5 },
  "server_clock": {
    "white_ms": 600000,
    "black_ms": 600000,
    "active": "white"
  }
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
  "authoritative_position_hash": "sha256:..."
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

## Validation Rules
- Reject envelope if required fields are missing.
- Reject unsupported protocol_version.
- Reject duplicate event_id from same player.
- Reject sequence regression from same player.
- Reject move_intent when not sender turn.
- Reject move_intent whose move is illegal in authoritative position.

## Reconnect Baseline
- Client reconnects with player_id and game_id.
- Server sends state_resync with authoritative board, halfmove, and clock.
- Client replaces local state with server state on mismatch.

## Clock Policy
- Clock state is authoritative on server.
- Clients display server-provided clock snapshots.
- Clients never decide timeout outcome.

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
