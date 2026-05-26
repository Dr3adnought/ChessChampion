# ChessChampion - Development Roadmap

## 🎯 Project Vision
Create a feature-rich, polished chess game that serves as both an engaging game for players of all skill levels and a learning tool for chess improvement. The final product should be intuitive, beautiful, and packed with quality-of-life features.

---

## ✅ Completed Features

### Phase 1: Core Foundation
- [x] Clean, modular architecture with separation of concerns
- [x] Full chess rules implementation (moves, castling, en passant, promotion)
- [x] Check, checkmate, and stalemate detection
- [x] 50-move rule implementation
- [x] Move validation system

### Phase 2: AI & Gameplay
- [x] AI opponent with minimax algorithm + alpha-beta pruning
- [x] Multiple difficulty levels (Easy, Medium, Hard, Expert)
- [x] Piece-square table evaluation
- [x] AI depth configuration (1-4 levels)

### Phase 3: User Experience Enhancements
- [x] Smooth piece animations with cubic ease-out (400ms)
- [x] Timing delays between player and AI moves (800ms)
- [x] Visual move indicators (legal moves highlighted)
- [x] Last move highlighting
- [x] Check highlighting on king
- [x] Board coordinates (a-h, 1-8)

### Phase 4: UI Improvements
- [x] Main menu with difficulty selection
- [x] Color selection (play as White or Black)
- [x] Game over menu with restart/quit options
- [x] Captured pieces sidebar with material advantage indicator
- [x] Player vs Player mode (local multiplayer)
- [x] Dynamic menu that adapts to game mode

### Phase 5: Advanced Controls
- [x] Move undo/redo system with UI buttons and keyboard shortcuts (Ctrl+Z/Y)
- [x] Pawn promotion dialog with interactive piece selection (mouse + keyboard)
- [x] Chess clock with selectable time controls and increment support

---

## 🚀 Planned Features (Prioritized)

### **Tier 1: Quick Wins** (Simple + High Impact)
Priority: Implement these ASAP for maximum user value

#### 1. Move Undo/Redo System ⭐⭐⭐
**Complexity:** Low 
**Impact:** High  
**Status:** ✅ **COMPLETED**

**Features:**
- ✅ Undo button in UI (or keyboard shortcut: Ctrl+Z)
- ✅ Redo button (Ctrl+Y)
- ✅ Navigate through move history
- ✅ Works for both PvP and PvAI modes
- ✅ Visual indication of current position in history

**Implementation Notes:**
- Implemented full undo/redo system with UI buttons
- Handles all special moves (castling, en passant, promotion, captures)
- Disabled during AI thinking/animation
- Redo stack clears when new move is made

**Dependencies:** None

---

#### 2. Pawn Promotion Dialog ⭐⭐⭐
**Complexity:** Low  
**Impact:** High  
**Status:** ✅ **COMPLETED**

**Features:**
- ✅ Modal dialog when pawn reaches last rank
- ✅ Visual selection of Queen, Rook, Bishop, or Knight
- ✅ Keyboard shortcuts (Q/R/B/N/ESC)
- ✅ Works with animations

**Implementation Notes:**
- Created PromotionDialog class with visual piece selection
- Game pauses when dialog appears
- Shows piece images for selection with hover effects
- Handles both PvP and PvAI modes

**Dependencies:** None

---

#### 3. Sound Effects ⭐⭐
**Complexity:** Low 
**Impact:** Medium-High  
**Status:** Ready to implement

**Features:**
- Move sound (different for normal vs capture)
- Capture sound
- Check sound
- Checkmate sound
- Castle sound
- Promotion sound
- Button click sounds in menu
- Volume control slider
- Mute toggle

**Implementation Notes:**
- Need to add sound files to `assets/sounds/`
- Use pygame mixer
- Store volume preference
- Option to disable in settings

**Dependencies:** None

---

### **Tier 2: Core Features** (Medium Complexity, Essential)
Priority: Implement after Tier 1 for complete chess experience

#### 4. Save/Load Game System ⭐⭐⭐
**Complexity:** Medium 
**Impact:** High  
**Status:** ✅ **COMPLETED**

