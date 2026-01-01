# Swamp Darts - Update Changelog
**Date:** December 31, 2024

## 🎯 Golf Mode - Major Enhancements

### New Game Modes
- **Match Play**: Head-to-head competition, win the most holes
  - Green highlighting on won holes in scorecard
  - Displays holes won instead of stroke total
  
- **Skins**: Win holes outright, ties carry over
  - Green highlighting on won holes
  - Displays skins won instead of stroke total
  
- **Stroke Play**: Traditional scoring (existing, now one of three modes)

### Player Support
- Increased from **1-4 players** to **1-6 players**

### Tie Breaker System
- **Toggle-able**: Can enable/disable in sidebar (enabled by default)
- **Activation**: Triggers when 2+ players tied for first after hole 18
- **Holes 19-20**: 
  - Hole 19: Players go in order (P1, P2, P3...)
  - Hole 20: Players go in reverse order (last to first)
- **Winner determination**: Best combined score on holes 19+20
- **Replay logic**: If still tied after hole 20, automatically replays holes 19-20 until winner emerges
- **Multi-way ties**: Works with any number of tied players (2, 3, 4, 5, or 6)
- **Stats handling**: Only first 18 holes saved to Google Sheets (holes 19-20 purely for determining winner)

### Visual Enhancements
- **Color-coded scoring**:
  - 🟢 Green: Under par
  - 🔴 Red: Over par
  - ⚪ White: Even par
  - Applied to both: top stat cards AND scorecard totals
  
- **Active player highlighting**: 
  - Subtle blue tint on active player's row in scorecard
  - Only highlights on the half (OUT/IN/TB) they're currently playing
  
- **Player name size**: Doubled from 14px to 28px in stat cards
- **Par display**: Now color-coded to match score color

### UI Reorganization
- Camera controls moved to bottom of sidebar
- Sidebar order now: Venue → Game Mode → Tie Breaker → Players → Camera → Reset

### Tie Breaker Card Display
- Shows ABOVE regular OUT/IN scorecards when active
- Lists all players currently in tie breaker
- Shows holes 19 and 20
- Updates automatically during replays

---

## 🥊 Cricket KO Mode - Stats & Analytics

### Stats Tracking & Saving
- **Full match statistics** saved to Google Sheets
- **New worksheet**: "Cricket_Matches" (separate from Golf)
- **Stats tracked**:
  - Match metadata (ID, Date, Venue, Game Mode)
  - Player placement (1st, 2nd, 3rd, 4th)
  - Performance: Total Marks, Total Darts, Marks Per Dart (MPD), Accuracy %
  - Board stats: Darts to Close
  - Combat: KO Hits Given/Received, Players Eliminated, Was Eliminated
  - PIN: PIN Attempts
  - Match outcome: Won Match (yes/no), Opponents list

### Stats Dashboard Enhancements
- **Top Player Stats** section (calculated from ALL data, not filtered):
  - Best Win Rate (% with player name)
  - Most Wins (count with player name)
  - Best MPD (with player name)
  - Best Accuracy (% with player name)
  - Best Streak (consecutive wins with player name)

- **Performance Graphs** (filtered data):
  - MPD Over Time (by game number, not date)
  - Accuracy Over Time
  - KO Hits Over Time
  - Interactive tooltips showing player, game number, stat, and date

- **Filter Controls**:
  - Players, Venues, Game Modes multiselects
  - "Select All" / "Clear" buttons below each filter
  - Persistent session state for selections

- **Additional Stats**:
  - Filtered Overview metrics
  - Player Performance table
  - Performance by Game Mode breakdown
  - Head-to-Head records
  - Match History

### Venue Management
- **Venue saving**: Works like player profiles
- Dropdown selection with saved venues
- "Custom" option to add new venues
- Save button to remember venues

### UI Updates
- Changed ice cube emoji (🧊) to boxing glove (🥊) throughout
- Updated home page to mention Cricket stats in Stats Dashboard description

---

## 📊 Stats Dashboard - General Improvements

### Golf Stats
- Added "Select All" / "Clear" buttons for Players filter
- Added "Select All" / "Clear" buttons for Venues filter
- Buttons appear below each multiselect

