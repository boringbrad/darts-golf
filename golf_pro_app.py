import streamlit as st
import os
import pandas as pd
from datetime import datetime
import json
import uuid
import random
import plotly.express as px
from streamlit_gsheets import GSheetsConnection


# 1. This MUST be the first Streamlit command
st.set_page_config(
    page_title="Swamp Darts",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
    <style>
        /* 1. GLOBAL BACKGROUNDS */
        [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main, [data-testid="stSidebar"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }

        /* 2. SIDEBAR SPECIFIC */
        [data-testid="stSidebarContent"] {
            background-color: #1e2129 !important;
        }

        /* 3. INPUT BOXES & DROPDOWNS */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] input, .stTextInput input {
            background-color: #1e2129 !important;
            color: #ffffff !important;
            border: 1px solid #00d4ff !important;
        }

        /* Dropdown menu items */
        div[data-baseweb="popover"] li {
            background-color: #1e2129 !important;
            color: #ffffff !important;
        }

        /* 4. FORCE ALL LABELS & TEXT TO WHITE */
        p, span, label, div, h1, h2, h3, [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        /* Override for player headers - allow custom colors */
        .player-header .player-name,
        .player-header .player-ko,
        .player-header .player-status {
            color: inherit !important;
        }

        /* 5. SCORECARD GRID FIX */
        [data-testid="column"] {
            background-color: #0e1117 !important;
        }

        /* 6. DEFAULT BUTTONS */
        .stButton > button {
            width: 100% !important;
            height: clamp(2rem, 4.5vh, 8rem) !important;
            font-size: clamp(0.85rem, 1.9vh, 2.5rem) !important;
            background-color: #1e2129 !important;
            border: 2px solid #00d4ff !important;
            color: white !important;
        }

        .stButton > button:hover:not(:disabled) {
            background: rgba(0, 212, 255, 0.2) !important;
        }

        .block-container {
            padding-top: clamp(3.5rem, 7vh, 7.5rem) !important;
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
            padding-left: clamp(0.5rem, 1vw, 1.5rem) !important;
            padding-right: clamp(0.5rem, 1vw, 1.5rem) !important;
        }

        /* Aggressive bottom spacing removal for all containers */
        .main, .main > div, .main > div > div,
        section.main, section.main > div, section.main > div > div,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        [data-testid="stVerticalBlock"]:last-child,
        .element-container:last-child,
        div[class*="css"]:last-child {
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }

        /* Remove default Streamlit bottom padding */
        footer {
            display: none !important;
        }

        .player-header > div {
            padding: clamp(4px, 0.7vh, 12px) !important;
            margin-bottom: clamp(2px, 0.4vh, 8px) !important;
        }

        .player-header {
            margin-bottom: clamp(2px, 0.4vh, 10px) !important;
        }

        .cricket-mark {
            font-size: clamp(20px, 4.5vh, 90px) !important;
            height: clamp(28px, 5.5vh, 100px) !important;
            line-height: 1 !important;
        }

        .dart-counter {
            font-size: clamp(10px, 1.6vh, 28px) !important;
            line-height: 1.3 !important;
        }

        [data-testid="stVerticalBlock"] {
            gap: clamp(0.15rem, 0.3vh, 0.6rem) !important;
        }

        [data-testid="stHorizontalBlock"] {
            gap: clamp(0.2rem, 0.4vh, 0.7rem) !important;
        }

        [data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
        }

        h1, h2, h3 {
            margin: clamp(0.3rem, 0.7vh, 1rem) 0 !important;
            line-height: 1.3 !important;
        }

        /* Sidebar radio button alignment */
        [data-testid="stSidebar"] [role="radiogroup"] {
            gap: 0.5rem !important;
        }

        [data-testid="stSidebar"] [role="radio"] {
            display: flex !important;
            align-items: center !important;
        }

        [data-testid="stSidebar"] label[data-baseweb="radio"] {
            display: flex !important;
            align-items: center !important;
            padding: 0.5rem 0 !important;
        }

        /* Hide the "Navigation" label for the radio group */
        [data-testid="stSidebar"] .row-widget.stRadio > label {
            display: none !important;
        }

        div {
            margin-block-start: 0 !important;
            margin-block-end: 0 !important;
        }

    </style>
    """, unsafe_allow_html=True)

def hide_header():
    st.markdown("""
        <style>
            header[data-testid="stHeader"] {
                background-color: rgba(0,0,0,0);
                color: white;
            }
            [data-testid="stDecoration"] {
                display: none;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 0rem;
            }
            [data-testid="stSidebarCollapsedControl"] {
                color: white;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 5px;
            }
            footer {
                visibility: hidden;
            }
        </style>
        """, unsafe_allow_html=True)

hide_header()

# --- CRICKET KO FUNCTIONS ---
CRICKET_NUMBERS = [20, 19, 18, 17, 16, 15, 'B', 'T', 'D']

def get_mark_symbol(marks):
    if marks == 0: return ""
    elif marks == 1: return "／"
    elif marks == 2: return "╳"
    elif marks >= 3: return "◉" + (f" +{marks-3}" if marks > 3 else "")

def check_board_closed(board):
    return all(marks >= 3 for marks in board.values())

def get_player_header_html(game, player_idx):
    """Generate HTML for a player's header box - now clickable for KO"""
    p_key = f"P{player_idx + 1}"
    is_active = player_idx == game['current_player_idx']
    is_skipped = game['ko_skipped'][p_key]
    is_eliminated = game['eliminated'][p_key]

    # Border style based on status
    if is_active:
        border_style = "border-left: 5px solid #ffff00;"  # Yellow bar for active
    elif is_skipped:
        border_style = "border-left: 5px solid #ff4444;"  # Red bar for skipped
    else:
        border_style = "border-left: 5px solid transparent;"  # Invisible to maintain spacing

    if is_eliminated:
        text_color = "#666"
    elif is_skipped:
        text_color = "#ff4444"
    elif is_active:
        text_color = "#ffff00"
    else:
        text_color = "#ffffff"

    # Show elimination progress only in non-tag-team multi-player games
    elim_progress_html = ""
    if any(game['board_closed'].values()) and not is_eliminated and not game['is_tag_team'] and game['num_players'] > 2:
        # Elimination phase active
        ko_hits = game['ko_elimination_progress'][p_key]
        dots = ["●" if i < ko_hits else "○" for i in range(3)]
        elim_progress_html = f"<div style='font-size: 10px; color: #888; margin-top: 3px;'>KO: {' '.join(dots)}</div>"

    # Calculate font size based on name length - using viewport height for scaling with larger sizes
    name_length = len(game['player_names'][player_idx])
    if name_length <= 6:
        font_size = "clamp(14px, 2.8vh, 50px)"
    elif name_length <= 8:
        font_size = "clamp(13px, 2.5vh, 45px)"
    elif name_length <= 10:
        font_size = "clamp(12px, 2.3vh, 42px)"
    elif name_length <= 12:
        font_size = "clamp(11px, 2.1vh, 38px)"
    else:
        font_size = "clamp(10px, 1.9vh, 35px)"

    ko_font_size = "clamp(12px, 2.1vh, 38px)"

    # Return just the HTML - button will be created separately in Streamlit
    return f"""
    <div class="player-header" style='text-align: center; margin-bottom: clamp(2px, 0.4vh, 10px);'>
        <div style='{border_style} border-radius: clamp(3px, 0.6vh, 12px); padding: clamp(4px, 0.7vh, 16px); background: rgba(255, 255, 255, 0.02);'>
            <div class="player-name" style='width: 100%; min-height: clamp(18px, 3.2vh, 55px); display: flex; align-items: center; justify-content: center;'>
                <span style='
                    font-weight: bold;
                    font-size: {font_size};
                    color: {text_color};
                    white-space: nowrap;
                    overflow: visible;
                    text-overflow: clip;
                    line-height: 1.3;
                '>{game['player_names'][player_idx]}</span>
            </div>
            <div class="player-ko"><span style='font-size: {ko_font_size}; color: {text_color}; line-height: 1.3;'>KO: {game['ko_numbers'][p_key]}</span></div>
        </div>
        {elim_progress_html}
    </div>
    """

def advance_to_next_player(game):
    """Advance to next non-eliminated player, handling tag team rotation"""
    if game['is_tag_team']:
        # Tag team: alternate between teams
        # P1(T1) → P3(T2) → P2(T1) → P4(T2) → P1...
        current = game['current_player_idx']
        if current == 0:  # P1 → P3
            next_idx = 2
        elif current == 2:  # P3 → P2
            next_idx = 1
        elif current == 1:  # P2 → P4
            next_idx = 3
        else:  # P4 → P1
            next_idx = 0
        game['current_player_idx'] = next_idx
    else:
        # Regular rotation, skip eliminated players
        next_idx = (game['current_player_idx'] + 1) % game['num_players']
        while game['eliminated'][f"P{next_idx + 1}"]:
            next_idx = (next_idx + 1) % game['num_players']
        game['current_player_idx'] = next_idx

def update_pin_count(current_pin, player_idx, player_board_closed):
    """
    Update pin count when PIN button is pressed.
    Player 0 (P1) moves in positive direction (+1, +2, +3)
    Player 1 (P2) moves in negative direction (-1, -2, -3)
    
    Logic:
    - Can always reverse opponent's pin (move toward 0)
    - Can only advance in YOUR direction if YOUR board is closed
    """
    if player_idx == 0:  # Player 1 (positive direction)
        if current_pin >= 0:
            # Moving in our direction - need board closed
            if player_board_closed:
                return current_pin + 1
            else:
                return current_pin  # Can't advance without closed board
        else:
            # Reversing opponent's pin - always allowed
            return current_pin + 1
    else:  # Player 2 (negative direction)
        if current_pin <= 0:
            # Moving in our direction - need board closed
            if player_board_closed:
                return current_pin - 1
            else:
                return current_pin  # Can't advance without closed board
        else:
            # Reversing opponent's pin - always allowed
            return current_pin - 1

def initialize_cricket_game(num_players, player_names, game_mode):
    available = list(range(1, 21))
    random.shuffle(available)
    ko_numbers = {f"P{i+1}": available[i] for i in range(num_players)}
    
    is_tag_team = "Tag Team" in game_mode
    
    # In tag team, Team 1 is P1+P2, Team 2 is P3+P4
    # They share boards: Team 1 shares one board, Team 2 shares another
    if is_tag_team:
        cricket_boards = {
            'T1': {num: 0 for num in CRICKET_NUMBERS},  # Team 1 shared board
            'T2': {num: 0 for num in CRICKET_NUMBERS}   # Team 2 shared board
        }
        board_closed = {'T1': False, 'T2': False}
    else:
        cricket_boards = {f"P{i+1}": {num: 0 for num in CRICKET_NUMBERS} for i in range(num_players)}
        board_closed = {f"P{i+1}": False for i in range(num_players)}
    
    return {
        'num_players': num_players,
        'player_names': player_names,
        'game_mode': game_mode,
        'is_tag_team': is_tag_team,
        'cricket_boards': cricket_boards,
        'ko_numbers': ko_numbers,
        'ko_skipped': {f"P{i+1}": False for i in range(num_players)},
        'consecutive_skips': {f"P{i+1}": 0 for i in range(num_players)},
        'board_closed': board_closed,
        'eliminated': {f"P{i+1}": False for i in range(num_players)},
        'ko_elimination_progress': {f"P{i+1}": 0 for i in range(num_players)},
        'pin_progress': {f"P{i+1}": [] for i in range(num_players)},
        'current_player_idx': 0,
        'dart_count': 0,
        'marks_per_dart': [0, 0, 0],
        'dart_hits': ['', '', ''],
        'pin_count': 0,
        'game_over': False,
        'winner': None,
        # Stats tracking
        'total_darts': {f"P{i+1}": 0 for i in range(num_players)},
        'total_marks': {f"P{i+1}": 0 for i in range(num_players)},
        'ko_hits_given': {f"P{i+1}": 0 for i in range(num_players)},
        'ko_hits_received': {f"P{i+1}": 0 for i in range(num_players)},
        'pin_attempts': {f"P{i+1}": 0 for i in range(num_players)},
        'darts_to_close': {f"P{i+1}": None for i in range(num_players)},
        'board_close_dart_count': {f"P{i+1}": 0 for i in range(num_players)},
        'start_time': datetime.now(),
        'venue': 'Home'
    }

# --- 1. GOLF SETTINGS & DATA HELPERS ---
PROFILE_FILE = "profiles.txt"
VENUE_FILE = "venues.txt"
HISTORY_FILE = "golf_history_v2.csv"

def get_profiles():
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f: f.write("")
    with open(PROFILE_FILE, "r") as f:
        profiles = sorted(list(set([l.strip() for l in f.readlines() if l.strip()])))
        # Remove Guest if it exists in the list, then add it at the end
        if "Guest" in profiles:
            profiles.remove("Guest")
        profiles.append("Guest")
        return profiles

def save_profile(name):
    if name.strip():
        profiles = get_profiles()
        if name.strip() not in profiles:
            with open(PROFILE_FILE, "a") as f: f.write(f"\n{name.strip()}")

def delete_profile(name):
    """Delete a profile name from the profiles file"""
    if name.strip():
        profiles = get_profiles()
        if name in profiles:
            profiles.remove(name)
            with open(PROFILE_FILE, "w") as f:
                f.write("\n".join(profiles))

def get_venues():
    if not os.path.exists(VENUE_FILE):
        with open(VENUE_FILE, "w") as f: f.write("Home\nCustom")
    with open(VENUE_FILE, "r") as f:
        return sorted(list(set([l.strip() for l in f.readlines() if l.strip()])))

def save_venue(venue):
    if venue.strip() and venue.strip() != "Custom":
        with open(VENUE_FILE, "a") as f: f.write(f"\n{venue.strip()}")

def save_match_data(match_id, player_names, player_scores, venue):
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        existing_df = conn.read(worksheet="Matches", ttl=0)
    except:
        existing_df = pd.DataFrame(columns=["Match_ID", "Date", "Venue", "Player", "Total", "Hole_Scores", "Opponents"])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_rows = []
    for i, name in enumerate(player_names):
        # Only save first 18 holes (ignore tie breaker holes 19-20)
        scores = player_scores[f"P{i+1}"][:18]
        total = sum(x for x in scores if x is not None)
        opponents = ", ".join([p for p in player_names if p != name])
        new_rows.append({
            "Match_ID": match_id, 
            "Date": timestamp, 
            "Venue": venue,
            "Player": name,
            "Total": total, 
            "Hole_Scores": json.dumps(scores), 
            "Opponents": opponents
        })
    
    updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
    conn.update(worksheet="Matches", data=updated_df)
    st.success("✅ Match Synced to Google Sheets!")

def save_cricket_match(game):
    """Save Cricket KO match stats to Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    match_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        existing_df = conn.read(worksheet="Cricket_Matches", ttl=0)
    except:
        existing_df = pd.DataFrame(columns=[
            "Match_ID", "Date", "Venue", "Game_Mode", "Player", "Placement",
            "Total_Marks", "Total_Darts", "Marks_Per_Dart", "Accuracy_Pct",
            "Darts_To_Close", "KO_Hits_Given", "KO_Hits_Received",
            "Players_Eliminated", "Was_Eliminated", "PIN_Attempts",
            "Won_Match", "Opponents"
        ])
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_rows = []
    
    # Determine placements and winner
    placements = determine_cricket_placements(game)
    winner_idx = placements[0] if placements else 0
    
    for i in range(game['num_players']):
        player_name = game['player_names'][i]
        p_key = f"P{i+1}"
        
        # Get player's board (handle tag team)
        if game['is_tag_team']:
            board_key = 'T1' if i < 2 else 'T2'
            board = game['cricket_boards'][board_key]
        else:
            board = game['cricket_boards'][p_key]
        
        total_marks = sum(board.values())
        total_darts = game['total_darts'][p_key]
        mpd = round(total_marks / total_darts, 2) if total_darts > 0 else 0
        accuracy = round((total_marks / total_darts * 100), 1) if total_darts > 0 else 0
        
        # Count eliminations (how many players this player eliminated)
        eliminations = 0
        for j in range(game['num_players']):
            if i != j and game['eliminated'][f"P{j+1}"]:
                # Check if this player got the final KO hit
                if game['ko_elimination_progress'][f"P{j+1}"] >= 3:
                    eliminations += 1
        
        opponents = ", ".join([game['player_names'][j] for j in range(game['num_players']) if j != i])
        placement = placements.index(i) + 1 if i in placements else game['num_players']
        
        new_rows.append({
            "Match_ID": match_id,
            "Date": timestamp,
            "Venue": game.get('venue', 'Home'),
            "Game_Mode": game['game_mode'],
            "Player": player_name,
            "Placement": f"{placement}{'st' if placement==1 else 'nd' if placement==2 else 'rd' if placement==3 else 'th'}",
            "Total_Marks": total_marks,
            "Total_Darts": total_darts,
            "Marks_Per_Dart": mpd,
            "Accuracy_Pct": accuracy,
            "Darts_To_Close": game['darts_to_close'][p_key] if game['darts_to_close'][p_key] else "",
            "KO_Hits_Given": game['ko_hits_given'][p_key],
            "KO_Hits_Received": game['ko_hits_received'][p_key],
            "Players_Eliminated": eliminations,
            "Was_Eliminated": game['eliminated'][p_key],
            "PIN_Attempts": game['pin_attempts'][p_key],
            "Won_Match": (i == winner_idx),
            "Opponents": opponents
        })
    
    updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
    conn.update(worksheet="Cricket_Matches", data=updated_df)
    st.success("✅ Cricket Match Synced to Google Sheets!")

def determine_cricket_placements(game):
    """Determine final placements for cricket match (returns list of player indices in order)"""
    if game.get('winner') is not None:
        # Game finished with a winner
        winner = game['winner']
        # Sort others by: not eliminated, then by marks, then by darts to close
        others = []
        for i in range(game['num_players']):
            if i != winner:
                p_key = f"P{i+1}"
                if game['is_tag_team']:
                    board_key = 'T1' if i < 2 else 'T2'
                    marks = sum(game['cricket_boards'][board_key].values())
                else:
                    marks = sum(game['cricket_boards'][p_key].values())
                
                others.append((i, not game['eliminated'][p_key], marks, -game['total_darts'][p_key]))
        
        others.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        return [winner] + [x[0] for x in others]
    else:
        # Game not finished, rank by marks
        rankings = []
        for i in range(game['num_players']):
            p_key = f"P{i+1}"
            if game['is_tag_team']:
                board_key = 'T1' if i < 2 else 'T2'
                marks = sum(game['cricket_boards'][board_key].values())
            else:
                marks = sum(game['cricket_boards'][p_key].values())
            rankings.append((i, marks, -game['total_darts'][p_key]))
        
        rankings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return [x[0] for x in rankings]

# --- 2. NAVIGATION ---
st.sidebar.title("🎮 Navigation")
page = st.sidebar.radio("Navigation", ["Home", "Golf", "KO Cricket", "Royal Rumble", "Stats Dashboard", "Manage Profiles"], label_visibility="collapsed")

# --- PAGE 0: HOME ---
if page == "Home":
    st.markdown("""
    <div style='text-align: center; padding: 40px 0;'>
        <h1 style='font-size: 48px; margin-bottom: 20px;'>Swamp Darts</h1>
        <p style='font-size: 20px; color: #888; margin-bottom: 40px;'>Your complete darts scoring and analytics platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Game modes section
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.05); border-radius: 12px; padding: 30px; height: 100%;'>
            <h2 style='text-align: center; margin-bottom: 20px;'>⛳ Golf</h2>
            <p style='color: #ccc; line-height: 1.6;'>
            Classic darts golf with multiple game modes. Track your shots, view live leaderboards,
            and save match results to the cloud.
            </p>
            <ul style='color: #aaa; margin-top: 15px;'>
                <li>3 game modes: Stroke Play, Match Play, Skins</li>
                <li>1-6 players</li>
                <li>18 hole rounds + tie breakers</li>
                <li>Live leaderboard</li>
                <li>Camera feed option</li>
                <li>Cloud save to Google Sheets</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.05); border-radius: 12px; padding: 30px; height: 100%;'>
            <h2 style='text-align: center; margin-bottom: 20px;'>🥊 KO Cricket</h2>
            <p style='color: #ccc; line-height: 1.6;'>
            Cricket with a knockout twist! Close your board, then battle in the PIN phase with a tug-of-war mechanic.
            </p>
            <ul style='color: #aaa; margin-top: 15px;'>
                <li>4 game modes: 1v1, Tag Team, Triple Threat, Fatal 4 Way</li>
                <li>KO skip mechanic</li>
                <li>Elimination rounds</li>
                <li>PIN tug-of-war endgame</li>
                <li>Camera feed option</li>
                <li>Detailed stats tracking</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.05); border-radius: 12px; padding: 30px; height: 100%;'>
            <h2 style='text-align: center; margin-bottom: 20px;'>💀 Royal Rumble</h2>
            <p style='color: #ccc; line-height: 1.6;'>
            Battle royale cricket! Players enter at timed intervals. Hit opponents to give them marks, hit yourself to heal. Last player standing wins!
            </p>
            <ul style='color: #aaa; margin-top: 15px;'>
                <li>3-20 players</li>
                <li>Timed player entries</li>
                <li>Custom entrance music</li>
                <li>Healing mechanic</li>
                <li>No-healing endgame phase</li>
                <li>Undo support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.05); border-radius: 12px; padding: 30px; height: 100%;'>
            <h2 style='text-align: center; margin-bottom: 20px;'>📊 Stats Dashboard</h2>
            <p style='color: #ccc; line-height: 1.6;'>
            Comprehensive analytics for your golf and cricket games. View player performance, match history, and detailed scoring breakdowns.
            </p>
            <ul style='color: #aaa; margin-top: 15px;'>
                <li>Golf & Cricket KO stats</li>
                <li>Player performance metrics</li>
                <li>Match history</li>
                <li>Head-to-head records</li>
                <li>Scoring trends</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    
    # Getting started section
    st.markdown("""
    <div style='background: rgba(255,255,255,0.08); border-radius: 12px; padding: 30px; margin-top: 40px;'>
        <h2 style='margin-bottom: 20px;'>🚀 Getting Started</h2>
        <ol style='color: #ccc; line-height: 2; font-size: 16px;'>
            <li><strong>Choose a game mode</strong> from the navigation menu on the left</li>
            <li><strong>Set up players</strong> in the sidebar (save profiles for quick access)</li>
            <li><strong>Configure game settings</strong> like number of holes or game mode</li>
            <li><strong>Optional:</strong> Enable camera feed to view your dartboard while playing</li>
            <li><strong>Start playing!</strong> Track scores in real-time</li>
            <li><strong>Save your match</strong> to view stats and history later</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    
    # Quick tips
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 14px; padding: 20px;'>
        <p>💡 <strong>Tip:</strong> Player profiles are saved locally. Use the same name across sessions to track your progress!</p>
        <p>📱 <strong>Janky Mobile:</strong> Needs latest iphone OS, formatting is kind of jank</p>
    </div>
    """, unsafe_allow_html=True)