**Features:**
- Save game to PGN (Portable Game Notation) format
- Load saved games
- Auto-save on quit option
- Save game list/history
- Resume interrupted games
- Export games for analysis

**PGN Format Example:**
```
[Event "ChessChampion Game"]
[Site "Local"]
[Date "2026.02.09"]
[White "Player"]
[Black "AI (Medium)"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6...
```

**Implementation Notes:**
- Implemented `game/save_load/` package (`schema.py`, `serializer.py`, `store.py`, `service.py`, `pgn.py`)
- Stores: moves, players/session metadata, clock state, timestamps, captured pieces, castling/en passant state
- Saves to `saved_games/` with index cache (`saved_games/index.json`)
- Exposes in-game Save/Load via sidebar buttons and keyboard shortcuts (`Ctrl+S`, `Ctrl+L`)
- Writes PGN sidecar files for each JSON save
- Includes rolling autosave slot (`autosave.json`) on quit/new-game/end-game transitions

**Dependencies:** None

---

#### 5. Move Timer (Per-Move Countdown) ⭐⭐
**Complexity:** Medium  
**Impact:** Medium  
**Status:** Planned

**Features:**
- Optional timer for each move
- Configurable time limits (5s, 10s, 15s, 30s, 60s)
- Visual countdown display
- Warning when time is low (< 5 seconds)
- Loss on timeout
- Disable for casual games

**Implementation Notes:**
- Add timer UI element
- Track time per move
- Pause during animations
- Add timer settings to menu

**Dependencies:** None

---

#### 6. Game Timer (Chess Clock) ⭐⭐
**Complexity:** Medium 
**Impact:** Medium  
**Status:** ✅ **COMPLETED**

**Features:**
- Total game time for each player
- Multiple time control options:
  - Blitz (3+0, 5+0)
  - Rapid (10+0, 15+10)
  - Classic (30+0, 60+30)
  - Custom time controls
- Time increment per move
- Display both clocks simultaneously
- Visual indication of active clock
- Flag fall (time runs out) detection

**Implementation Notes:**
- Implemented in `game/timer.py` with per-player clocks and increment support
- Integrated into menu flow with preset time controls (including untimed)
- Clock display is rendered in the sidebar with active-player highlighting
- Timer pauses during animations and enforces timeout loss

**Dependencies:** None

---

#### 7. Game Review Mode ⭐⭐
**Complexity:** Medium 
**Impact:** High  
**Status:** Planned

**Features:**
- Navigate through completed games
- Step forward/backward through moves
- Jump to specific move
- Show move notation
- Display position evaluation (if AI played)
- Highlight best moves vs played moves
- Add comments to moves

**UI Elements:**
- Move list panel
- Navigation buttons (|<, <, >, >|)
- Move number scrubber
- Analysis panel

**Implementation Notes:**
- Build on saved game system
- Read-only board mode
- Show alternative lines
- Integrate with undo system

**Dependencies:** Save/Load Game System

---

### **Tier 3: Advanced Features** (Higher Complexity)
Priority: Polish and advanced functionality

#### 8. Learning/Tutorial Mode ⭐⭐⭐
**Complexity:** High 
**Impact:** High for beginners  
**Status:** Planned

**Features:**
- Interactive tutorials for:
  - How pieces move
  - Basic tactics (pins, forks, skewers)
  - Opening principles
  - Endgame basics
  - Special moves (castling, en passant)
- Practice puzzles
- Hints system
- Move suggestions with explanations
- Progressive difficulty

**Structure:**
```
tutorials/
├── basics/
│   ├── pawn_movement.json
│   ├── knight_movement.json
│   └── ...
├── tactics/
│   ├── pins.json
│   ├── forks.json
│   └── ...
└── endgames/
    ├── king_queen_vs_king.json
    └── ...
```

**Implementation Notes:**
- Create tutorial system with JSON scenarios
- Add interactive overlay with instructions
- Track tutorial progress
- Award system for completion

**Dependencies:** None (standalone feature)

---