### Cricket Stats
- Toggle between "Golf" and "Cricket KO" at top of page
- Comprehensive analytics with graphs
- Filter controls for deep-dive analysis

---

## 🏠 Home Page Updates

### Golf Card
- Updated to mention: "3 game modes: Stroke Play, Match Play, Skins"
- Changed to "1-6 players" (was "1-4 players")
- Changed to "18 hole rounds" (removed "9 or" mention)
- Added "Tie breaker option (holes 19-20)"

### Cricket KO Card
- Changed emoji from 🧊 to 🥊

### Stats Dashboard Card
- Updated to mention "golf and cricket games"
- Changed feature list to "Golf & Cricket KO stats"

---

## 🔧 Technical Implementation Details

### Google Sheets Integration
- **Cricket_Matches worksheet** columns:
  ```
  Match_ID | Date | Venue | Game_Mode | Player | Placement | Total_Marks | 
  Total_Darts | Marks_Per_Dart | Accuracy_Pct | Darts_To_Close | 
  KO_Hits_Given | KO_Hits_Received | Players_Eliminated | Was_Eliminated | 
  PIN_Attempts | Won_Match | Opponents
  ```
- Stats only save first 18 holes for Golf (tie breaker excluded)
- No new permissions needed (uses existing credentials)

### Session State Management
- Golf: Added `game_mode`, `tie_breaker_enabled`, `in_tie_breaker`, `tie_breaker_players`
- Cricket: Filter states for players, venues, game modes
- Player scores extended to 20 holes (for tie breaker)

### Color Coding System
- CSS classes: `.under-par`, `.over-par`, `.even-par`
- Applied to `.stat-score` and `.par-under`/`.par-over`/`.par-even`
- Uses `!important` flags to override defaults

### Tie Breaker Logic
- Detects ties after hole 18 (2+ players with best score)
- Rotates player order between holes 19 and 20
- Replays automatically if still tied
- Handles multi-way ties and player elimination

---

## 📋 Files Modified

- `dart_golf_app_FIXED.py` - Main application file (all changes)

---

## 🚀 Next Steps / Future Enhancements

Potential future additions:
- More detailed number-specific stats for Cricket
- Win streak tracking
- Player profiles with lifetime stats
- Tournament mode
- Additional game modes

---

## 📝 Git Commit Message

**Short version:**
```
Golf & Cricket enhancements: Match Play, Skins, tie breakers, 6-player support, Cricket stats with graphs
```

**Detailed version:**
```
Golf & Cricket major enhancements

Golf updates:
- Added Match Play and Skins game modes
- Support for 1-6 players (up from 1-4)
- Tie breaker system (holes 19-20) with multi-way ties and replays
- Color-coded scoring (green/red/white for under/over/even par)
- Active player row highlighting in scorecard
- Camera controls moved to bottom of sidebar
- Larger player names in stat cards

Cricket updates:
- Full stats tracking and saving to Google Sheets
- Performance graphs (MPD, Accuracy, KO hits over time)
- Top player stats display
- Filter improvements with Select All/Clear buttons
- Venue saving like player profiles
- Boxing glove emoji updates

Stats Dashboard:
- Toggle between Golf and Cricket stats
- Comprehensive Cricket analytics
- Filter controls for both modes

UI improvements:
- Consistent color coding throughout
- Subtle active player highlighting
- Updated home page descriptions
```

---

## ✅ Testing Checklist

- [ ] Golf Stroke Play with 1-6 players
- [ ] Golf Match Play with green hole highlighting
- [ ] Golf Skins with carryover logic
- [ ] Tie breaker activation after hole 18
- [ ] Multi-way tie (3+ players)
- [ ] Tie breaker replay on continued tie
- [ ] Color coding (green/red/white) on scores
- [ ] Active player row highlighting
- [ ] Cricket match saving to Google Sheets
- [ ] Cricket stats graphs rendering
- [ ] Top player stats calculations
- [ ] Filter Select All/Clear buttons
- [ ] Venue saving and loading
- [ ] Camera controls at bottom of sidebar

---

**Build Date:** December 31, 2024
**Version:** 2.0 - The "Ultimate Darts Companion"