# --- PAGE 1: GOLF ---
elif page == "Golf":
    def calculate_holes_won(player_scores, num_players, mode):
        """Calculate holes won for Match Play or Skins modes"""
        holes_won = {f"P{i+1}": 0 for i in range(num_players)}
        
        if mode == "Match Play":
            # Head-to-head: compare each player against all others for each hole
            for hole in range(18):
                hole_scores = {}
                for i in range(num_players):
                    score = player_scores[f"P{i+1}"][hole]
                    if score is not None:
                        hole_scores[f"P{i+1}"] = score
                
                if len(hole_scores) >= 2:  # At least 2 players have scored
                    min_score = min(hole_scores.values())
                    winners = [p for p, s in hole_scores.items() if s == min_score]
                    
                    if len(winners) == 1:  # One winner (not a tie)
                        holes_won[winners[0]] += 1
        
        elif mode == "Skins":
            # Skins: win the hole outright (no ties), carries over
            carryover = 1  # Number of skins worth for this hole
            
            for hole in range(18):
                hole_scores = {}
                for i in range(num_players):
                    score = player_scores[f"P{i+1}"][hole]
                    if score is not None:
                        hole_scores[f"P{i+1}"] = score
                
                if len(hole_scores) >= 2:  # At least 2 players have scored
                    min_score = min(hole_scores.values())
                    winners = [p for p, s in hole_scores.items() if s == min_score]
                    
                    if len(winners) == 1:  # One winner (not a tie) - wins the skin(s)
                        holes_won[winners[0]] += carryover
                        carryover = 1  # Reset
                    else:  # Tie - skin carries over
                        carryover += 1
        
        return holes_won
    
    def calculate_hole_winner(player_scores, hole_idx, num_players):
        """Returns list of player keys who won this hole (empty if tie or incomplete)"""
        hole_scores = {}
        for i in range(num_players):
            score = player_scores[f"P{i+1}"][hole_idx]
            if score is not None:
                hole_scores[f"P{i+1}"] = score
        
        if len(hole_scores) >= 2:
            min_score = min(hole_scores.values())
            winners = [p for p, s in hole_scores.items() if s == min_score]
            if len(winners) == 1:  # Clear winner
                return winners
        return []
    
    def inject_custom_css(width_px):
        st.markdown(f"""
            <style>
            .block-container {{
                padding-top: clamp(3.5rem, 7vh, 7.5rem) !important;
                padding-bottom: 0 !important;
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
            }}
            [data-testid="stCameraInput"], [data-testid="stCameraInput"] > div,
            [data-testid="stCameraInput"] > div > div, [data-testid="stCameraInput"] canvas {{
                width: {width_px}px !important; height: auto !important; 
                min-height: unset !important; max-height: unset !important; margin: 0 auto !important;
            }}
            [data-testid="stCameraInput"] > div:first-child {{ display: none !important; }}
            [data-testid="stCameraInput"] video {{
                width: {width_px}px !important; height: auto !important;
                border-radius: 15px; border: 4px solid #00d4ff; object-fit: contain !important;
            }}
            .stat-card {{ flex: 1; background: #111; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; }}
            .stat-card.active {{ border: 2px solid #00d4ff; background: rgba(0, 212, 255, 0.1); }}
            .stat-name {{ font-size: 28px; color: #888; text-transform: uppercase; font-weight: bold; }}
            .stat-score {{ font-size: 36px; font-weight: 900; line-height: 1; color: white; }}
            .stat-score.under-par {{ color: #00ff88 !important; }}
            .stat-score.over-par {{ color: #ff4b4b !important; }}
            .stat-score.even-par {{ color: white !important; }}
            .par-under {{ color: #00ff88 !important; font-size: 18px; font-weight: bold; }}
            .par-over {{ color: #ff4b4b !important; font-size: 18px; font-weight: bold; }}
            .par-even {{ color: white !important; font-size: 18px; font-weight: bold; }}
            .par-over {{ color: #ff4b4b; font-size: 18px; font-weight: bold; }}
            .par-even {{ color: #888; font-size: 18px; font-weight: bold; }}
            .golf-table {{ width: 100%; border-collapse: collapse; color: white; table-layout: fixed; margin-top: 20px; }}
            .golf-header {{ background-color: #1a2a4a; border: 1px solid #444; text-align: center; padding: 10px; font-weight: bold; font-size: clamp(1.2rem, 2.5vh, 2.5rem); }}
            .golf-cell {{ border: 1px solid #444; text-align: center; padding: 10px; font-size: 18px; }}
            .hole-winner {{ background-color: #00ff88 !important; color: black !important; font-weight: bold; }}
            .active-hole-head {{ background-color: #00d4ff !important; color: black !important; font-weight: 900; }}
            .active-player-row {{ background-color: rgba(0, 212, 255, 0.04) !important; }}
            div[data-testid="stHorizontalBlock"] > div:last-child button {{ background-color: #333 !important; color: #ff4b4b !important; border: 1px solid #ff4b4b !important; }}
            </style>
        """, unsafe_allow_html=True)

    if 'player_scores' not in st.session_state:
        st.session_state.update({
            'player_scores': {f"P{i}": [None]*20 for i in range(1,7)},  # 20 holes for tie breaker
            'current_hole': 0, 'active_idx': 0, 'game_over': False,
            'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper(),
            'game_mode': 'Stroke Play', 'tie_breaker_enabled': True,
            'in_tie_breaker': False, 'tie_breaker_players': []
        })

    with st.sidebar:
        st.title("⛳ Match Setup")
        st.subheader("📍 Venue")
        venue_list = ["The Mullet", "Cake House", "Smokey Mountain", "Other"]
        venue_choice = st.selectbox("Where are we playing?", venue_list)
        if venue_choice == "Other":
            final_venue = st.text_input("Enter Venue Name", "Private Club")
        else:
            final_venue = venue_choice
        
        st.divider()
        
        # Game Mode Selection
        st.subheader("🎮 Game Mode")
        game_mode = st.selectbox(
            "Select Mode",
            ["Stroke Play", "Match Play", "Skins"],
            index=["Stroke Play", "Match Play", "Skins"].index(st.session_state.get('game_mode', 'Stroke Play'))
        )
        st.session_state.game_mode = game_mode
        
        if game_mode == "Stroke Play":
            st.caption("Traditional scoring - lowest total score wins")
        elif game_mode == "Match Play":
            st.caption("Head-to-head - win the most holes")
        else:  # Skins
            st.caption("Win holes outright - ties carry over")
        
        # Tie Breaker Toggle
        tie_breaker_enabled = st.checkbox("Enable Tie Breaker (Holes 19-20)", value=st.session_state.get('tie_breaker_enabled', True))
        st.session_state.tie_breaker_enabled = tie_breaker_enabled
        if tie_breaker_enabled:
            st.caption("If tied after 18 holes, play holes 19-20")
        
        st.divider()
        
        # Player Setup
        num_players = st.slider("Players", 1, 6, 2)
        names = []
        profiles = get_profiles()
        for i in range(1, num_players + 1):
            p_key = f"sel_p{i}"
            def_idx = 0 if profiles else 0  # Default to first profile
            sel = st.selectbox(f"Player {i}", profiles, index=def_idx, key=p_key)
            if sel == "Guest":
                g_name = st.text_input(f"Guest {i} Name", f"Guest {i}", key=f"g_name_{i}")
                names.append(g_name)
                if st.button(f"💾 Save '{g_name}'", key=f"save_p{i}"):
                    save_profile(g_name); st.rerun()
            else: names.append(sel)
        
        st.divider()

        # Initialize camera settings in session state
        if 'golf_camera_size_val' not in st.session_state:
            st.session_state.golf_camera_size_val = 800
        if 'golf_camera_scale_val' not in st.session_state:
            st.session_state.golf_camera_scale_val = 1.0
        if 'golf_camera_x_val' not in st.session_state:
            st.session_state.golf_camera_x_val = 0
        if 'golf_camera_y_val' not in st.session_state:
            st.session_state.golf_camera_y_val = 0

        # Camera Controls
        camera_on = st.toggle("📹 Camera Feed", value=False, key="golf_camera_toggle")
        if camera_on:
            camera_size = st.slider("Box Size", 200, 2000, value=st.session_state.golf_camera_size_val, step=50, key="golf_camera_size")
            camera_scale = st.slider("Scale", 0.5, 3.0, value=st.session_state.golf_camera_scale_val, step=0.1, key="golf_camera_scale")
            camera_x = st.slider("Position X (%)", -50, 50, value=st.session_state.golf_camera_x_val, step=1, key="golf_camera_x")
            camera_y = st.slider("Position Y (%)", -50, 50, value=st.session_state.golf_camera_y_val, step=1, key="golf_camera_y")

            # Store values in session state
            st.session_state.golf_camera_size_val = camera_size
            st.session_state.golf_camera_scale_val = camera_scale
            st.session_state.golf_camera_x_val = camera_x
            st.session_state.golf_camera_y_val = camera_y
        else:
            # Use stored values even when camera is off
            camera_size = st.session_state.golf_camera_size_val
            camera_scale = st.session_state.golf_camera_scale_val
            camera_x = st.session_state.golf_camera_x_val
            camera_y = st.session_state.golf_camera_y_val

        if st.button("🔄 Reset Match"):
            st.session_state.update({
                'player_scores': {f"P{i}": [None]*20 for i in range(1,7)}, 
                'current_hole': 0, 'active_idx': 0, 'game_over': False, 
                'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper(),
                'game_mode': game_mode, 'tie_breaker_enabled': tie_breaker_enabled,
                'in_tie_breaker': False, 'tie_breaker_players': []
            })
            st.rerun()

    inject_custom_css(camera_size)

    # Layout: Camera (C1-4) + Game (C5-9) if camera on, otherwise Game uses full width
    if camera_on:
        import streamlit.components.v1 as components

        layout_cols = st.columns([4, 5])

        # Camera feed (left side)
        with layout_cols[0]:
            camera_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ margin: 0; padding: 0; }}
                    #camera-container {{
                        width: {camera_size}px;
                        height: {camera_size}px;
                        overflow: hidden;
                        position: relative;
                        border: 2px solid #444;
                        border-radius: 10px;
                        background: black;
                    }}
                    #video {{
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        width: auto;
                        height: auto;
                        min-width: 100%;
                        min-height: 100%;
                        transform: translate(calc(-50% + {camera_x}%), calc(-50% + {camera_y}%)) scale({camera_scale});
                        object-fit: cover;
                    }}
                </style>
            </head>
            <body>
                <div id="camera-container">
                    <video id="video" autoplay playsinline></video>
                </div>
                <script>
                    navigator.mediaDevices.getUserMedia({{
                        video: {{
                            facingMode: 'environment',
                            width: {{ ideal: 1920 }},
                            height: {{ ideal: 1080 }}
                        }},
                        audio: false
                    }})
                    .then(stream => {{
                        document.getElementById('video').srcObject = stream;
                    }})
                    .catch(err => {{
                        console.error('Camera error:', err);
                        document.getElementById('camera-container').innerHTML = '<p style="color: white; padding: 20px;">Camera access denied or unavailable</p>';
                    }});
                </script>
            </body>
            </html>
            """
            components.html(camera_html, height=camera_size + 10)

        # Game content (right side)
        with layout_cols[1]:
            game_container = st.container()
    else:
        # No camera - use full width
        game_container = st.container()

    with game_container:
        cols = st.columns(num_players)

        # Calculate holes won if in Match Play or Skins mode (only first 18 holes)
        game_mode = st.session_state.game_mode
        if game_mode in ["Match Play", "Skins"]:
            holes_won_dict = calculate_holes_won(st.session_state.player_scores, num_players, game_mode)
        
        # Check if we're in tie breaker mode
        in_tie_breaker = st.session_state.get('in_tie_breaker', False)
        
        for i in range(num_players):
            p_sc = st.session_state.player_scores[f"P{i+1}"]
            
            # Display different totals based on game mode (only first 18 holes for regular scoring)
            if game_mode in ["Match Play", "Skins"]:
                # Show holes won (from first 18 holes)
                display_total = holes_won_dict[f"P{i+1}"]
                display_label = "Holes Won" if game_mode == "Match Play" else "Skins Won"
                par_str = ""
                par_class = "par-even"
                
                # Add tie breaker scores if applicable
                if in_tie_breaker and f"P{i+1}" in st.session_state.get('tie_breaker_players', []):
                    tb_score = sum(x for x in p_sc[18:20] if x is not None)
                    if tb_score > 0:
                        par_str = f"TB: {tb_score}"
            else:
                # Stroke Play - show traditional score (first 18 holes)
                total = sum(x for x in p_sc[:18] if x is not None)
                display_total = total
                display_label = "Total Score"
                holes_played = sum(1 for x in p_sc[:18] if x is not None)
                rel_par = total - (holes_played * 4)
                par_str = f"{rel_par:+}" if rel_par != 0 else "E"
                par_class = "par-under" if rel_par < 0 else "par-over" if rel_par > 0 else "par-even"
                
                # Add tie breaker scores if applicable
                if in_tie_breaker and f"P{i+1}" in st.session_state.get('tie_breaker_players', []):
                    tb_score = sum(x for x in p_sc[18:20] if x is not None)
                    if tb_score > 0:
                        par_str += f" | TB: {tb_score}"
            active = "active" if i == st.session_state.active_idx and not st.session_state.game_over else ""
            
            # Determine score color class for Stroke Play mode
            if game_mode == "Stroke Play":
                holes_played = sum(1 for x in p_sc[:18] if x is not None)
                if holes_played > 0:
                    rel_par = display_total - (holes_played * 4)
                    if rel_par < 0:
                        score_color_class = "under-par"
                    elif rel_par > 0:
                        score_color_class = "over-par"
                    else:
                        score_color_class = "even-par"
                else:
                    score_color_class = "even-par"
            else:
                score_color_class = "even-par"  # No coloring for Match Play/Skins
            
            if par_str:
                cols[i].markdown(f"<div class='stat-card {active}'><div class='stat-name'>{names[i]}</div><div class='stat-score {score_color_class}'>{display_total}</div><div class='{par_class}'>{par_str}</div></div>", unsafe_allow_html=True)
            else:
                cols[i].markdown(f"<div class='stat-card {active}'><div class='stat-name'>{names[i]}</div><div class='stat-score {score_color_class}'>{display_total}</div><div style='font-size: 14px; color: #888; margin-top: 5px;'>{display_label}</div></div>", unsafe_allow_html=True)
    
        def draw_card(start, end, label):
            html = f"<table class='golf-table'><tr><td class='golf-header' style='width:100px;'>{label}</td>"
            for h in range(start, end): 
                active_h = "active-hole-head" if h == st.session_state.current_hole and not st.session_state.game_over else ""
                html += f"<td class='golf-header {active_h}'>{h+1}</td>"
            html += "<td class='golf-header' style='background:#00d4ff; color:black;'>TOT</td></tr>"
            
            for i in range(num_players):
                p_s = st.session_state.player_scores[f"P{i+1}"]
                
                # Check if this player is active AND current hole is in this card's range
                is_active_player = (i == st.session_state.active_idx and 
                                  not st.session_state.game_over and
                                  start <= st.session_state.current_hole < end)
                row_class = "active-player-row" if is_active_player else ""
                
                html += f"<tr class='{row_class}'><td class='golf-cell' style='text-align:left;'>{names[i]}</td>"
                
                for h in range(start, end):
                    score_val = p_s[h] if p_s[h] is not None else '-'
                    
                    # Check if this player won this hole (for Match Play/Skins)
                    winner_class = ""
                    if game_mode in ["Match Play", "Skins"] and p_s[h] is not None and h < 18:  # Only first 18 holes
                        winners = calculate_hole_winner(st.session_state.player_scores, h, num_players)
                        if f"P{i+1}" in winners:
                            winner_class = "hole-winner"
                    
                    html += f"<td class='golf-cell {winner_class}'>{score_val}</td>"
                
                # Total column - show appropriate total (only first 18 or tie breaker range)
                if game_mode in ["Match Play", "Skins"]:
                    if start >= 18:  # Tie breaker card
                        tot_display = sum(x for x in p_s[start:end] if x is not None)
                    else:
                        tot_display = holes_won_dict[f"P{i+1}"]
                    tot_color = "white"  # No par coloring for Match Play/Skins
                else:
                    # Stroke Play - calculate total and par
                    tot_display = sum(x for x in p_s[start:end] if x is not None)
                    holes_in_range = sum(1 for x in p_s[start:end] if x is not None)
                    par_for_range = holes_in_range * 4
                    rel_par = tot_display - par_for_range
                    
                    # Determine color based on par
                    if rel_par < 0:
                        tot_color = "#00ff88"  # Under par - green
                    elif rel_par > 0:
                        tot_color = "#ff4b4b"  # Over par - red
                    else:
                        tot_color = "white"    # Even par - white
                
                html += f"<td class='golf-cell' style='font-weight:bold; color:{tot_color};'>{tot_display}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
    
        # Show tie breaker card ABOVE regular scorecards if in tie breaker mode
        if st.session_state.get('in_tie_breaker', False):
            st.markdown("### 🏆 TIE BREAKER")
            tie_players = st.session_state.get('tie_breaker_players', [])
            if tie_players:
                player_names_in_tie = ', '.join([names[int(p[1:])-1] for p in tie_players])
                st.caption(f"Players in tie breaker: {player_names_in_tie}")
            draw_card(18, 20, "TB")
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        
        draw_card(0, 9, "OUT")
        draw_card(9, 18, "IN")
    
        if not st.session_state.game_over:
            btn_cols = st.columns([1,1,1,1,1,1,1.5])
            def submit(val):
                st.session_state.history_stack.append({
                    'player_scores': {k: list(v) for k, v in st.session_state.player_scores.items()}, 
                    'current_hole': st.session_state.current_hole, 
                    'active_idx': st.session_state.active_idx,
                    'in_tie_breaker': st.session_state.get('in_tie_breaker', False),
                    'tie_breaker_players': st.session_state.get('tie_breaker_players', [])
                })
                
                # Record score for current player
                st.session_state.player_scores[f"P{st.session_state.active_idx + 1}"][st.session_state.current_hole] = val
                
                # Handle tie breaker mode separately
                in_tie_breaker = st.session_state.get('in_tie_breaker', False)
                
                if in_tie_breaker:
                    # Tie breaker player rotation logic
                    tie_players = st.session_state.tie_breaker_players
                    current_player_key = f"P{st.session_state.active_idx + 1}"
                    current_tb_idx = tie_players.index(current_player_key)
                    
                    if st.session_state.current_hole == 18:  # Hole 19
                        # Players go in order
                        if current_tb_idx < len(tie_players) - 1:
                            # Move to next tie breaker player
                            next_player_key = tie_players[current_tb_idx + 1]
                            st.session_state.active_idx = int(next_player_key[1:]) - 1
                        else:
                            # All players done with hole 19, move to hole 20
                            st.session_state.current_hole = 19
                            # Reverse order for hole 20 - last player goes first
                            st.session_state.active_idx = int(tie_players[-1][1:]) - 1
                            
                    elif st.session_state.current_hole == 19:  # Hole 20
                        # Players go in reverse order
                        if current_tb_idx > 0:  # Not the first player in original order
                            # Move to previous player in tie_players list
                            next_player_key = tie_players[current_tb_idx - 1]
                            st.session_state.active_idx = int(next_player_key[1:]) - 1
                        else:
                            # All players done with hole 20 - check for winner
                            # Calculate tie breaker scores (holes 19-20 combined)
                            tb_scores = {}
                            for p in tie_players:
                                p_idx = int(p[1:]) - 1
                                tb_total = sum(x for x in st.session_state.player_scores[p][18:20] if x is not None)
                                tb_scores[p] = tb_total
                            
                            # Find best tie breaker score
                            if game_mode in ["Match Play", "Skins"]:
                                best_tb = max(tb_scores.values())  # Most holes won
                            else:
                                best_tb = min(tb_scores.values())  # Lowest score
                            
                            # Check if still tied
                            still_tied = [p for p, s in tb_scores.items() if s == best_tb]
                            
                            if len(still_tied) == 1:
                                # We have a winner!
                                st.session_state.game_over = True
                            else:
                                # Still tied - replay holes 19-20
                                # Clear holes 19-20 scores for tied players
                                for p in still_tied:
                                    st.session_state.player_scores[p][18] = None
                                    st.session_state.player_scores[p][19] = None
                                
                                # Update tie breaker players to only those still tied
                                st.session_state.tie_breaker_players = still_tied
                                tie_players = still_tied
                                
                                # Restart at hole 19 with first tied player
                                st.session_state.current_hole = 18
                                st.session_state.active_idx = int(tie_players[0][1:]) - 1
                else:
                    # Normal game flow
                    if st.session_state.active_idx < num_players - 1:
                        st.session_state.active_idx += 1
                    elif st.session_state.current_hole < 17:
                        st.session_state.current_hole += 1
                        st.session_state.active_idx = 0
                    else:
                        # Finished hole 18 - check for tie
                        if st.session_state.tie_breaker_enabled:
                            # Calculate scores/holes won for first 18 holes
                            if game_mode in ["Match Play", "Skins"]:
                                scores = holes_won_dict
                            else:
                                scores = {f"P{i+1}": sum(x for x in st.session_state.player_scores[f"P{i+1}"][:18] if x is not None) for i in range(num_players)}
                            
                            # Find the best score
                            if game_mode in ["Match Play", "Skins"]:
                                best_score = max(scores.values())  # Most holes/skins won
                            else:
                                best_score = min(scores.values())  # Lowest score
                            
                            # Find all players with best score
                            tied_players = [p for p, s in scores.items() if s == best_score]
                            
                            if len(tied_players) >= 2:  # 2 or more players tied for first
                                # Enter tie breaker mode
                                st.session_state.in_tie_breaker = True
                                st.session_state.tie_breaker_players = tied_players
                                st.session_state.current_hole = 18  # Start hole 19
                                # First-place player goes first
                                st.session_state.active_idx = int(tied_players[0][1:]) - 1
                            else:
                                # No tie - end game
                                st.session_state.game_over = True
                        else:
                            st.session_state.game_over = True
                
                st.rerun()
    
            for i in range(1, 7):
                if btn_cols[i-1].button(str(i), use_container_width=True): submit(i)
            if btn_cols[6].button("UNDO", use_container_width=True) and st.session_state.history_stack:
                prev = st.session_state.history_stack.pop()
                st.session_state.update({
                    'player_scores': prev['player_scores'], 
                    'current_hole': prev['current_hole'], 
                    'active_idx': prev['active_idx'],
                    'in_tie_breaker': prev.get('in_tie_breaker', False),
                    'tie_breaker_players': prev.get('tie_breaker_players', [])
                })
                st.rerun()
        else:
            if st.button(f"🏆 SAVE MATCH AT {final_venue.upper()}", use_container_width=True, type="primary"):
                save_match_data(st.session_state.match_id, names, st.session_state.player_scores, final_venue)
                st.session_state.update({
                    'player_scores': {f"P{i}": [None]*20 for i in range(1,7)}, 
                    'current_hole': 0, 'active_idx': 0, 'game_over': False, 
                    'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper(),
                    'game_mode': game_mode, 'tie_breaker_enabled': st.session_state.tie_breaker_enabled,
                    'in_tie_breaker': False, 'tie_breaker_players': []
                })
                st.rerun()
    
# --- PAGE 2: STATS DASHBOARD ---
elif page == "Stats Dashboard":
    # Stats type selector
    stats_type = st.radio("Stats Type", ["Golf", "Cricket KO"], horizontal=True)
    
    if stats_type == "Golf":
        st.title("📊 Elite Darts Golf Analytics")
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        try:
            df = conn.read(worksheet="Matches", ttl="1m")
            
            if df.empty:
                st.info("No match history found in Google Sheets.")
            else:
                df['Hole_Scores'] = df['Hole_Scores'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df['Total'] = pd.to_numeric(df['Total'])
                df['Rank'] = df.groupby('Match_ID')['Total'].rank(method='min', ascending=True)
                df['Is_Winner'] = df['Rank'] == 1

                st.sidebar.header("Filter Statistics")
                all_players = sorted(df['Player'].unique())
                all_venues = sorted(df['Venue'].unique())
                
                # Initialize session state for Golf filters
                if 'golf_selected_players' not in st.session_state:
                    st.session_state.golf_selected_players = all_players
                if 'golf_selected_venues' not in st.session_state:
                    st.session_state.golf_selected_venues = all_venues
                
                # Players filter
                selected_players = st.sidebar.multiselect(
                    "Select Players", 
                    options=all_players, 
                    default=st.session_state.golf_selected_players
                )
                st.session_state.golf_selected_players = selected_players
                
                col_p1, col_p2 = st.sidebar.columns(2)
                with col_p1:
                    if st.button("Select All", key="golf_select_all_players"):
                        st.session_state.golf_selected_players = all_players
                with col_p2:
                    if st.button("Clear", key="golf_clear_players"):
                        st.session_state.golf_selected_players = []
                
                # Venues filter
                selected_venues = st.sidebar.multiselect(
                    "Select Venues", 
                    options=all_venues, 
                    default=st.session_state.golf_selected_venues
                )
                st.session_state.golf_selected_venues = selected_venues
                
                col_v1, col_v2 = st.sidebar.columns(2)
                with col_v1:
                    if st.button("Select All", key="golf_select_all_venues"):
                        st.session_state.golf_selected_venues = all_venues
                with col_v2:
                    if st.button("Clear", key="golf_clear_venues"):
                        st.session_state.golf_selected_venues = []

            filtered_df = df[(df['Player'].isin(selected_players)) & (df['Venue'].isin(selected_venues))]

            st.subheader("📍 Venue Course Records")
            venue_records = df.loc[df.groupby('Venue')['Total'].idxmin()][['Venue', 'Player', 'Total', 'Date']]
            v_recs = venue_records[venue_records['Venue'].isin(selected_venues)]
            cols = st.columns(min(len(v_recs), 4))
            for idx, row in enumerate(v_recs.itertuples()):
                cols[idx % len(cols)].metric(row.Venue, f"{row.Total} pts", f"By {row.Player}")

            st.divider()

            st.subheader("📈 Performance Trends")
            if not filtered_df.empty:
                chart_data = filtered_df.sort_values('Date')
                st.line_chart(chart_data, x='Date', y='Total', color='Player', use_container_width=True)
                st.caption("Lower scores are better. Use the sidebar to isolate specific players.")
            else:
                st.warning("Adjust filters to view trend data.")

            with st.expander("⚔️ Head-to-Head Win Matrix", expanded=False):
                matrix_data = []
                for p1 in all_players:
                    row = {'Player': p1}
                    for p2 in all_players:
                        if p1 == p2:
                            row[p2] = "-"
                        else:
                            m1 = df[df['Player'] == p1]['Match_ID']
                            m2 = df[df['Player'] == p2]['Match_ID']
                            common_matches = set(m1).intersection(set(m2))
                            p1_wins = df[(df['Match_ID'].isin(common_matches)) & (df['Player'] == p1) & (df['Is_Winner'])].shape[0]
                            row[p2] = p1_wins
                    matrix_data.append(row)
                st.dataframe(pd.DataFrame(matrix_data).set_index('Player'), use_container_width=True)

            st.subheader("🎯 Achievement Tracking")
            all_hole_data = []
            for _, row in filtered_df.iterrows():
                for h_idx, score in enumerate(row['Hole_Scores']):
                    all_hole_data.append({
                        'Player': row['Player'],
                        'Hole': h_idx + 1,
                        'Score': score,
                        'Is_Ace': 1 if score == 1 else 0,
                        'Is_Bogey': 1 if score >= 5 else 0
                    })
            h_df = pd.DataFrame(all_hole_data)

            if not h_df.empty:
                c1, c2, c3 = st.columns(3)
                with c1:
                    ace_stats = h_df.groupby('Player')['Is_Ace'].sum().sort_values(ascending=False)
                    st.write("**🏆 Total Aces**")
                    st.dataframe(ace_stats, use_container_width=True)
                with c2:
                    bogey_stats = h_df.groupby('Player')['Is_Bogey'].sum().sort_values(ascending=False)
                    st.write("**💀 Total Bogeys**")
                    st.dataframe(bogey_stats, use_container_width=True)
                with c3:
                    nemesis = h_df.groupby(['Player', 'Hole'])['Score'].mean().reset_index()
                    worst_holes = nemesis.loc[nemesis.groupby('Player')['Score'].idxmax()]
                    st.write("**👹 Nemesis Hole**")
                    st.dataframe(worst_holes[['Player', 'Hole', 'Score']].rename(columns={'Score': 'Avg'}), hide_index=True)

            st.divider()
            st.subheader("📜 Detailed Match History")
            history_df = filtered_df[['Date', 'Venue', 'Player', 'Total', 'Opponents']].sort_values('Date', ascending=False)
            st.dataframe(history_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error generating stats: {e}")
    
    elif stats_type == "Cricket KO":  # Cricket KO stats
        st.title("🥊 Cricket KO Analytics")
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        try:
            df = conn.read(worksheet="Cricket_Matches", ttl="1m")
            
            if df.empty:
                st.info("No Cricket KO match history found. Play some matches and save them to see stats!")
            else:
                # Convert data types
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                df['Total_Marks'] = pd.to_numeric(df['Total_Marks'])
                df['Total_Darts'] = pd.to_numeric(df['Total_Darts'])
                df['Marks_Per_Dart'] = pd.to_numeric(df['Marks_Per_Dart'])
                df['Accuracy_Pct'] = pd.to_numeric(df['Accuracy_Pct'])
                df['KO_Hits_Given'] = pd.to_numeric(df['KO_Hits_Given'])
                df['KO_Hits_Received'] = pd.to_numeric(df['KO_Hits_Received'])
                df['PIN_Attempts'] = pd.to_numeric(df['PIN_Attempts'])
                df['Won_Match'] = df['Won_Match'].astype(bool)
                df['Was_Eliminated'] = df['Was_Eliminated'].astype(bool)
                
                # Sidebar filters with Select All / Clear All
                st.sidebar.header("Filter Statistics")
                all_players = sorted(df['Player'].unique())
                all_venues = sorted(df['Venue'].unique())
                all_modes = sorted(df['Game_Mode'].unique())
                
                # Initialize session state for filters if not exists
                if 'cricket_selected_players' not in st.session_state:
                    st.session_state.cricket_selected_players = all_players
                if 'cricket_selected_venues' not in st.session_state:
                    st.session_state.cricket_selected_venues = all_venues
                if 'cricket_selected_modes' not in st.session_state:
                    st.session_state.cricket_selected_modes = all_modes
                
                # Players filter
                selected_players = st.sidebar.multiselect(
                    "Players", 
                    all_players, 
                    default=st.session_state.cricket_selected_players
                )
                st.session_state.cricket_selected_players = selected_players
                
                col_p1, col_p2 = st.sidebar.columns(2)
                with col_p1:
                    if st.button("Select All", key="select_all_players"):
                        st.session_state.cricket_selected_players = all_players
                with col_p2:
                    if st.button("Clear", key="clear_players"):
                        st.session_state.cricket_selected_players = []
                
                # Venues filter
                selected_venues = st.sidebar.multiselect(
                    "Venues", 
                    all_venues, 
                    default=st.session_state.cricket_selected_venues
                )
                st.session_state.cricket_selected_venues = selected_venues
                
                col_v1, col_v2 = st.sidebar.columns(2)
                with col_v1:
                    if st.button("Select All", key="select_all_venues"):
                        st.session_state.cricket_selected_venues = all_venues
                with col_v2:
                    if st.button("Clear", key="clear_venues"):
                        st.session_state.cricket_selected_venues = []
                
                # Game Modes filter
                selected_modes = st.sidebar.multiselect(
                    "Game Modes", 
                    all_modes, 
                    default=st.session_state.cricket_selected_modes
                )
                st.session_state.cricket_selected_modes = selected_modes
                
                col_m1, col_m2 = st.sidebar.columns(2)
                with col_m1:
                    if st.button("Select All", key="select_all_modes"):
                        st.session_state.cricket_selected_modes = all_modes
                with col_m2:
                    if st.button("Clear", key="clear_modes"):
                        st.session_state.cricket_selected_modes = []
                
                # Filter dataframe
                filtered_df = df[
                    (df['Player'].isin(selected_players)) &
                    (df['Venue'].isin(selected_venues)) &
                    (df['Game_Mode'].isin(selected_modes))
                ]
                
                if filtered_df.empty:
                    st.warning("No matches found with selected filters.")
                else:
                    # Calculate top player stats from ALL data (not filtered)
                    player_full_stats = df.groupby('Player').agg({
                        'Match_ID': 'nunique',
                        'Won_Match': 'sum',
                        'Marks_Per_Dart': 'mean',
                        'Accuracy_Pct': 'mean'
                    }).round(2)
                    
                    player_full_stats['Win_Rate'] = ((player_full_stats['Won_Match'] / player_full_stats['Match_ID']) * 100).round(1)
                    
                    # Calculate win streaks
                    def calculate_win_streak(player_name):
                        player_df = df[df['Player'] == player_name].sort_values('Date')
                        max_streak = 0
                        current_streak = 0
                        for won in player_df['Won_Match']:
                            if won:
                                current_streak += 1
                                max_streak = max(max_streak, current_streak)
                            else:
                                current_streak = 0
                        return max_streak
                    
                    # Top Player Metrics
                    st.header("🏆 Top Player Stats")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        top_win_rate_player = player_full_stats['Win_Rate'].idxmax()
                        top_win_rate = player_full_stats.loc[top_win_rate_player, 'Win_Rate']
                        st.metric("Best Win Rate", f"{top_win_rate:.1f}%", f"{top_win_rate_player}")
                    
                    with col2:
                        most_wins_player = player_full_stats['Won_Match'].idxmax()
                        most_wins = int(player_full_stats.loc[most_wins_player, 'Won_Match'])
                        st.metric("Most Wins", f"{most_wins}", f"{most_wins_player}")
                    
                    with col3:
                        best_mpd_player = player_full_stats['Marks_Per_Dart'].idxmax()
                        best_mpd = player_full_stats.loc[best_mpd_player, 'Marks_Per_Dart']
                        st.metric("Best MPD", f"{best_mpd:.2f}", f"{best_mpd_player}")
                    
                    with col4:
                        best_acc_player = player_full_stats['Accuracy_Pct'].idxmax()
                        best_acc = player_full_stats.loc[best_acc_player, 'Accuracy_Pct']
                        st.metric("Best Accuracy", f"{best_acc:.1f}%", f"{best_acc_player}")
                    
                    with col5:
                        # Calculate win streaks for all players
                        streaks = {player: calculate_win_streak(player) for player in df['Player'].unique()}
                        best_streak_player = max(streaks, key=streaks.get)
                        best_streak = streaks[best_streak_player]
                        st.metric("Best Streak", f"{best_streak}", f"{best_streak_player}")
                    
                    st.divider()
                    
                    # Overview metrics (filtered data)
                    st.header("📈 Filtered Overview")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_matches = filtered_df['Match_ID'].nunique()
                        st.metric("Total Matches", total_matches)
                    
                    with col2:
                        total_games = len(filtered_df)
                        st.metric("Total Games Played", total_games)
                    
                    with col3:
                        wins = filtered_df['Won_Match'].sum()
                        win_pct = (wins / total_games * 100) if total_games > 0 else 0
                        st.metric("Win Rate", f"{win_pct:.1f}%")
                    
                    with col4:
                        avg_mpd = filtered_df['Marks_Per_Dart'].mean()
                        st.metric("Avg MPD", f"{avg_mpd:.2f}")
                    
                    # Player Performance
                    st.header("🎯 Player Performance")
                    player_stats = filtered_df.groupby('Player').agg({
                        'Match_ID': 'nunique',
                        'Won_Match': 'sum',
                        'Marks_Per_Dart': 'mean',
                        'Accuracy_Pct': 'mean',
                        'KO_Hits_Given': 'sum',
                        'KO_Hits_Received': 'sum',
                        'Was_Eliminated': 'sum',
                        'PIN_Attempts': 'sum',
                        'Darts_To_Close': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else None
                    }).round(2)
                    
                    player_stats.columns = ['Matches', 'Wins', 'Avg MPD', 'Avg Accuracy %', 
                                           'KO Hits Given', 'KO Hits Taken', 'Times Eliminated', 
                                           'PIN Attempts', 'Avg Darts to Close']
                    player_stats['Win Rate %'] = ((player_stats['Wins'] / player_stats['Matches']) * 100).round(1)
                    player_stats['KO Ratio'] = (player_stats['KO Hits Given'] / (player_stats['KO Hits Taken'] + 1)).round(2)
                    
                    # Reorder columns
                    player_stats = player_stats[['Matches', 'Wins', 'Win Rate %', 'Avg MPD', 
                                                'Avg Accuracy %', 'Avg Darts to Close', 'KO Hits Given', 
                                                'KO Hits Taken', 'KO Ratio', 'Times Eliminated', 'PIN Attempts']]
                    
                    st.dataframe(player_stats, use_container_width=True)
                    
                    # Performance Trends Over Time (by game number)
                    st.header("📈 Performance Trends Over Time")
                    
                    # Add game number to filtered data
                    trend_df = filtered_df.copy()
                    trend_df = trend_df.sort_values(['Player', 'Date'])
                    trend_df['Game_Number'] = trend_df.groupby('Player').cumcount() + 1
                    
                    # Only show graphs if there's data
                    if len(trend_df) > 0:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.subheader("MPD Over Time")
                            import altair as alt
                            mpd_chart = alt.Chart(trend_df).mark_line(point=True).encode(
                                x=alt.X('Game_Number:Q', title='Game Number'),
                                y=alt.Y('Marks_Per_Dart:Q', title='Marks Per Dart'),
                                color='Player:N',
                                tooltip=['Player', 'Game_Number', 'Marks_Per_Dart', 'Date']
                            ).properties(height=300)
                            st.altair_chart(mpd_chart, use_container_width=True)
                        
                        with col2:
                            st.subheader("Accuracy Over Time")
                            acc_chart = alt.Chart(trend_df).mark_line(point=True).encode(
                                x=alt.X('Game_Number:Q', title='Game Number'),
                                y=alt.Y('Accuracy_Pct:Q', title='Accuracy %'),
                                color='Player:N',
                                tooltip=['Player', 'Game_Number', 'Accuracy_Pct', 'Date']
                            ).properties(height=300)
                            st.altair_chart(acc_chart, use_container_width=True)
                        
                        with col3:
                            st.subheader("KO Hits Over Time")
                            ko_chart = alt.Chart(trend_df).mark_line(point=True).encode(
                                x=alt.X('Game_Number:Q', title='Game Number'),
                                y=alt.Y('KO_Hits_Given:Q', title='KO Hits Given'),
                                color='Player:N',
                                tooltip=['Player', 'Game_Number', 'KO_Hits_Given', 'Date']
                            ).properties(height=300)
                            st.altair_chart(ko_chart, use_container_width=True)
                        
                        st.caption("📊 Hover over points to see details. Use filters to compare specific players.")
                    
                    st.divider()
                    
                    # Game Mode Breakdown
                    st.header("🎮 Performance by Game Mode")
                    mode_stats = filtered_df.groupby(['Player', 'Game_Mode']).agg({
                        'Match_ID': 'count',
                        'Won_Match': 'sum',
                        'Marks_Per_Dart': 'mean'
                    }).round(2)
                    mode_stats.columns = ['Games', 'Wins', 'Avg MPD']
                    mode_stats['Win Rate %'] = ((mode_stats['Wins'] / mode_stats['Games']) * 100).round(1)
                    st.dataframe(mode_stats, use_container_width=True)
                    
                    # Head to Head
                    st.header("⚔️ Head-to-Head Records")
                    
                    # Create matchup records
                    h2h_data = []
                    for match_id in filtered_df['Match_ID'].unique():
                        match_df = filtered_df[filtered_df['Match_ID'] == match_id]
                        winner = match_df[match_df['Won_Match'] == True]['Player'].values
                        if len(winner) > 0:
                            winner = winner[0]
                            for _, row in match_df.iterrows():
                                if row['Player'] != winner:
                                    h2h_data.append({
                                        'Winner': winner,
                                        'Loser': row['Player'],
                                        'Mode': row['Game_Mode']
                                    })
                    
                    if h2h_data:
                        h2h_df = pd.DataFrame(h2h_data)
                        h2h_summary = h2h_df.groupby(['Winner', 'Loser']).size().reset_index(name='Wins')
                        h2h_summary = h2h_summary.sort_values('Wins', ascending=False)
                        st.dataframe(h2h_summary, use_container_width=True, hide_index=True)
                    else:
                        st.info("Not enough data for head-to-head records.")
                    
                    # Recent Matches
                    st.header("📜 Match History")
                    history_df = filtered_df[['Date', 'Venue', 'Game_Mode', 'Player', 'Placement', 
                                             'Total_Marks', 'Marks_Per_Dart', 'KO_Hits_Given', 
                                             'Won_Match']].sort_values('Date', ascending=False)
                    history_df['Won_Match'] = history_df['Won_Match'].map({True: '✅', False: '❌'})
                    history_df.columns = ['Date', 'Venue', 'Mode', 'Player', 'Place', 'Marks', 'MPD', 'KOs', 'Won']
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error loading Cricket stats: {e}")

# --- PAGE 3: KO CRICKET ---
elif page == "KO Cricket":
    
    if 'cricket_game' not in st.session_state:
        st.session_state.cricket_game = None
        st.session_state.current_multiplier = 1
        st.session_state.game_history = []
    
    with st.sidebar:
        st.header("⚙️ Cricket KO Setup")
        
        # Game mode selection
        game_mode = st.selectbox(
            "Game Mode",
            ["Singles Match (1v1)", "Tag Team (2v2)", "Triple Threat (1v1v1)", "Fatal 4 Way (1v1v1v1)"],
            key="cricket_mode"
        )
        
        # Venue selection with save
        venues = get_venues()
        cricket_venue_sel = st.selectbox("Venue", venues, key="cricket_venue_select")
        if cricket_venue_sel == "Custom":
            cricket_venue = st.text_input("Custom Venue Name", "Home", key="cricket_venue_custom")
            if st.button(f"💾 Save '{cricket_venue}'", key="cricket_save_venue"):
                save_venue(cricket_venue)
                st.rerun()
        else:
            cricket_venue = cricket_venue_sel
        
        # Determine number of players based on mode
        if "Singles" in game_mode:
            num_cricket_players = 2
        elif "Tag Team" in game_mode:
            num_cricket_players = 4
        elif "Triple Threat" in game_mode:
            num_cricket_players = 3
        else:  # Fatal 4 Way
            num_cricket_players = 4
        
        cricket_names = []
        profiles = get_profiles()
        for i in range(num_cricket_players):
            p_key = f"cricket_p{i}"
            def_idx = 0 if profiles else 0  # Default to first profile
            sel = st.selectbox(f"Player {i+1}", profiles, index=def_idx, key=p_key)
            if sel == "Guest":
                g_name = st.text_input(f"Guest {i+1} Name", f"Guest {i+1}", key=f"cricket_guest_{i}")
                cricket_names.append(g_name)
                if st.button(f"💾 Save '{g_name}'", key=f"cricket_save_{i}"):
                    save_profile(g_name)
                    st.rerun()
            else:
                cricket_names.append(sel)
        
        st.divider()
        
        if st.button("🎲 Start New Game", type="primary"):
            st.session_state.cricket_game = initialize_cricket_game(num_cricket_players, cricket_names, game_mode)
            st.session_state.cricket_game['venue'] = cricket_venue  # Store venue in game state
            st.session_state.current_multiplier = 1
            st.session_state.game_history = []
            st.rerun()
        
        if st.session_state.cricket_game:
            st.divider()
            if st.button("💾 Save Match to Sheets", type="primary"):
                save_cricket_match(st.session_state.cricket_game)
                st.session_state.cricket_game = None
                st.rerun()
            
            if st.button("🔄 Reset Game"):
                st.session_state.cricket_game = None
                st.rerun()
    
    if st.session_state.cricket_game is None:
        st.title("🎯 Cricket KO")
        st.info("👈 Set up players and click 'Start New Game' to begin!")
    
    else:
        game = st.session_state.cricket_game
        current_player = game['player_names'][game['current_player_idx']]
        player_key = f"P{game['current_player_idx'] + 1}"
        
        # Initialize camera settings in session state
        if 'cricket_camera_size_val' not in st.session_state:
            st.session_state.cricket_camera_size_val = 800
        if 'cricket_camera_scale_val' not in st.session_state:
            st.session_state.cricket_camera_scale_val = 1.0
        if 'cricket_camera_x_val' not in st.session_state:
            st.session_state.cricket_camera_x_val = 0
        if 'cricket_camera_y_val' not in st.session_state:
            st.session_state.cricket_camera_y_val = 0
        
        # Camera toggle in sidebar
        with st.sidebar:
            st.divider()
            camera_on = st.toggle("📹 Camera Feed", value=False, key="cricket_camera_toggle")
            if camera_on:
                camera_size = st.slider("Box Size", 200, 2000, value=st.session_state.cricket_camera_size_val, step=50, key="cricket_camera_size")
                st.markdown("**Camera Adjustments**")
                camera_scale = st.slider("Scale", 0.5, 3.0, value=st.session_state.cricket_camera_scale_val, step=0.1, key="cricket_camera_scale")
                camera_x = st.slider("Position X (%)", -50, 50, value=st.session_state.cricket_camera_x_val, step=1, key="cricket_camera_x")
                camera_y = st.slider("Position Y (%)", -50, 50, value=st.session_state.cricket_camera_y_val, step=1, key="cricket_camera_y")
                
                # Update session state with current slider values
                st.session_state.cricket_camera_size_val = camera_size
                st.session_state.cricket_camera_scale_val = camera_scale
                st.session_state.cricket_camera_x_val = camera_x
                st.session_state.cricket_camera_y_val = camera_y
            else:
                # Use stored values when camera is off
                camera_size = st.session_state.cricket_camera_size_val
                camera_scale = st.session_state.cricket_camera_scale_val
                camera_x = st.session_state.cricket_camera_x_val
                camera_y = st.session_state.cricket_camera_y_val
        
        # Layout: Camera (C1-4) + Game (C5-9) if camera on, otherwise Game uses full width
        if camera_on:
            import streamlit.components.v1 as components
            
            layout_cols = st.columns([4, 5])
            
            # Camera feed (left side)
            with layout_cols[0]:
                camera_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ margin: 0; padding: 0; }}
                        #camera-container {{
                            width: {camera_size}px;
                            height: {camera_size}px;
                            overflow: hidden;
                            position: relative;
                            border: 2px solid #444;
                            border-radius: 10px;
                            background: black;
                        }}
                        #video {{
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            width: auto;
                            height: auto;
                            min-width: 100%;
                            min-height: 100%;
                            transform: translate(calc(-50% + {camera_x}%), calc(-50% + {camera_y}%)) scale({camera_scale});
                            object-fit: cover;
                        }}
                    </style>
                </head>
                <body>
                    <div id="camera-container">
                        <video id="video" autoplay playsinline></video>
                    </div>
                    <script>
                        navigator.mediaDevices.getUserMedia({{ 
                            video: {{ 
                                facingMode: 'environment',
                                width: {{ ideal: 1920 }},
                                height: {{ ideal: 1080 }}
                            }}, 
                            audio: false 
                        }})
                        .then(stream => {{
                            document.getElementById('video').srcObject = stream;
                        }})
                        .catch(err => {{
                            console.error('Camera error:', err);
                            document.getElementById('camera-container').innerHTML = '<p style="color: white; padding: 20px;">Camera access denied or unavailable</p>';
                        }});
                    </script>
                </body>
                </html>
                """
                components.html(camera_html, height=camera_size + 10)
            
            # Game content (right side)
            with layout_cols[1]:
                game_container = st.container()
        else:
            # No camera - use centered layout as before
            st.markdown("""
            <style>
            /* Center content horizontally */
            div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
                width: 50% !important;
                margin: 0 auto !important;
            }
            @media (max-width: 768px) {
                div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
                    width: 100% !important;
                }
            }

            /* Remove height from empty vertical blocks */
            div[data-testid="stVerticalBlock"]:empty {
                display: none !important;
            }

            /* Collapse empty space after last element */
            .element-container:last-child:empty,
            div[data-testid="stVerticalBlock"]:last-child:empty {
                display: none !important;
                height: 0 !important;
                min-height: 0 !important;
            }

            /* Make buttons fill vertical space better */
            .stButton > button {
                margin-bottom: clamp(0.5rem, 1.5vh, 2rem) !important;
            }
            </style>
            """, unsafe_allow_html=True)
            game_container = st.container()
        
        # No title needed - cleaner interface
        
        with game_container:
            # Player headers and dart counter - 9 column layout
            header_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
            
            # C1-C2: Empty
            
            # C3: Player 1 (or Team 1 Player 1 in tag team) - only for 3-4 players
            with header_cols[2]:
                if game['num_players'] >= 3:
                    player_idx = 0
                    p_key = f"P{player_idx + 1}"
                    is_self = player_idx == game['current_player_idx']
                    already_skipped = game['ko_skipped'][p_key]
                    at_skip_limit = game['consecutive_skips'][p_key] >= 1
                    is_eliminated = game['eliminated'][p_key]
                    
                    # Check elimination phase
                    active_players = sum(1 for p in range(game['num_players']) if not game['eliminated'][f"P{p+1}"])
                    in_elimination_phase = any(game['board_closed'].values()) and active_players > 2 and not game['is_tag_team']
                    current_player_key = f"P{game['current_player_idx'] + 1}"
                    current_player_board_closed = game['board_closed'].get(current_player_key, False)
                    
                    # Display header HTML
                    st.markdown(get_player_header_html(game, player_idx), unsafe_allow_html=True)
                    
                    # Clickable KO button
                    if st.button(f"💀 KO", disabled=(is_self or is_eliminated or (already_skipped and not in_elimination_phase) or (at_skip_limit and not in_elimination_phase)), use_container_width=True, key=f"ko_header_{player_idx}"):
                        # Track stats
                        game['total_darts'][current_player_key] += 1
                        game['ko_hits_given'][current_player_key] += 1
                        game['ko_hits_received'][p_key] += 1
                        
                        if in_elimination_phase and current_player_board_closed:
                            game['ko_elimination_progress'][p_key] += 1
                            game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                            game['marks_per_dart'][game['dart_count']] = 0
                            game['dart_count'] += 1
                            if game['ko_elimination_progress'][p_key] >= 3:
                                game['eliminated'][p_key] = True
                        else:
                            game['ko_skipped'][p_key] = True
                            game['consecutive_skips'][p_key] += 1
                            game['marks_per_dart'][game['dart_count']] = 0
                            game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                            game['dart_count'] += 1
                        if game['dart_count'] >= 3:
                            game['consecutive_skips'][current_player_key] = 0
                            advance_to_next_player(game)
                            game['dart_count'] = 0
                            game['marks_per_dart'] = [0, 0, 0]
                            game['dart_hits'] = ['', '', '']
                        st.session_state.current_multiplier = 1
                        st.rerun()
            
            # C4: Player 2 (or Team 1 Player 2 in tag team) - always used
            with header_cols[3]:
                player_idx = 1 if game['num_players'] >= 3 else 0
                p_key = f"P{player_idx + 1}"
                is_self = player_idx == game['current_player_idx']
                already_skipped = game['ko_skipped'][p_key]
                at_skip_limit = game['consecutive_skips'][p_key] >= 1
                is_eliminated = game['eliminated'][p_key]
                
                # Check elimination phase
                active_players = sum(1 for p in range(game['num_players']) if not game['eliminated'][f"P{p+1}"])
                in_elimination_phase = any(game['board_closed'].values()) and active_players > 2 and not game['is_tag_team']
                current_player_key = f"P{game['current_player_idx'] + 1}"
                current_player_board_closed = game['board_closed'].get(current_player_key, False)
                
                # Display header HTML
                st.markdown(get_player_header_html(game, player_idx), unsafe_allow_html=True)
                
                # Clickable KO button
                if st.button(f"💀 KO", disabled=(is_self or is_eliminated or (already_skipped and not in_elimination_phase) or (at_skip_limit and not in_elimination_phase)), use_container_width=True, key=f"ko_header_{player_idx}"):
                    # Track stats
                    game['total_darts'][current_player_key] += 1
                    game['ko_hits_given'][current_player_key] += 1
                    game['ko_hits_received'][p_key] += 1
                    
                    if in_elimination_phase and current_player_board_closed:
                        game['ko_elimination_progress'][p_key] += 1
                        game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                        game['marks_per_dart'][game['dart_count']] = 0
                        game['dart_count'] += 1
                        if game['ko_elimination_progress'][p_key] >= 3:
                            game['eliminated'][p_key] = True
                    else:
                        game['ko_skipped'][p_key] = True
                        game['consecutive_skips'][p_key] += 1
                        game['marks_per_dart'][game['dart_count']] = 0
                        game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                        game['dart_count'] += 1
                    if game['dart_count'] >= 3:
                        game['consecutive_skips'][current_player_key] = 0
                        advance_to_next_player(game)
                        game['dart_count'] = 0
                        game['marks_per_dart'] = [0, 0, 0]
                        game['dart_hits'] = ['', '', '']
                    st.session_state.current_multiplier = 1
                    st.rerun()
            
            # C5: Dart counter and pin meter (center)
            with header_cols[4]:
                dart_display = []
                for i in range(3):
                    if i < game['dart_count']:
                        hit = game['dart_hits'][i]
                        if hit:
                            dart_display.append(hit)
                        else:
                            dart_display.append("???")
                    else:
                        dart_display.append("-")
                
                # Build pin meter if any board is closed
                pin_meter_html = ""
                if any(game['board_closed'].values()):
                    pin = game['pin_count']
                    p1_dots = []
                    p2_dots = []
                    
                    # Player 1 side (positive)
                    for i in range(3, 0, -1):
                        if pin >= i:
                            p1_dots.append("●")
                        else:
                            p1_dots.append("○")
                    
                    # Player 2 side (negative)
                    for i in range(1, 4):
                        if pin <= -i:
                            p2_dots.append("●")
                        else:
                            p2_dots.append("○")
                    
                    meter = " ".join(p1_dots) + " ━ " + " ".join(p2_dots)
                    pin_meter_html = f"""<div style='margin-top: clamp(3px, 0.6vh, 12px); padding-top: clamp(3px, 0.6vh, 12px); border-top: 1px solid #333;'>
                        <div style='font-size: clamp(9px, 1.5vh, 22px); color: #888; margin-bottom: 2px; line-height: 1.3;'>PIN</div>
                        <div style='font-size: clamp(11px, 2.2vh, 32px); letter-spacing: 1px; font-weight: bold; line-height: 1.3;'>{meter}</div>
                    </div>"""

                st.markdown(f"""
                <div class='dart-counter' style='text-align: center;'>
                    <div style='font-size: clamp(10px, 1.6vh, 24px); color: #888; margin-bottom: 2px; line-height: 1.3;'>DARTS THIS TURN</div>
                    <div style='font-size: clamp(12px, 2.4vh, 36px); font-weight: bold; line-height: 1.3;'>{' | '.join(dart_display)}</div>
                    {pin_meter_html}
                </div>
                """, unsafe_allow_html=True)
            
            # C6: Player 3 (or Team 2 Player 1) - always used (at least for player 2 in 1v1)
            with header_cols[5]:
                if game['num_players'] == 2:
                    player_idx = 1
                elif game['num_players'] == 3:
                    player_idx = 2
                else:  # 4 players
                    player_idx = 2
                
                p_key = f"P{player_idx + 1}"
                is_self = player_idx == game['current_player_idx']
                already_skipped = game['ko_skipped'][p_key]
                at_skip_limit = game['consecutive_skips'][p_key] >= 1
                is_eliminated = game['eliminated'][p_key]
                
                # Check elimination phase
                active_players = sum(1 for p in range(game['num_players']) if not game['eliminated'][f"P{p+1}"])
                in_elimination_phase = any(game['board_closed'].values()) and active_players > 2 and not game['is_tag_team']
                current_player_key = f"P{game['current_player_idx'] + 1}"
                current_player_board_closed = game['board_closed'].get(current_player_key, False)
                
                # Display header HTML
                st.markdown(get_player_header_html(game, player_idx), unsafe_allow_html=True)
                
                # Clickable KO button
                if st.button(f"💀 KO", disabled=(is_self or is_eliminated or (already_skipped and not in_elimination_phase) or (at_skip_limit and not in_elimination_phase)), use_container_width=True, key=f"ko_header_{player_idx}"):
                    # Track stats
                    game['total_darts'][current_player_key] += 1
                    game['ko_hits_given'][current_player_key] += 1
                    game['ko_hits_received'][p_key] += 1
                    
                    if in_elimination_phase and current_player_board_closed:
                        game['ko_elimination_progress'][p_key] += 1
                        game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                        game['marks_per_dart'][game['dart_count']] = 0
                        game['dart_count'] += 1
                        if game['ko_elimination_progress'][p_key] >= 3:
                            game['eliminated'][p_key] = True
                    else:
                        game['ko_skipped'][p_key] = True
                        game['consecutive_skips'][p_key] += 1
                        game['marks_per_dart'][game['dart_count']] = 0
                        game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                        game['dart_count'] += 1
                    if game['dart_count'] >= 3:
                        game['consecutive_skips'][current_player_key] = 0
                        advance_to_next_player(game)
                        game['dart_count'] = 0
                        game['marks_per_dart'] = [0, 0, 0]
                        game['dart_hits'] = ['', '', '']
                    st.session_state.current_multiplier = 1
                    st.rerun()
            
            # C7: Player 4 (or Team 2 Player 2) - only for 4 players
            with header_cols[6]:
                if game['num_players'] == 4:
                    player_idx = 3
                    p_key = f"P{player_idx + 1}"
                    is_self = player_idx == game['current_player_idx']
                    already_skipped = game['ko_skipped'][p_key]
                    at_skip_limit = game['consecutive_skips'][p_key] >= 1
                    is_eliminated = game['eliminated'][p_key]
                    
                    # Check elimination phase
                    active_players = sum(1 for p in range(game['num_players']) if not game['eliminated'][f"P{p+1}"])
                    in_elimination_phase = any(game['board_closed'].values()) and active_players > 2 and not game['is_tag_team']
                    current_player_key = f"P{game['current_player_idx'] + 1}"
                    current_player_board_closed = game['board_closed'].get(current_player_key, False)
                    
                    # Display header HTML
                    st.markdown(get_player_header_html(game, player_idx), unsafe_allow_html=True)
                    
                    # Clickable KO button
                    if st.button(f"💀 KO", disabled=(is_self or is_eliminated or (already_skipped and not in_elimination_phase) or (at_skip_limit and not in_elimination_phase)), use_container_width=True, key=f"ko_header_{player_idx}"):
                        # Track stats
                        game['total_darts'][current_player_key] += 1
                        game['ko_hits_given'][current_player_key] += 1
                        game['ko_hits_received'][p_key] += 1
                        
                        if in_elimination_phase and current_player_board_closed:
                            game['ko_elimination_progress'][p_key] += 1
                            game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                            game['marks_per_dart'][game['dart_count']] = 0
                            game['dart_count'] += 1
                            if game['ko_elimination_progress'][p_key] >= 3:
                                game['eliminated'][p_key] = True
                        else:
                            game['ko_skipped'][p_key] = True
                            game['consecutive_skips'][p_key] += 1
                            game['marks_per_dart'][game['dart_count']] = 0
                            game['dart_hits'][game['dart_count']] = f"KO{game['ko_numbers'][p_key]}"
                            game['dart_count'] += 1
                        if game['dart_count'] >= 3:
                            game['consecutive_skips'][current_player_key] = 0
                            advance_to_next_player(game)
                            game['dart_count'] = 0
                            game['marks_per_dart'] = [0, 0, 0]
                            game['dart_hits'] = ['', '', '']
                        st.session_state.current_multiplier = 1
                        st.rerun()
            
            # C8-C9: Empty
            
            # Perfect turn celebration banner
            if 'perfect_turn' in st.session_state and st.session_state.perfect_turn:
                import time
                current_time = time.time()
                
                if st.session_state.perfect_turn_start is None:
                    st.session_state.perfect_turn_start = current_time
                
                elapsed = current_time - st.session_state.perfect_turn_start
                
                if elapsed < 2:  # Show for 2 seconds
                    st.markdown(f"""
                    <div style='background: #00ff88; padding: clamp(5px, 1.5vh, 20px); text-align: center; border-radius: 5px; margin: clamp(3px, 0.8vh, 12px) 0;'>
                        <h3 style='color: #000; margin: 0; font-size: clamp(13px, 2.8vh, 36px); line-height: 1.3;'>🎯 DARTS BACK! 🎯</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.1)
                    st.rerun()
                else:
                    # Clear celebration
                    del st.session_state.perfect_turn
                    del st.session_state.perfect_turn_start
                    st.rerun()
            
            # Check if game is over (someone won via pin)
            if game['game_over']:
                winner_name = game['player_names'][game['winner']]
                st.markdown(f"""
                <div style='background: #00ff88; padding: clamp(8px, 2.2vh, 35px); text-align: center; border-radius: 8px; margin: clamp(5px, 1.5vh, 25px) 0;'>
                    <h1 style='color: #000; margin: 0; font-size: clamp(18px, 5vh, 60px); line-height: 1.3;'>🏆 {winner_name} WINS! 🏆</h1>
                    <div style='color: #000; font-size: clamp(13px, 3vh, 36px); margin-top: clamp(4px, 1.2vh, 20px); line-height: 1.3;'>Victory by PIN!</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Save Match button
                if st.button("💾 Save Match to Sheets", type="primary", use_container_width=True):
                    save_cricket_match(game)
                    st.session_state.cricket_game = None
                    st.rerun()
                
                # Start New Game button
                if st.button("🎮 Start New Game", use_container_width=True):
                    st.session_state.cricket_game = None
                    st.rerun()
            
            # Check if current player skipped
            elif game['ko_skipped'][player_key]:
                # Initialize countdown if not set
                if 'skip_countdown' not in st.session_state:
                    st.session_state.skip_countdown = 3
                    st.session_state.skip_start_time = None
                
                # Use time-based countdown instead of sleep
                import time
                current_time = time.time()
                
                if st.session_state.skip_start_time is None:
                    st.session_state.skip_start_time = current_time
                
                elapsed = current_time - st.session_state.skip_start_time
                remaining = max(0, 3 - int(elapsed))
                
                st.markdown(f"""
                <div style='background: #ff4444; padding: clamp(6px, 1.5vh, 22px); text-align: center; border-radius: 5px; margin: clamp(4px, 1vh, 18px) 0;'>
                    <h2 style='color: white; margin: 0; font-size: clamp(13px, 2.8vh, 36px); line-height: 1.3;'>💀 {current_player} SKIPPED! 💀</h2>
                    <div style='color: white; font-size: clamp(12px, 2.2vh, 30px); margin-top: clamp(3px, 0.7vh, 12px); line-height: 1.3;'>{remaining}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if remaining == 0:
                    # Time's up - advance to next player
                    game['ko_skipped'][player_key] = False
                    advance_to_next_player(game)
                    game['dart_count'] = 0
                    game['marks_per_dart'] = [0, 0, 0]
                    game['dart_hits'] = ['', '', '']
                    # Clear countdown
                    del st.session_state.skip_countdown
                    del st.session_state.skip_start_time
                    st.rerun()
                else:
                    # Keep counting down
                    time.sleep(0.1)
                    st.rerun()
            
            else:
                # Cricket board - rebuild for all game modes
                for idx, num in enumerate(CRICKET_NUMBERS):
                    num_label = "B" if num == 'B' else ("T" if num == 'T' else ("D" if num == 'D' else str(num)))
                    
                    # Get marks for each position based on game mode
                    if game['is_tag_team']:
                        # Tag team: T1 in C4, T2 in C6
                        marks_c3 = ""
                        marks_c4 = get_mark_symbol(game['cricket_boards']['T1'][num])
                        marks_c6 = get_mark_symbol(game['cricket_boards']['T2'][num])
                        marks_c7 = ""
                    elif game['num_players'] == 2:
                        # Singles: P1 in C4, P2 in C6
                        marks_c3 = ""
                        marks_c4 = get_mark_symbol(game['cricket_boards']['P1'][num])
                        marks_c6 = get_mark_symbol(game['cricket_boards']['P2'][num])
                        marks_c7 = ""
                    elif game['num_players'] == 3:
                        # Triple Threat: P1 in C3, P2 in C4, P3 in C6
                        marks_c3 = get_mark_symbol(game['cricket_boards']['P1'][num])
                        marks_c4 = get_mark_symbol(game['cricket_boards']['P2'][num])
                        marks_c6 = get_mark_symbol(game['cricket_boards']['P3'][num])
                        marks_c7 = ""
                    else:  # 4 players
                        # Fatal 4 Way: P1 in C3, P2 in C4, P3 in C6, P4 in C7
                        marks_c3 = get_mark_symbol(game['cricket_boards']['P1'][num])
                        marks_c4 = get_mark_symbol(game['cricket_boards']['P2'][num])
                        marks_c6 = get_mark_symbol(game['cricket_boards']['P3'][num])
                        marks_c7 = get_mark_symbol(game['cricket_boards']['P4'][num])
                    
                    cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
                    
                    # C1-C2: Empty
                    
                    # C3: Marks (if applicable)
                    with cols[2]:
                        if marks_c3:
                            st.markdown(f"<div class='cricket-mark' style='text-align: center; font-size: clamp(20px, 4.5vh, 90px); height: clamp(28px, 5.5vh, 100px); display: flex; align-items: center; justify-content: center; font-weight: bold; line-height: 1;'>{marks_c3}</div>", unsafe_allow_html=True)

                    # C4: Marks (always used)
                    with cols[3]:
                        st.markdown(f"<div class='cricket-mark' style='text-align: center; font-size: clamp(20px, 4.5vh, 90px); height: clamp(28px, 5.5vh, 100px); display: flex; align-items: center; justify-content: center; font-weight: bold; line-height: 1;'>{marks_c4}</div>", unsafe_allow_html=True)
                    
                    # C5: Number button
                    with cols[4]:
                        # Determine which board to use
                        current_player_key = f"P{game['current_player_idx'] + 1}"
                        
                        if game['is_tag_team']:
                            # Tag team: P1/P2 use T1 board, P3/P4 use T2 board
                            board_key = 'T1' if game['current_player_idx'] in [0, 1] else 'T2'
                        else:
                            board_key = current_player_key
                        
                        current_player_marks = game['cricket_boards'][board_key][num]
                        is_eliminated = game['eliminated'][current_player_key]
                        
                        # Disable if: eliminated, skipped, board closed, OR this number is already closed (3+ marks)
                        current_player_disabled = (
                            is_eliminated or
                            game['ko_skipped'][current_player_key] or
                            game['board_closed'].get(board_key, False) or
                            current_player_marks >= 3
                        )

                        if st.button(num_label, key=f"num_{num}", disabled=current_player_disabled, use_container_width=True):
                            st.session_state.game_history.append(json.dumps({
                                'boards': {k: dict(v) for k, v in game['cricket_boards'].items()},
                                'dart': game['dart_count'],
                                'marks_per_dart': game['marks_per_dart'][:],
                                'player': game['current_player_idx'],
                                'skipped': dict(game['ko_skipped']),
                                'consecutive_skips': dict(game['consecutive_skips']),
                                'pin_count': game['pin_count']
                            }))
                            
                            # Track stats
                            game['total_darts'][current_player_key] += 1
                            marks_added = st.session_state.current_multiplier
                            game['total_marks'][current_player_key] += marks_added
                            
                            # Apply to correct board (team or individual)
                            # Cap marks at 3 - no extra points in Cricket KO
                            new_marks = game['cricket_boards'][board_key][num] + marks_added
                            game['cricket_boards'][board_key][num] = min(new_marks, 3)
                            game['marks_per_dart'][game['dart_count']] = marks_added
                            
                            # Record what was hit
                            num_display = "BULL" if num == 'B' else ("TRIP" if num == 'T' else ("DBL" if num == 'D' else str(num)))
                            if st.session_state.current_multiplier == 1:
                                game['dart_hits'][game['dart_count']] = num_display
                            elif st.session_state.current_multiplier == 2:
                                game['dart_hits'][game['dart_count']] = f"D{num_display}"
                            else:
                                game['dart_hits'][game['dart_count']] = f"T{num_display}"
                            
                            game['dart_count'] += 1
                            st.session_state.current_multiplier = 1
                            
                            # Reset consecutive skips - player has thrown a dart
                            game['consecutive_skips'][current_player_key] = 0
                            
                            # Check if board is closed
                            was_closed_before = game['board_closed'][board_key]
                            if check_board_closed(game['cricket_boards'][board_key]):
                                game['board_closed'][board_key] = True
                                # Track darts to close if this is the first time closing
                                if not was_closed_before and game['darts_to_close'][current_player_key] is None:
                                    game['darts_to_close'][current_player_key] = game['board_close_dart_count'][current_player_key] + 1
                            
                            # Increment board close dart counter (if not closed yet)
                            if not game['board_closed'][board_key]:
                                game['board_close_dart_count'][current_player_key] += 1
                            
                            # Check if turn is over
                            if game['dart_count'] >= 3:
                                all_darts_scored = all(m > 0 for m in game['marks_per_dart'])
                                
                                if all_darts_scored:
                                    # Trigger celebration banner
                                    st.session_state.perfect_turn = True
                                    st.session_state.perfect_turn_start = None
                                    game['dart_count'] = 0
                                    game['marks_per_dart'] = [0, 0, 0]
                                    game['dart_hits'] = ['', '', '']
                                else:
                                    advance_to_next_player(game)
                                    game['dart_count'] = 0
                                    game['marks_per_dart'] = [0, 0, 0]
                                    game['dart_hits'] = ['', '', '']
                                    game['consecutive_skips'][current_player_key] = 0
                            st.rerun()

                    # C6: Marks (always used - at least P2 in 1v1)
                    with cols[5]:
                        st.markdown(f"<div class='cricket-mark' style='text-align: center; font-size: clamp(20px, 4.5vh, 90px); height: clamp(28px, 5.5vh, 100px); display: flex; align-items: center; justify-content: center; font-weight: bold; line-height: 1;'>{marks_c6}</div>", unsafe_allow_html=True)

                    # C7: Marks (if applicable)
                    with cols[6]:
                        if marks_c7:
                            st.markdown(f"<div class='cricket-mark' style='text-align: center; font-size: clamp(20px, 4.5vh, 90px); height: clamp(28px, 5.5vh, 100px); display: flex; align-items: center; justify-content: center; font-weight: bold; line-height: 1;'>{marks_c7}</div>", unsafe_allow_html=True)
                    
                    # C8-C9: Empty
            
            # PIN button - only show when down to 2 active players (or tag team with boards closed)
            active_players = sum(1 for p in range(game['num_players']) if not game['eliminated'][f"P{p+1}"])
            show_pin = (active_players == 2 or game['is_tag_team']) and any(game['board_closed'].values())
            
            if show_pin:
                cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
                with cols[4]:
                    # Determine if PIN button should be enabled
                    current_player_key = f"P{game['current_player_idx'] + 1}"
                    pin_disabled = game['ko_skipped'][current_player_key]

                    if st.button("PIN", key="pin_button", disabled=pin_disabled, use_container_width=True):
                        # Track stats
                        game['total_darts'][current_player_key] += 1
                        game['pin_attempts'][current_player_key] += 1
                        
                        st.session_state.game_history.append(json.dumps({
                            'boards': {k: dict(v) for k, v in game['cricket_boards'].items()},
                            'dart': game['dart_count'],
                            'marks_per_dart': game['marks_per_dart'][:],
                            'player': game['current_player_idx'],
                            'skipped': dict(game['ko_skipped']),
                            'consecutive_skips': dict(game['consecutive_skips']),
                            'pin_count': game['pin_count']
                        }))
                        
                        # Determine correct board
                        if game['is_tag_team']:
                            board_key = 'T1' if game['current_player_idx'] in [0, 1] else 'T2'
                            # Map tag team players to team direction: T1 (P1+P2) = 0, T2 (P3+P4) = 1
                            team_idx = 0 if game['current_player_idx'] in [0, 1] else 1
                        else:
                            board_key = current_player_key
                            team_idx = game['current_player_idx']

                        # Update pin count
                        game['pin_count'] = update_pin_count(
                            game['pin_count'],
                            team_idx,
                            game['board_closed'][board_key]
                        )
                        
                        # Record the dart
                        game['dart_hits'][game['dart_count']] = "PIN"
                        game['marks_per_dart'][game['dart_count']] = 0  # Doesn't count toward "darts back"
                        game['dart_count'] += 1
                        st.session_state.current_multiplier = 1
                        
                        # Reset consecutive skips - player has thrown a dart
                        game['consecutive_skips'][current_player_key] = 0
                        
                        # Check for win condition
                        if abs(game['pin_count']) >= 3:
                            game['game_over'] = True
                            game['winner'] = game['current_player_idx']  # Store index, not name
                            st.rerun()
                        
                        # Check if turn is over
                        if game['dart_count'] >= 3:
                            all_darts_scored = all(m > 0 for m in game['marks_per_dart'])
                            
                            if all_darts_scored:
                                # Trigger celebration banner
                                st.session_state.perfect_turn = True
                                st.session_state.perfect_turn_start = None
                                game['dart_count'] = 0
                                game['marks_per_dart'] = [0, 0, 0]
                                game['dart_hits'] = ['', '', '']
                            else:
                                advance_to_next_player(game)
                                game['dart_count'] = 0
                                game['marks_per_dart'] = [0, 0, 0]
                                game['dart_hits'] = ['', '', '']
                                game['consecutive_skips'][current_player_key] = 0
                        st.rerun()

            # Container for bottom buttons - constrained width
            st.markdown("""
            <style>
            .bottom-buttons-container {
                max-width: 500px;
                margin: 0 auto;
            }
            @media (max-width: 768px) {
                .bottom-buttons-container {
                    max-width: 100%;
                }
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown("<div class='bottom-buttons-container'>", unsafe_allow_html=True)
            
            # Multipliers and Miss - 9 column layout
            st.markdown("""
            <style>
            /* Make primary multiplier buttons stand out with subtle glow - only for multipliers */
            div[data-testid="stHorizontalBlock"] > div:nth-child(4) button[kind="primary"],
            div[data-testid="stHorizontalBlock"] > div:nth-child(5) button[kind="primary"] {
                background-color: rgba(255, 215, 0, 0.3) !important;
                color: #FFD700 !important;
                border: 2px solid #FFD700 !important;
                box-shadow: 0 0 10px rgba(255, 215, 0, 0.3) !important;
                font-weight: bold !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Row 1: Multipliers, Miss, Next Player, Undo (shifted left by 1 for centering)
            mult_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
            
            # C3: 2x
            with mult_cols[2]:
                if st.button("2x", type="primary" if st.session_state.current_multiplier==2 else "secondary", use_container_width=True, key="mult2"):
                    st.session_state.current_multiplier = 2
                    st.rerun()
            
            # C4: 3x
            with mult_cols[3]:
                if st.button("3x", type="primary" if st.session_state.current_multiplier==3 else "secondary", use_container_width=True, key="mult3"):
                    st.session_state.current_multiplier = 3
                    st.rerun()
            
            # C5: Miss
            with mult_cols[4]:
                if st.button("Miss", use_container_width=True, key="miss"):
                    current_player_key = f"P{game['current_player_idx'] + 1}"
                    
                    # Track stats
                    game['total_darts'][current_player_key] += 1
                    if not game['board_closed'].get(f"P{game['current_player_idx'] + 1}" if not game['is_tag_team'] else ('T1' if game['current_player_idx'] < 2 else 'T2'), False):
                        game['board_close_dart_count'][current_player_key] += 1
                    
                    game['marks_per_dart'][game['dart_count']] = 0
                    game['dart_hits'][game['dart_count']] = "MISS"
                    game['dart_count'] += 1
                    st.session_state.current_multiplier = 1
                    
                    # Reset consecutive skips - player has thrown a dart
                    game['consecutive_skips'][current_player_key] = 0
                    
                    if game['dart_count'] >= 3:
                        all_darts_scored = all(m > 0 for m in game['marks_per_dart'])
                        
                        if all_darts_scored:
                            game['dart_count'] = 0
                            game['marks_per_dart'] = [0, 0, 0]
                            game['dart_hits'] = ['', '', '']
                        else:
                            player_key = f"P{game['current_player_idx'] + 1}"
                            game['consecutive_skips'][player_key] = 0
                            advance_to_next_player(game)
                            game['dart_count'] = 0
                            game['marks_per_dart'] = [0, 0, 0]
                            game['dart_hits'] = ['', '', '']
                    st.rerun()
            
            # C6: Next Player
            with mult_cols[5]:
                if st.button("Next Player", use_container_width=True, key="next_player"):
                    # Fill remaining darts with misses
                    while game['dart_count'] < 3:
                        game['marks_per_dart'][game['dart_count']] = 0
                        game['dart_hits'][game['dart_count']] = "MISS"
                        game['dart_count'] += 1
                    
                    # Move to next non-eliminated player
                    current_player_key = f"P{game['current_player_idx'] + 1}"
                    advance_to_next_player(game)
                    game['dart_count'] = 0
                    game['marks_per_dart'] = [0, 0, 0]
                    game['dart_hits'] = ['', '', '']
                    game['consecutive_skips'][current_player_key] = 0
                    st.session_state.current_multiplier = 1
                    st.rerun()
            
            # C7: Undo
            with mult_cols[6]:
                if st.button("Undo", disabled=len(st.session_state.game_history)==0, use_container_width=True, key="undo"):
                    if len(st.session_state.game_history) > 0:
                        prev = json.loads(st.session_state.game_history.pop())
                        # Properly restore the boards - convert string keys back to int where needed
                        for p_key, board in prev['boards'].items():
                            game['cricket_boards'][p_key] = {}
                            for k, v in board.items():
                                # Convert numeric string keys back to integers
                                try:
                                    key = int(k)
                                except ValueError:
                                    key = k
                                game['cricket_boards'][p_key][key] = v
                        game['dart_count'] = prev['dart']
                        game['marks_per_dart'] = prev['marks_per_dart']
                        game['current_player_idx'] = prev['player']
                        game['ko_skipped'] = prev['skipped']
                        game['consecutive_skips'] = prev['consecutive_skips']
                        if 'pin_count' in prev:
                            game['pin_count'] = prev['pin_count']
                        st.session_state.current_multiplier = 1
                        st.rerun()

# --- PAGE 4: ROYAL RUMBLE ---
elif page == "Royal Rumble":
    import time
    import base64

    # Royal Rumble specific button styling
    st.markdown("""
    <style>
    /* Royal Rumble button styling - all active buttons get cyan border, disabled get grey */
    .stButton > button {
        height: clamp(2.5rem, 5vh, 5rem) !important;
        font-size: clamp(1rem, 2vh, 2rem) !important;
        background-color: #1e2129 !important;
    }
    /* Active buttons (primary and secondary) - cyan border */
    [data-testid="stVerticalBlock"]:has(#royal-rumble-marker) .stButton > button[kind="primary"],
    [data-testid="stVerticalBlock"]:has(#royal-rumble-marker) .stButton > button[kind="secondary"] {
        background-color: #1e2129 !important;
        border: 2px solid #00d4ff !important;
        color: white !important;
        height: clamp(2.5rem, 5vh, 5rem) !important;
        font-size: clamp(1rem, 2vh, 2rem) !important;
        padding: clamp(8px, 2vh, 16px) !important;
    }
    [data-testid="stVerticalBlock"]:has(#royal-rumble-marker) .stButton > button[kind="primary"]:hover,
    [data-testid="stVerticalBlock"]:has(#royal-rumble-marker) .stButton > button[kind="secondary"]:hover {
        background-color: #2a2f3a !important;
        border-color: #00e5ff !important;
    }
    /* Disabled buttons - grey border, same height/size */
    [data-testid="stVerticalBlock"]:has(#royal-rumble-marker) .stButton > button:disabled {
        background-color: #1e2129 !important;
        border: 2px solid #444 !important;
        color: #888 !important;
        height: clamp(2.5rem, 5vh, 5rem) !important;
        font-size: clamp(1rem, 2vh, 2rem) !important;
        padding: clamp(8px, 2vh, 16px) !important;
        cursor: not-allowed !important;
    }
    </style>
    <div id="royal-rumble-marker" style="display: none;"></div>
    """, unsafe_allow_html=True)

    # Initialize session state for Royal Rumble
    if 'rumble_game' not in st.session_state:
        st.session_state.rumble_game = None

    game = st.session_state.rumble_game

    if game is None:
        # Setup Phase
        st.title("Royal Rumble Setup")
        st.markdown("**WWE-style darts battle royale! Last player standing wins!**")

        with st.sidebar:
            st.subheader("Game Settings")
            entry_interval = st.number_input("Entry Interval (seconds)", min_value=10, max_value=600, value=120, step=10)
            no_healing_delay = st.number_input("No Healing After Last Entry (seconds)", min_value=0, max_value=600, value=300, step=30)
            st.caption(f"New player every {entry_interval//60}:{entry_interval%60:02d}")
            st.caption(f"No healing after {no_healing_delay//60}:{no_healing_delay%60:02d}")

            st.divider()

            # Entrance settings
            st.subheader("Entrance Settings")
            enable_entrances = st.toggle("Enable Entrances", value=True, help="Show entrance banners and play entrance music")

            if enable_entrances:
                music_duration = st.slider("Music Duration (seconds)", min_value=15, max_value=120, value=45, step=5)
                st.caption(f"Entrance music plays for {music_duration} seconds")
            else:
                music_duration = 0
                st.caption("Banner will show for 5 seconds (no music)")

        st.divider()

        # Player Setup
        st.subheader("Player Setup (2-20 players)")
        num_players = st.slider("Number of Players", 2, 20, 6)

        players = []
        profiles = get_profiles()

        # Create columns for player input
        cols_per_row = 2
        for i in range(0, num_players, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                player_idx = i + j
                if player_idx < num_players:
                    with cols[j]:
                        st.markdown(f"**Player {player_idx + 1}**")
                        name = st.selectbox(f"Name", profiles, index=0, key=f"rumble_p{player_idx}", label_visibility="collapsed")
                        if name == "Guest":
                            name = st.text_input("Guest Name", f"Guest {player_idx + 1}", key=f"rumble_guest_{player_idx}")

                        # Music file upload (only if entrances enabled)
                        if enable_entrances:
                            music_file = st.file_uploader(f"Entrance Music (MP3)", type=['mp3', 'wav', 'ogg'], key=f"rumble_music_{player_idx}")
                        else:
                            music_file = None

                        players.append({
                            'name': name,
                            'music_file': music_file,
                            'music_data': None
                        })

        st.divider()

        if st.button("START ROYAL RUMBLE!", type="primary", use_container_width=True):
            # Assign random numbers (1-20)
            import random
            available_numbers = list(range(1, 21))
            random.shuffle(available_numbers)

            # Randomize entry order
            entry_order = list(range(num_players))
            random.shuffle(entry_order)

            # Process music files
            for idx, player in enumerate(players):
                if player['music_file'] is not None:
                    # Read and encode music file
                    music_bytes = player['music_file'].read()
                    player['music_data'] = base64.b64encode(music_bytes).decode()
                    player['music_type'] = player['music_file'].type

            # Initialize game state
            st.session_state.rumble_game = {
                'players': [
                    {
                        'name': players[entry_order[i]]['name'],
                        'number': available_numbers[i],
                        'music_data': players[entry_order[i]]['music_data'],
                        'music_type': players[entry_order[i]].get('music_type'),
                        'marks': 0,
                        'eliminated': False,
                        'entry_position': i,
                        'has_entered': i < 2,  # First 2 start immediately
                        'eliminated_by': None
                    }
                    for i in range(num_players)
                ],
                'active_player_indices': [0, 1],  # Indices into players array
                'current_turn_idx': 0,  # Index into active_player_indices
                'entry_interval': entry_interval,
                'no_healing_delay': no_healing_delay,
                'game_start_time': time.time(),
                'last_entry_time': time.time(),
                'next_entry_idx': 2,  # Next player to enter
                'no_healing_active': False,
                'no_healing_start': None,
                'game_over': False,
                'winner': None,
                'current_entry_player': None,  # For showing entry animation
                'paused': False,
                'pause_time': None,
                'total_pause_duration': 0,
                'game_history': [],  # For undo functionality
                'enable_entrances': enable_entrances,
                'music_duration': music_duration
            }
            st.rerun()

    else:
        # Active Game

        # Sidebar controls
        with st.sidebar:
            st.divider()
            if st.button("Pause" if not game.get('paused', False) else "Resume", use_container_width=True):
                if not game.get('paused', False):
                    # Pause the game
                    game['paused'] = True
                    game['pause_time'] = time.time()
                else:
                    # Resume the game
                    pause_duration = time.time() - game['pause_time']
                    game['total_pause_duration'] += pause_duration
                    game['paused'] = False
                    game['pause_time'] = None
                st.rerun()

            if st.button("Reset Game", use_container_width=True):
                st.session_state.rumble_game = None
                st.rerun()

        current_time = time.time()

        # Adjust current time if paused
        if game.get('paused', False):
            current_time = game['pause_time']

        # Account for total pause duration
        adjusted_time = current_time - game['total_pause_duration']

        # Show player entry animation
        if game['current_entry_player'] is not None:
            entering_player = game['players'][game['current_entry_player']]

            # Auto-close after 5 seconds
            import streamlit.components.v1 as components
            components.html(f"""
            <div id="entry-banner" style='background: linear-gradient(90deg, #ff0000, #ffaa00); padding: 30px; text-align: center; border-radius: 10px; margin: 20px 0;'>
                <h1 style='color: #000; margin: 0; font-size: clamp(2rem, 5vh, 3rem);'>{entering_player['name']} IS ENTERING!</h1>
                <h2 style='color: #000; margin: 10px 0; font-size: clamp(1.2rem, 3vh, 2rem);'>Number: {entering_player['number']}</h2>
            </div>
            <script>
                setTimeout(function() {{
                    window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'close_entry'}}, '*');
                }}, 5000);
            </script>
            """, height=150)

            # Play music (only if entrances are enabled and music exists)
            if game.get('enable_entrances', True) and entering_player['music_data'] is not None:
                music_duration_ms = game.get('music_duration', 45) * 1000
                audio_html = f"""
                <audio id="entrance-music" autoplay loop volume="1.0">
                    <source src="data:{entering_player['music_type']};base64,{entering_player['music_data']}" type="{entering_player['music_type']}">
                </audio>
                <script>
                    // Ensure music plays immediately and loudly
                    var audio = document.getElementById('entrance-music');
                    audio.volume = 1.0;
                    audio.play().catch(function(error) {{
                        console.log('Audio autoplay blocked:', error);
                    }});

                    // Stop after configured duration
                    setTimeout(function() {{
                        audio.pause();
                        audio.currentTime = 0;
                    }}, {music_duration_ms});
                </script>
                """
                st.markdown(audio_html, unsafe_allow_html=True)

            # Auto-close entry banner after 5 seconds
            if 'entry_banner_time' not in game:
                game['entry_banner_time'] = time.time()

            elapsed_banner_time = time.time() - game['entry_banner_time']
            if elapsed_banner_time >= 5:
                game['current_entry_player'] = None
                if 'entry_banner_time' in game:
                    del game['entry_banner_time']
                st.rerun()
            else:
                # Force refresh to check timer
                time.sleep(0.5)
                st.rerun()

        else:
            # Normal game display

            # Show winner banner at the top if game is over
            if game['game_over']:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; border-radius: 15px; margin: 30px 0;'>
                    <h1 style='color: #fff; margin: 0; font-size: clamp(2rem, 6vh, 4rem);'>{game['winner']} WINS!</h1>
                    <h2 style='color: #fff; margin: 20px 0; font-size: clamp(1.2rem, 3vh, 2rem);'>ROYAL RUMBLE CHAMPION!</h2>
                </div>
                """, unsafe_allow_html=True)

            # Live updating timers with JavaScript (no auto-reload)
            import streamlit.components.v1 as components

            # Calculate initial values
            time_until_next = game['entry_interval'] - (adjusted_time - game['last_entry_time']) if game['next_entry_idx'] < len(game['players']) else 0
            elapsed = adjusted_time - game['game_start_time']
            time_until_no_healing = game['no_healing_delay'] - (adjusted_time - game['no_healing_start']) if (game['no_healing_start'] is not None and not game['no_healing_active']) else 0

            is_paused = game.get('paused', False)
            all_players_in = game['next_entry_idx'] >= len(game['players'])
            show_healing_timer = game['no_healing_start'] is not None

            components.html(f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;700&display=swap');
            </style>
            <div id="timers" style="display: flex; justify-content: space-around; text-align: center; color: white; font-family: 'Source Sans Pro', sans-serif;">
                <div style="flex: 1;">
                    <div id="timer1-label" style="font-size: clamp(0.8rem, 1.5vh, 1.2rem); margin-bottom: 5px; color: white;">{'Healing Ends' if all_players_in and show_healing_timer else 'Next Entry'}</div>
                    <div id="timer1" style="font-size: clamp(2rem, 5vh, 4rem); font-weight: bold; color: white; font-family: 'Source Sans Pro', sans-serif;">{int(time_until_no_healing // 60) if all_players_in and show_healing_timer else int(time_until_next // 60)}:{int(time_until_no_healing % 60) if all_players_in and show_healing_timer else int(time_until_next % 60):02d}</div>
                </div>
                <div style="flex: 1;">
                    <div style="font-size: clamp(0.8rem, 1.5vh, 1.2rem); margin-bottom: 5px; color: white;">Time</div>
                    <div id="timer2" style="font-size: clamp(2rem, 5vh, 4rem); font-weight: bold; color: white; font-family: 'Source Sans Pro', sans-serif;">{int(elapsed // 60)}:{int(elapsed % 60):02d}</div>
                </div>
            </div>
            <script>
                let nextEntry = {time_until_next};
                let gameTime = {elapsed};
                let healingEnds = {time_until_no_healing};
                let isPaused = {str(is_paused).lower()};
                let allPlayersIn = {str(all_players_in).lower()};
                let noHealingActive = {str(game.get('no_healing_active', False)).lower()};
                let showHealingTimer = {str(show_healing_timer).lower()};

                setInterval(function() {{
                    if (!isPaused) {{
                        // Update Timer 1 (Next Entry or Healing Ends)
                        if (allPlayersIn && showHealingTimer) {{
                            // Show Healing Ends timer
                            if (!noHealingActive && healingEnds > 0) {{
                                healingEnds--;
                                let mins = Math.floor(healingEnds / 60);
                                let secs = Math.floor(healingEnds % 60);
                                document.getElementById('timer1').innerText = mins + ':' + (secs < 10 ? '0' : '') + secs;
                                document.getElementById('timer1').style.color = 'white';
                                document.getElementById('timer1').style.fontSize = 'clamp(2rem, 5vh, 4rem)';
                                // Timer hit zero - events will trigger on next button press
                            }} else if (noHealingActive) {{
                                document.getElementById('timer1-label').innerText = 'No Healing';
                                document.getElementById('timer1').innerText = 'ACTIVE';
                                document.getElementById('timer1').style.color = '#ff0000';
                                document.getElementById('timer1').style.fontSize = 'clamp(1.5rem, 4vh, 3rem)';
                            }}
                        }} else if (!allPlayersIn) {{
                            // Show Next Entry timer
                            if (nextEntry > 0) {{
                                nextEntry--;
                                let mins = Math.floor(nextEntry / 60);
                                let secs = Math.floor(nextEntry % 60);
                                document.getElementById('timer1').innerText = mins + ':' + (secs < 10 ? '0' : '') + secs;
                            }} else {{
                                // Timer at zero, show 0:00
                                document.getElementById('timer1').innerText = '0:00';
                            }}
                        }} else {{
                            // All players in, waiting for healing timer to start
                            document.getElementById('timer1-label').innerText = 'All Players In';
                            document.getElementById('timer1').innerText = '--:--';
                        }}

                        // Update Timer 2 (Game Time)
                        gameTime++;
                        let mins2 = Math.floor(gameTime / 60);
                        let secs2 = Math.floor(gameTime % 60);
                        document.getElementById('timer2').innerText = mins2 + ':' + (secs2 < 10 ? '0' : '') + secs2;
                    }}
                }}, 1000);
            </script>
            """, height=80)

            st.divider()

            current_player_game_idx = game['active_player_indices'][game['current_turn_idx']] if game['active_player_indices'] else None

            # All Players Display - 2 columns (compact header) - shows active and eliminated
            st.markdown("<h3 style='font-size: clamp(1rem, 2vh, 1.5rem); margin-bottom: 5px;'>Players</h3>", unsafe_allow_html=True)

            # Display all players in turn order (active_player_indices order), then eliminated
            player_cols = st.columns(2)

            # Build display order: active players in turn order, then eliminated players
            display_order = []

            # First, add all active players in their turn order
            for player_idx in game['active_player_indices']:
                if game['players'][player_idx]['has_entered'] and not game['players'][player_idx]['eliminated']:
                    display_order.append(player_idx)

            # Then add eliminated players (in entry order)
            for i, player in enumerate(game['players']):
                if player['has_entered'] and player['eliminated']:
                    display_order.append(i)

            for idx, i in enumerate(display_order):
                player = game['players'][i]
                if player['has_entered']:  # Only show players who have entered
                    is_current = (i == current_player_game_idx)
                    is_eliminated = player['eliminated']
                    arrow = "➡️ " if is_current else ""

                    if is_eliminated:
                        # Grey out eliminated players
                        border = "border-left: 5px solid #555;"
                        opacity = "opacity: 0.4;"
                        bar_color = "#666"
                    else:
                        border = "border-left: 5px solid #ffaa00;" if is_current else "border-left: 5px solid transparent;"
                        opacity = ""
                        # Progress bar
                        progress_pct = (player['marks'] / 10) * 100
                        bar_color = "#00ff00" if player['marks'] < 5 else ("#ffaa00" if player['marks'] < 8 else "#ff0000")

                    progress_pct = (player['marks'] / 10) * 100

                    with player_cols[idx % 2]:
                        st.markdown(f"""
                        <div style='{border} background: rgba(255,255,255,0.05); padding: 6px 8px; margin: 2px 0; border-radius: 6px; {opacity}'>
                            <div style='font-size: clamp(0.85rem, 1.8vh, 1.3rem); font-weight: bold;'>{arrow}{player['name']} (#{player['number']}){' - ELIMINATED' if is_eliminated else ''}</div>
                            <div style='background: #333; border-radius: 8px; height: clamp(16px, 2.5vh, 24px); margin-top: 4px; position: relative;'>
                                <div style='background: {bar_color}; width: {progress_pct}%; height: 100%; border-radius: 8px; transition: width 0.3s;'></div>
                                <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-weight: bold; font-size: clamp(0.65rem, 1.2vh, 0.9rem);'>{player['marks']}/10</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # Number Pad for Scoring
            st.markdown(f"<h3 style='font-size: clamp(1rem, 2vh, 1.5rem); margin: 10px 0 5px 0;'>➡️ {game['players'][current_player_game_idx]['name']}'s Turn</h3>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: clamp(0.7rem, 1.3vh, 0.9rem); opacity: 0.7; margin-bottom: 8px;'>Click a number that was hit</p>", unsafe_allow_html=True)

            # Create number pad (1-20) in a 4x5 grid
            nums_per_row = 5
            for row in range(4):
                cols = st.columns(nums_per_row)
                for col_idx in range(nums_per_row):
                    num = row * nums_per_row + col_idx + 1
                    if num <= 20:
                        with cols[col_idx]:
                            # Check if this number belongs to an active player
                            number_owner = None
                            for i in game['active_player_indices']:
                                if game['players'][i]['number'] == num and not game['players'][i]['eliminated']:
                                    number_owner = i
                                    break

                            disabled = (number_owner is None)

                            # All numbers are buttons, disabled ones just can't be clicked
                            button_type = "primary" if (not disabled and number_owner == current_player_game_idx) else "secondary"
                            button_clicked = st.button(str(num), use_container_width=True, key=f"num_{num}", type=button_type, disabled=disabled)

                            if button_clicked and not disabled:
                                # Save state for undo
                                import copy
                                game['game_history'].append(copy.deepcopy({
                                    'players': game['players'],
                                    'active_player_indices': game['active_player_indices'],
                                    'current_turn_idx': game['current_turn_idx']
                                }))

                                # Hit this number
                                target_player = game['players'][number_owner]
                                current_player = game['players'][current_player_game_idx]

                                if number_owner == current_player_game_idx:
                                    # Hit own number - can only heal if not in no-healing phase
                                    if not game['no_healing_active']:
                                        target_player['marks'] = max(0, target_player['marks'] - 1)
                                else:
                                    # Hit opponent - give them a mark
                                    target_player['marks'] += 1

                                    # Check for elimination
                                    if target_player['marks'] >= 10:
                                        target_player['eliminated'] = True
                                        target_player['eliminated_by'] = current_player['name']

                                        # Remove from active players
                                        game['active_player_indices'].remove(number_owner)

                                        # Adjust current_turn_idx if needed
                                        if game['current_turn_idx'] >= len(game['active_player_indices']):
                                            game['current_turn_idx'] = 0

                                        # Check for winner (only if all players have entered)
                                        all_players_entered = game['next_entry_idx'] >= len(game['players'])
                                        if len(game['active_player_indices']) == 1 and all_players_entered:
                                            game['game_over'] = True
                                            game['winner'] = game['players'][game['active_player_indices'][0]]['name']

                                st.rerun()

            # Control Buttons - Undo and Next Player
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Undo", use_container_width=True, disabled=len(game['game_history']) == 0):
                    if game['game_history']:
                        # Restore previous state
                        prev_state = game['game_history'].pop()
                        game['players'] = prev_state['players']
                        game['active_player_indices'] = prev_state['active_player_indices']
                        game['current_turn_idx'] = prev_state['current_turn_idx']
                        st.rerun()
            with col2:
                if st.button("Next Player", use_container_width=True):
                    # Check if it's time for a new player to enter
                    current_time = time.time()
                    adjusted_time = current_time - game['total_pause_duration']

                    if not game.get('paused', False) and game['next_entry_idx'] < len(game['players']) and game.get('current_entry_player') is None:
                        time_since_last_entry = adjusted_time - game['last_entry_time']
                        if time_since_last_entry >= game['entry_interval']:
                            # Timer hit zero - new player enters!
                            new_player_idx = game['next_entry_idx']

                            # Insert the new player right after the current player in active_player_indices
                            insert_position = game['current_turn_idx'] + 1
                            game['active_player_indices'].insert(insert_position, new_player_idx)

                            # Mark player as entered
                            game['players'][new_player_idx]['has_entered'] = True

                            game['last_entry_time'] = adjusted_time
                            game['next_entry_idx'] += 1
                            game['current_entry_player'] = new_player_idx

                            # Make the new player the current turn (they go immediately)
                            game['current_turn_idx'] = insert_position

                            # Check if this was the last player
                            if game['next_entry_idx'] >= len(game['players']):
                                game['no_healing_start'] = adjusted_time

                            st.rerun()

                    # Check if no-healing should activate (timer hit zero and Next Player pressed)
                    if not game.get('paused', False) and game['no_healing_start'] is not None and not game['no_healing_active']:
                        time_since_no_healing_start = adjusted_time - game['no_healing_start']
                        if time_since_no_healing_start >= game['no_healing_delay']:
                            game['no_healing_active'] = True

                    # Advance to next player (only if no entry happened)
                    game['current_turn_idx'] = (game['current_turn_idx'] + 1) % len(game['active_player_indices'])
                    st.rerun()


# --- PAGE 5: MANAGE PROFILES ---
elif page == "Manage Profiles":
    st.title("Manage Profiles")
    st.markdown("Add or delete player profiles. Profiles are used for quick selection in Golf and Cricket games.")

    st.divider()

    # Get current profiles
    profiles = get_profiles()

    # Add Profile Section
    st.subheader("Add New Profile")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_profile_name = st.text_input("Profile Name", key="new_profile_input", placeholder="Enter player name")
    with col2:
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
        if st.button("Save Profile", use_container_width=True, type="primary"):
            if new_profile_name.strip():
                if new_profile_name.strip() in profiles:
                    st.error(f"Profile '{new_profile_name}' already exists!")
                else:
                    save_profile(new_profile_name.strip())
                    st.success(f"Profile '{new_profile_name}' saved!")
                    st.rerun()
            else:
                st.error("Please enter a profile name")

    st.divider()

    # Delete Profile Section
    st.subheader("Delete Profiles")

    if len(profiles) > 1 or (len(profiles) == 1 and profiles[0] != "Guest"):
        # Show profiles as cards with delete buttons
        cols_per_row = 3
        profile_list = [p for p in profiles if p != "Guest"]  # Don't show Guest in delete list

        if profile_list:
            for i in range(0, len(profile_list), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, profile in enumerate(profile_list[i:i+cols_per_row]):
                    with cols[j]:
                        st.markdown(f"""
                        <div style='background: rgba(255,255,255,0.05); border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 10px;'>
                            <div style='font-size: 24px; font-weight: bold; margin-bottom: 10px;'>{profile}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Delete", key=f"delete_{profile}", use_container_width=True):
                            delete_profile(profile)
                            st.success(f"Deleted '{profile}'")
                            st.rerun()
        else:
            st.info("No custom profiles to delete. Only 'Guest' exists as a fallback.")
    else:
        st.info("No profiles to delete. Add some profiles first!")

    st.divider()

    # Current Profiles List
    st.subheader("Current Profiles")
    if profiles:
        st.markdown(f"**{len(profiles)} profile(s):** {', '.join(profiles)}")
    else:
        st.info("No profiles saved yet")