#### 9. User Profiles & Statistics ⭐⭐
**Complexity:** High 
**Impact:** Medium  
**Status:** Planned

**Features:**
- User account system (local)
- Player statistics:
  - Games played
  - Win/Loss/Draw ratio
  - Average game length
  - Favorite openings
  - Performance by color
  - Time spent playing
- Achievement system
- Game history
- Progress tracking

**Profile Storage:**
```json
{
  "username": "Player1",
  "created": "2026-02-09",
  "stats": {
    "games_played": 150,
    "wins": 82,
    "losses": 55,
    "draws": 13,
    "current_streak": 3,
    "best_streak": 8
  },
  "achievements": [...],
  "elo_rating": 1450
}
```

**Implementation Notes:**
- Store profiles in `profiles/` directory as JSON
- Profile selector on startup
- Statistics dashboard
- Link to game history

**Dependencies:** Save/Load Game System

---

#### 10. Elo Rating System ⭐⭐
**Complexity:** Medium-High 
**Impact:** Medium  
**Status:** Planned

**Features:**
- Calculate Elo rating for player
- Assign ratings to AI difficulty levels:
  - Easy: 800
  - Medium: 1200
  - Hard: 1600
  - Expert: 2000
- Track rating over time
- Rating graph/history
- Rating brackets (Beginner, Intermediate, Advanced, Expert)
- Rating milestones with achievements

**Implementation Notes:**
- Use standard Elo formula
- K-factor of 32 for rating changes
- Track rating separately for PvP and PvAI
- Rating updates after each game

**Dependencies:** User Profiles

---

### **Tier 4: Polish & Extra Features**
Priority: Nice-to-have enhancements

#### 11. Board Themes & Customization ⭐
**Complexity:** Low-Medium   
**Impact:** Low-Medium  
**Status:** Planned

**Features:**
- Multiple board color schemes:
  - Classic (current)
  - Wooden
  - Blue/White
  - Pink/Rose
  - Dark mode
  - High contrast
- Multiple piece sets
- Board size adjustment
- Coordinate display toggle
- Move highlight style options

**Implementation Notes:**
- Create theme configuration files
- Settings menu for customization
- Save preferences

**Dependencies:** None

---

#### 12. Position Setup Mode ⭐
**Complexity:** Medium 
**Impact:** Low-Medium  
**Status:** Planned

**Features:**
- Set up custom positions
- Place/remove pieces freely
- Set turn, castling rights, en passant
- Load positions from FEN notation
- Validate legal positions
- Save custom positions
- Useful for:
  - Puzzle creation
  - Endgame practice
  - Position analysis

**Implementation Notes:**
- Create position editor UI
- FEN import/export
- Validation system
- Integration with game mode

**Dependencies:** None

---

#### 13. Online Multiplayer 🌐
**Complexity:** Very High 
**Impact:** High  
**Status:** Planned (phased delivery)

**Features (target state):**
- Play against remote opponents
- Matchmaking system
- Friend system
- Chat functionality
- Spectator mode
- Tournament system

**Phased Scope (recommended):**
- Phase A: Direct PvP by invite code (host/join), no accounts
- Phase B: Persistent accounts, friend list, reconnect flow
- Phase C: Matchmaking, ratings sync, tournaments, spectator mode

**Technical Considerations:**
- Requires server infrastructure
- WebSocket or socket.io for real-time play
- User authentication
- Database for user accounts
- Latency handling

**Implementation Notes:**
- Major undertaking; deliver as incremental slices
- Start with deterministic move relay protocol and server-authoritative turn validation
- Add reconnect and latency-tolerant clock synchronization before matchmaking
- Consider using chess.com/lichess APIs instead
- Or implement as separate "Online Edition"

**Dependencies:** User Profiles, Elo Rating, Game Timer

---

#### 14. Desktop Packaging & Distribution 📦
**Complexity:** Medium
**Impact:** High
**Status:** Planned

**Features:**
- One-click distributable builds for Windows (`.exe` installer)
- Portable build option (zip, no installer)
- Branded app icon, version metadata, and release notes
- Include required assets (`assets/`, sounds, piece sprites) in packaged app
- Optional auto-update check endpoint (future)

**Implementation Notes:**
- Primary path: PyInstaller for local executable generation
- Installer path: Inno Setup or NSIS for signed installer output
- Add CI release workflow to produce versioned artifacts on tags
- Add smoke test checklist for packaged build startup, save/load, and clock behavior

**Dependencies:** Stable settings/config layout

---

#### 15. AI Improvements ⭐⭐
**Complexity:** High (ongoing)  
**Impact:** Medium  
**Status:** Continuous improvement

**Enhancements:**
- Opening book integration
- Endgame tablebase support
- Better evaluation function
- Iterative deepening
- Move ordering improvements
- Quiescence search
- Transposition tables
- Multi-threading support

**Implementation Notes:**
- Incremental improvements over time
- Performance benchmarking
- Option for "experimental AI" mode

**Dependencies:** None

---

#### 16. Analysis Engine Integration 🔧
**Complexity:** High 
**Impact:** Medium-High  
**Status:** Future consideration

**Features:**
- Integrate Stockfish or similar engine
- Show best move analysis
- Position evaluation bar
- Multi-line analysis
- Blunder detection
- Mistake highlighting in review mode

**Implementation Notes:**
- Use python-chess library
- Run Stockfish as subprocess
- Parse UCI protocol
- Display in review mode

**Dependencies:** Game Review Mode

---

## 🎨 UI/UX Improvements

### Current UI Elements:
- Main menu
- Time control selection menu
- Game board (800x800)
- Captured pieces sidebar (200px)
- Live chess clocks in sidebar (timed games)
- Undo/Redo buttons in sidebar + keyboard shortcuts
- Save/Load buttons in sidebar + keyboard shortcuts
- Load-list overlay with selectable save entries
- Game over overlay

### Planned UI Additions:
- **Settings Menu:**
  - Sound volume
  - Theme selection
  - Board flip option
  - Animation speed
  - Show coordinates toggle
  - Auto-save toggle

- **In-Game HUD:**
  - Current turn indicator (improved)
  - Timer displays
  - Move counter
  - Undo/Redo buttons
  - Save game button
  - Settings button
  - Resign/Draw offer buttons

- **Status Bar:**
  - Game mode indicator
  - Player names
  - Elo ratings (if applicable)
  - Connection status (for online)

---

## 📊 Technical Improvements

### Performance Optimizations:
- [ ] Optimize board copying for AI (currently okay)
- [ ] Cache legal move calculations
- [ ] Implement move ordering for faster AI
- [ ] Profile and optimize rendering
- [ ] Reduce memory allocations in hot paths

### Code Quality:
- [x] Add unit test baseline (save/load regression + schema/store/timer unit tests)
- [ ] Expand comprehensive unit tests across core chess engine modules
- [ ] Add integration tests
- [ ] Create test coverage report
- [ ] Add type checking with mypy
- [ ] Improve documentation
- [ ] Add docstring examples

### Architecture:
- [ ] Separate rendering thread for smoother animations
- [ ] Event system for better decoupling
- [ ] Plugin system for features
- [ ] Configuration file system (YAML/TOML)

---

## 📝 Documentation Needs

- [ ] User manual / Help system
- [ ] API documentation for modules
- [ ] Contributing guidelines
- [ ] Installation guide for different platforms
- [ ] Tutorial creation guide
- [ ] Development setup guide

---

## ✅ Preflight Checklist (Packaging + Online PvP + Testing)

Complete these before committing to full distribution and multiplayer implementation.

### Foundations
- [x] Add runtime path utility for source + packaged execution (assets/settings/saves)
- [x] Move writable files (saves/settings/logs) to user data folder strategy
- [x] Introduce app version constant + expose in UI/build metadata
- [x] Define protocol versioning and message envelope contract for network play

### Packaging Readiness
- [x] Add first PyInstaller build configuration/spec
- [x] Verify packaged asset inclusion (pieces, sounds, UI assets)
- [x] Add release smoke checklist (startup, move flow, save/load, timer, promotion, undo/redo)
- [x] Add tag-driven CI artifact build plan for reproducible releases

### Online PvP Readiness
- [x] Choose and lock authority model (recommended: server-authoritative)
- [x] Define Phase A network events (host, join, move_intent, move_accepted, resync, resign, draw)
- [x] Add reconnect token + session resume strategy
- [x] Add desync guardrails (move number + board hash/FEN checkpoint)
- [x] Define authoritative clock sync behavior for timed games
- [x] Implement Phase A in-process authoritative session manager (host/join/move/resync/reconnect)
- [x] Add transport-backed session hub/client adapter shim (message routing over protocol envelopes)
- [x] Wire minimal Online Host/Join menu + main-loop handshake flow (Phase A bootstrap)
- [x] Integrate authoritative move flow in online mode (`move_intent` send + `move_accepted` apply)
- [x] Apply authoritative full-state snapshots on desync/resync events in online mode
- [x] Normalize reconnect payload shape and apply reconnect snapshots client-side
- [x] Add runtime transport selection/bootstrap routing (shim vs TCP)
- [x] Add first real TCP adapter path (JSON-over-TCP envelope transport)
- [x] Add minimal TCP session server process reusing authoritative SessionManager
- [x] Persist online reconnect/session metadata (including transport label) through save/load
- [x] Add online HUD indicator for connection state and active transport backend

### Testing Baseline
- [x] Save/Load regression tests in `tests/test_save_load_regression.py`
- [x] Schema validation unit tests in `tests/test_schema_validation_unit.py`
- [x] Store-layer unit tests in `tests/test_store_layer_unit.py`
- [x] Timer unit tests in `tests/test_timer_unit.py`
- [x] Path/runtime layout unit tests in `tests/test_paths_unit.py`
- [x] Settings/config persistence unit tests in `tests/test_settings_unit.py`
- [x] Network protocol contract unit tests in `tests/test_network_protocol_contract_unit.py`
- [x] State fingerprint determinism unit tests in `tests/test_state_fingerprint_unit.py`
- [x] Network session manager unit tests in `tests/test_network_session_manager_unit.py`
- [x] Network transport shim unit tests in `tests/test_network_transport_shim_unit.py`
- [x] Network bootstrap selection unit tests in `tests/test_network_bootstrap_unit.py`
- [x] TCP transport adapter unit tests in `tests/test_network_tcp_adapter_unit.py`
- [x] TCP session server integration tests (host/join/move/reconnect over sockets) in `tests/test_network_tcp_session_server_integration.py`
- [x] Online sync helper unit tests in `tests/test_online_sync_unit.py`
- [x] Move-validation unit tests (castling/en passant/check constraints) in `tests/test_move_validation_unit.py`
- [x] Deterministic serialization/deserialization parity tests for random legal games in `tests/test_serialization_parity_unit.py`

---

## 🎯 Milestone Goals

### Version 1.0 (MVP - Current)
- ✅ Core chess gameplay
- ✅ AI opponent
- ✅ Basic UI
- ✅ Animations
- ✅ PvP mode
- ✅ Undo/Redo controls
- ✅ Pawn promotion dialog
- ✅ Time controls and chess clock

### Version 1.5 (Near-term)
Target: 1-2 weeks
- [x] Undo/Redo
- [x] Pawn promotion dialog
- [ ] Sound effects
- [x] Save/Load games
- [ ] Basic settings menu

### Version 2.0 (Complete Experience)
Target: 1-2 months
- [ ] Move timers
- [ ] Game review mode
- [ ] Tutorial system
- [ ] User profiles
- [ ] Elo ratings
- [ ] Themes & customization

### Version 2.5 (Distribution + Online Foundations)
Target: 2-3 months
- [x] Windows distributable build pipeline (PyInstaller)
- [ ] Installer packaging and release checklist
- [x] Network PvP Phase A spike (host/join + move relay)
- [x] Network game synchronization + reconnect baseline

### Version 3.0 (Advanced)
Target: 3-6 months
- [ ] Analysis engine integration
- [ ] Position setup mode
- [ ] Advanced AI improvements
- [ ] Comprehensive statistics
- [ ] Achievement system

### Version 4.0 (Online)
Target: 6+ months (if pursued)
- [ ] Online multiplayer
- [ ] Matchmaking
- [ ] Tournaments
- [ ] Leaderboards

---

## 🔄 Development Workflow

### For Each Feature:
1. **Design Phase**
   - Sketch UI mockups
   - Define data structures
   - Identify dependencies

2. **Implementation Phase**
   - Create feature branch
   - Write tests first (TDD when applicable)
   - Implement feature
   - Manual testing

3. **Polish Phase**
   - Code review
   - Refactoring
   - Documentation
   - Integration testing

4. **Release Phase**
   - Merge to master
   - Update CHANGELOG
   - Tag version
   - Push to GitHub

---

## 📋 Next Session Priorities

### Single-Track Plan: Home-LAN Playable Release First

Use this as the only active lane until complete. Defer new feature work (including Tutorial) until these checkpoints are done.

1. **Checkpoint R1 - Packaging Baseline**
- [x] Build packaged client artifact and verify launch on host machine
- [x] Produce simple server run artifact/launcher instructions for non-developer use

2. **Checkpoint R2 - Connection UX Baseline**
- [x] Remove env-var dependency for normal users (simple host/join config in UI or persisted settings)
- [x] Keep advanced options optional; prioritize one clear happy path

3. **Checkpoint R3 - Two-Machine LAN Acceptance**
- [ ] Run host + guest on two different home machines using packaged artifacts only
- [ ] Complete one full game with authoritative move relay over TCP
- [ ] Verify reconnect at least once mid-game

#### R3 Result Summary (Fill After Test Run)
- Date:
- Build commit:
- Host machine:
- Guest machine:
- Host LAN IP:
- Result: PASS / FAIL
- Notes:
- Follow-up fixes:

4. **Checkpoint R4 - Beta Playable Exit Gate**
- [ ] One-page setup guide enables non-developer success
- [ ] Fix only blockers found in R3
- [ ] Tag milestone as **Beta Playable (Home LAN)**

### After Beta Playable (Resume Feature Work)

1. Tutorial System
2. Sound Effects
3. Basic settings menu polish
4. Game Review Mode
5. Move Timer (per-move countdown)
6. Profile/statistics groundwork

---

## 🧩 Save/Load V1 - Implementation Tickets

Goal: Ship reliable game resume first (JSON), plus PGN export for interoperability.

### Ticket SL-01: Persistence Module Skeleton
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Create `game/save_load/` package
- Add modules: `schema.py`, `serializer.py`, `store.py`, `pgn.py`, `service.py`
- Add `saved_games/` directory bootstrap logic

**Acceptance Criteria:**
- [x] New package and modules import without errors
- [x] `saved_games/` auto-creates if missing
- [x] No gameplay behavior changes yet

### Ticket SL-02: JSON Schema + Validation
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Define `schema_version` and required fields for session, position, captures, history, and clock
- Implement lightweight payload validation in `schema.py`

**Acceptance Criteria:**
- [x] Invalid/missing required fields return clear validation errors
- [x] Schema version is stored in every save file
- [x] Validation passes for newly generated saves

### Ticket SL-03: Serialize Runtime -> JSON
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Implement serializer for:
  - board via string notation matrix
  - turn/status/clocks/castling/en passant
  - captures, move history, redo stack, last move
  - mode + AI metadata (color/difficulty/depth)

**Acceptance Criteria:**
- [x] Mid-game state serializes without exceptions
- [x] Castling rights and en passant target are preserved
- [x] Timed and untimed sessions serialize correctly

### Ticket SL-04: Deserialize JSON -> Runtime
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Reconstruct `Board`, `GameState`, and timer state from JSON
- Rebuild move and redo structures needed for undo/redo continuity
- Restore last move highlight and session metadata

**Acceptance Criteria:**
- [x] Loaded game position exactly matches saved position
- [x] Undo/redo works after load
- [x] Timers resume with correct remaining time/player

### Ticket SL-05: Store Layer + Save Index
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Implement save/write/read/list/delete in `store.py`
- Add `saved_games/index.json` summary cache for quick menu listing
- Support `manual` and `autosave` source tags

**Acceptance Criteria:**
- [x] Save files persist and can be listed without full file scans
- [x] Delete removes file and updates index
- [x] Corrupt save entries are skipped with non-fatal warning

### Ticket SL-06: Service Facade Integration
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Add `service.py` facade methods: `save_game`, `load_game`, `list_saves`, `delete_save`
- Wire into game flow with minimal surface changes

**Acceptance Criteria:**
- [x] Single-call save/load API works from main loop integration points
- [x] Failures return actionable error messages (not hard crashes)
- [x] Existing gameplay loop remains stable

### Ticket SL-07: PGN Export (V1)
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Generate PGN text for completed/in-progress games
- Include required tags: Event, Site, Date, White, Black, Result
- Write sidecar `.pgn` alongside JSON save

**Acceptance Criteria:**
- [x] PGN file is generated for saved games
- [x] Moves are exported in legal notation sequence
- [x] Unknown result uses `*` for in-progress games

### Ticket SL-08: Manual Save/Load UI Hooks
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Add basic in-menu actions: Save Game / Load Game
- Provide load list from save index and simple success/error feedback

**Acceptance Criteria:**
- [x] Player can save current game from UI flow
- [x] Player can load selected save and continue playing
- [x] Errors are shown cleanly without freezing UI

### Ticket SL-09: Autosave (Quit/New Game Transition)
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Add autosave trigger on quit/end-game transition/new-game transition
- Keep one rolling autosave slot

**Acceptance Criteria:**
- [x] Autosave file updates on configured transition points
- [x] Manual saves are never overwritten by autosave
- [x] Autosave can be loaded like any other entry

### Ticket SL-10: Regression Test Pack (Manual + Optional Unit Tests)
**Status:** ✅ Completed (May 25, 2026)

**Scope:**
- Execute core save/load validation scenarios
- Add optional unit tests for serializer/schema/store where feasible

**Acceptance Criteria:**
- [x] En passant availability preserved across save/load
- [x] Castling rights preserved across save/load
- [x] Promotion history and undo/redo survive load
- [x] Timed game state and timeout behavior survive load

Recommended order: `SL-01` -> `SL-02` -> `SL-03` -> `SL-04` -> `SL-05` -> `SL-06` -> `SL-07` -> `SL-08` -> `SL-09` -> `SL-10`

---

## 🕹 Save/Load Quick Usage

- Save during a game: click **Save** in the sidebar, or press `Ctrl+S`
- Load during a game: click **Load** in the sidebar, or press `Ctrl+L`
- Select a save from the load overlay list
- Autosave is written automatically to `saved_games/autosave.json` when you quit, choose New Game from game-over, or end the game
- Manual saves and autosave are kept separate (manual saves are not overwritten by autosave)

---

## 💡 Ideas for Future Consideration

- Chess variants (Chess960, 3-check, King of the Hill)
- Puzzle rush mode
- Daily puzzle
- Blindfold chess mode
- Coordinate training
- Move prediction training
- Integration with chess.com/lichess APIs
- Mobile app version (using Kivy or similar)
- Web version (using Pygame Web/WASM)
- Twitch integration for streaming
- Discord bot integration

---

## 🎓 Learning Resources

For implementing advanced features:
- **Chess Programming Wiki**: https://www.chessprogramming.org/
- **python-chess library**: https://python-chess.readthedocs.io/
- **Stockfish engine**: https://stockfishchess.org/
- **PGN specification**: https://www.chess.com/terms/chess-pgn
- **FEN notation**: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation
- **Elo rating system**: https://en.wikipedia.org/wiki/Elo_rating_system

---

## 📌 Notes

- This roadmap is a living document and will be updated as features are completed
- Priorities may shift based on user feedback and development experience
- Some features may be combined or split as needed
- Estimated times are rough guidelines and may vary
- Focus on completing Tier 1 and Tier 2 before considering Tier 3 and beyond

**Last Updated:** May 25, 2026 (roadmap refresh)
