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
    page_title="Dart Golf Pro", 
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

        /* 5. SCORECARD GRID FIX */
        [data-testid="column"] {
            background-color: #0e1117 !important;
        }

        /* 6. BIGGER BUTTONS */
        .stButton > button {
            width: 100% !important;
            height: 3.5rem !important;
            background-color: #1e2129 !important;
            border: 2px solid #00d4ff !important;
            color: white !important;
        }
        
        /* Cricket Board Styles */
        .cricket-board {
            background: #1a1a1a;
            border: 2px solid #00d4ff;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .cricket-row {
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 4px 0;
            background: #2a2a2a;
            border-radius: 5px;
        }
        .cricket-row.closed {
            background: #1a4d2e;
            border: 1px solid #00ff88;
        }
        .cricket-label {
            font-size: 20px;
            font-weight: bold;
            width: 80px;
        }
        .cricket-marks {
            font-size: 28px;
            margin-left: 20px;
            color: #00d4ff;
            font-family: monospace;
        }
        
        /* Pin Display */
        .pin-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
        }
        .pin-circle {
            display: inline-block;
            width: 60px;
            height: 60px;
            line-height: 60px;
            margin: 8px;
            background: #2a2a2a;
            border: 3px solid #666;
            border-radius: 50%;
            font-size: 28px;
            font-weight: bold;
        }
        .pin-circle.hit {
            background: #00ff88;
            border-color: #00ff88;
            color: #000;
        }
        
        /* KO Alert */
        .ko-display {
            background: #ff4444;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin: 15px 0;
        }
        .ko-number-badge {
            background: #ff4444;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 14px;
        }
        
        /* Turn indicator */
        .turn-banner {
            background: #00d4ff;
            color: #000;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. Updated function to hide header but KEEP sidebar toggle
def hide_header():
    st.markdown("""
        <style>
            /* Hide the background of the header but not the element itself */
            header[data-testid="stHeader"] {
                background-color: rgba(0,0,0,0);
                color: white;
            }
            
            /* Hide the decoration line */
            [data-testid="stDecoration"] {
                display: none;
            }

            /* Adjust space at the top */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 0rem;
            }

            /* Make sure the sidebar 'arrow' button is visible */
            [data-testid="stSidebarCollapsedControl"] {
                color: white;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 5px;
            }

            /* Hide the footer */
            footer {
                visibility: hidden;
            }
        </style>
        """, unsafe_allow_html=True)

# 3. Call the updated function
hide_header()


# --- CRICKET KO FUNCTIONS ---
CRICKET_NUMBERS = [15, 16, 17, 18, 19, 20, 'D', 'T', 'B']

def get_mark_symbol(marks):
    """Convert marks to display symbol"""
    if marks == 0:
        return ""
    elif marks == 1:
        return "/"
    elif marks == 2:
        return "X"
    elif marks >= 3:
        closed = "⊚"
        if marks > 3:
            closed += f" +{marks-3}"
        return closed

def check_board_closed(board):
    """Check if all cricket numbers are closed (3+ marks)"""
    return all(marks >= 3 for marks in board.values())

def initialize_cricket_game(num_players, player_names):
    """Initialize a new Cricket KO game"""
    available = list(range(1, 21))
    random.shuffle(available)
    ko_numbers = {f"P{i+1}": available[i] for i in range(num_players)}
    
    return {
        'num_players': num_players,
        'player_names': player_names,
        'cricket_boards': {f"P{i+1}": {num: 0 for num in CRICKET_NUMBERS} for i in range(num_players)},
        'ko_numbers': ko_numbers,
        'ko_skipped': {f"P{i+1}": False for i in range(num_players)},
        'ko_skip_count': {f"P{i+1}": 0 for i in range(num_players)},
        'pin_progress': {f"P{i+1}": [] for i in range(num_players)},
        'board_closed': {f"P{i+1}": False for i in range(num_players)},
        'current_player_idx': 0,
        'dart_count': 0,
        'marks_this_turn': 0,
        'game_over': False,
        'winner': None
    }


# --- 1. GOLF SETTINGS & DATA HELPERS ---
PROFILE_FILE = "profiles.txt"
HISTORY_FILE = "golf_history_v2.csv"

def get_profiles():
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f: f.write("Brad\nGuest")
    with open(PROFILE_FILE, "r") as f:
        return sorted(list(set([l.strip() for l in f.readlines() if l.strip()])))

def save_profile(name):
    if name.strip() and name.strip() != "Guest":
        with open(PROFILE_FILE, "a") as f: f.write(f"\n{name.strip()}")

def save_match_data(match_id, player_names, player_scores, venue):
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        existing_df = conn.read(worksheet="Matches", ttl=0)
    except:
        existing_df = pd.DataFrame(columns=["Match_ID", "Date", "Venue", "Player", "Total", "Hole_Scores", "Opponents"])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_rows = []
    for i, name in enumerate(player_names):
        scores = player_scores[f"P{i+1}"]
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

# --- 2. NAVIGATION ---
st.sidebar.title("🎮 Navigation")
page = st.sidebar.radio("Go to:", ["Live Game", "Stats Dashboard", "Cricket KO"])

# --- 3. PAGE 1: LIVE GAME (GOLF) ---
if page == "Live Game":
    def inject_custom_css(width_px):
        st.markdown(f"""
            <style>
            .block-container {{ padding: 1rem 1.5rem !important; }}
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
            .stat-name {{ font-size: 14px; color: #888; text-transform: uppercase; font-weight: bold; }}
            .stat-score {{ font-size: 36px; font-weight: 900; color: white; line-height: 1; }}
            .par-under {{ color: #00ff88; font-size: 18px; font-weight: bold; }}
            .par-over {{ color: #ff4b4b; font-size: 18px; font-weight: bold; }}
            .par-even {{ color: #888; font-size: 18px; font-weight: bold; }}
            .golf-table {{ width: 100%; border-collapse: collapse; color: white; table-layout: fixed; margin-top: 20px; }}
            .golf-header {{ background-color: #1a2a4a; border: 1px solid #444; text-align: center; padding: 10px; font-weight: bold; }}
            .golf-cell {{ border: 1px solid #444; text-align: center; padding: 10px; font-size: 18px; }}
            .active-hole-head {{ background-color: #00d4ff !important; color: black !important; font-weight: 900; }}
            .stButton > button {{ height: 65px !important; font-size: 24px !important; font-weight: 900 !important; }}
            div[data-testid="stHorizontalBlock"] > div:last-child button {{ background-color: #333 !important; color: #ff4b4b !important; border: 1px solid #ff4b4b !important; }}
            </style>
        """, unsafe_allow_html=True)

    if 'player_scores' not in st.session_state:
        st.session_state.update({
            'player_scores': {f"P{i}": [None]*18 for i in range(1,5)}, 
            'current_hole': 0, 'active_idx': 0, 'game_over': False,
            'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper()
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
        use_cam = st.toggle("🎥 Show Board Camera", value=True)
        cam_size = st.slider("Camera Size (px)", 300, 1600, 800, step=50) if use_cam else 800
        num_players = st.slider("Players", 1, 4, 2)
        names = []
        profiles = get_profiles()
        for i in range(1, num_players + 1):
            p_key = f"sel_p{i}"
            def_idx = profiles.index("Brad") if (i==1 and "Brad" in profiles) else profiles.index("Guest")
            sel = st.selectbox(f"Player {i}", profiles, index=def_idx, key=p_key)
            if sel == "Guest":
                g_name = st.text_input(f"Guest {i} Name", f"Guest {i}", key=f"g_name_{i}")
                names.append(g_name)
                if st.button(f"💾 Save '{g_name}'", key=f"save_p{i}"):
                    save_profile(g_name); st.rerun()
            else: names.append(sel)
        if st.button("🔄 Reset Match"):
            st.session_state.update({'player_scores': {f"P{i}": [None]*18 for i in range(1,5)}, 'current_hole': 0, 'active_idx': 0, 'game_over': False, 'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper()})
            st.rerun()

    inject_custom_css(cam_size)
    if use_cam:
        st.camera_input("Board", key="dart_cam", label_visibility="collapsed")
        st.divider()

    cols = st.columns(num_players)
    for i in range(num_players):
        p_sc = st.session_state.player_scores[f"P{i+1}"]
        total = sum(x for x in p_sc if x is not None)
        holes_played = sum(1 for x in p_sc if x is not None)
        rel_par = total - (holes_played * 4)
        par_str = f"{rel_par:+}" if rel_par != 0 else "E"
        par_class = "par-under" if rel_par < 0 else "par-over" if rel_par > 0 else "par-even"
        active = "active" if i == st.session_state.active_idx and not st.session_state.game_over else ""
        cols[i].markdown(f"<div class='stat-card {active}'><div class='stat-name'>{names[i]}</div><div class='stat-score'>{total}</div><div class='{par_class}'>{par_str}</div></div>", unsafe_allow_html=True)

    def draw_card(start, end, label):
        html = f"<table class='golf-table'><tr><td class='golf-header' style='width:100px;'>{label}</td>"
        for h in range(start, end): 
            active_h = "active-hole-head" if h == st.session_state.current_hole and not st.session_state.game_over else ""
            html += f"<td class='golf-header {active_h}'>{h+1}</td>"
        html += "<td class='golf-header' style='background:#00d4ff; color:black;'>TOT</td></tr>"
        for i in range(num_players):
            p_s = st.session_state.player_scores[f"P{i+1}"]
            html += f"<tr><td class='golf-cell' style='text-align:left;'>{names[i]}</td>"
            for h in range(start, end): html += f"<td class='golf-cell'>{p_s[h] if p_s[h] is not None else '-'}</td>"
            html += f"<td class='golf-cell' style='font-weight:bold;'>{sum(x for x in p_s[start:end] if x is not None)}</td></tr>"
        st.markdown(html + "</table>", unsafe_allow_html=True)

    draw_card(0, 9, "OUT"); draw_card(9, 18, "IN")

    if not st.session_state.game_over:
        btn_cols = st.columns([1,1,1,1,1,1,1.5])
        def submit(val):
            st.session_state.history_stack.append({'player_scores': {k: list(v) for k, v in st.session_state.player_scores.items()}, 'current_hole': st.session_state.current_hole, 'active_idx': st.session_state.active_idx})
            st.session_state.player_scores[f"P{st.session_state.active_idx + 1}"][st.session_state.current_hole] = val
            if st.session_state.active_idx < num_players - 1: st.session_state.active_idx += 1
            elif st.session_state.current_hole < 17: st.session_state.current_hole += 1; st.session_state.active_idx = 0
            else: st.session_state.game_over = True
            st.rerun()

        for i in range(1, 7):
            if btn_cols[i-1].button(str(i), use_container_width=True): submit(i)
        if btn_cols[6].button("UNDO", use_container_width=True) and st.session_state.history_stack:
            prev = st.session_state.history_stack.pop()
            st.session_state.update({'player_scores': prev['player_scores'], 'current_hole': prev['current_hole'], 'active_idx': prev['active_idx']})
            st.rerun()
    else:
        if st.button(f"🏆 SAVE MATCH AT {final_venue.upper()}", use_container_width=True, type="primary"):
            save_match_data(st.session_state.match_id, names, st.session_state.player_scores, final_venue)
            st.session_state.update({'player_scores': {f"P{i}": [None]*18 for i in range(1,5)}, 'current_hole': 0, 'active_idx': 0, 'game_over': False, 'history_stack': [], 'match_id': str(uuid.uuid4())[:8].upper()})
            st.rerun()

# --- PAGE 2: STATS DASHBOARD ---
elif page == "Stats Dashboard":
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
            
            selected_players = st.sidebar.multiselect("Select Players", options=all_players, default=all_players)
            selected_venues = st.sidebar.multiselect("Select Venues", options=all_venues, default=all_venues)

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

# --- PAGE 3: CRICKET KO ---
else:  # page == "Cricket KO"
    
    if 'cricket_game' not in st.session_state:
        st.session_state.cricket_game = None
    
    with st.sidebar:
        st.header("⚙️ Cricket KO Setup")
        
        num_cricket_players = st.slider("Number of Players", 2, 4, 2, key="cricket_num")
        
        cricket_names = []
        profiles = get_profiles()
        for i in range(num_cricket_players):
            p_key = f"cricket_p{i}"
            def_idx = profiles.index("Brad") if (i==0 and "Brad" in profiles) else profiles.index("Guest")
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
            st.session_state.cricket_game = initialize_cricket_game(num_cricket_players, cricket_names)
            st.rerun()
        
        if st.session_state.cricket_game and st.button("🔄 Reset Game"):
            st.session_state.cricket_game = None
            st.rerun()
        
        with st.expander("📋 Rules"):
            st.markdown("""
            **Cricket Numbers:** 15-20, 3 Doubles, 3 Triples, 3 Bulls
            
            **KO:** Hit opponent's number → they skip next turn
            
            **Pin:** After closing board, hit 1→2→3 to win
            
            **Bonus:** 3 darts with 3+ marks = go again
            """)
    
    # --- GAME DISPLAY ---
    if st.session_state.cricket_game is None:
        st.title("🎯 Cricket KO")
        st.info("👈 Set up players and click 'Start New Game' to begin!")
        
        with st.expander("📖 Full Rules", expanded=True):
            st.markdown("""
            ### Cricket KO - Complete Rules
            
            #### Objective
            Close all cricket numbers (15-20 + Doubles/Triples/Bulls), then complete the Pin (1-2-3).
            
            #### Cricket Phase
            - **Numbers:** 15, 16, 17, 18, 19, 20
            - **Specials:** 3 Doubles, 3 Triples, 3 Bulls
            - Need 3 marks to close each (/, X, ⊚)
            
            #### KO System
            - Each player gets random number (1-20)
            - Hit opponent's KO → they skip next turn
            - Can't skip 2 turns in a row
            
            #### The Pin
            - After board closed: hit 1→2→3 to WIN
            - Opponent can reverse your pin
            - Must keep board closed to advance
            
            #### Bonus Turns
            - 3 darts with 3+ marks → GO AGAIN
            - KO hits and Pin numbers don't count
            """)
    
    else:
        game = st.session_state.cricket_game
        current_player = game['player_names'][game['current_player_idx']]
        player_key = f"P{game['current_player_idx'] + 1}"
        
        st.title("🎯 Cricket KO - LIVE")
        
        # --- TURN BANNER ---
        if not game['game_over']:
            if game['ko_skipped'][player_key]:
                st.markdown(f"<div class='ko-display'>💀 {current_player} is SKIPPED! 💀</div>", unsafe_allow_html=True)
                if st.button("⏭️ Next Player", use_container_width=True):
                    game['ko_skipped'][player_key] = False
                    game['ko_skip_count'][player_key] = 0
                    game['current_player_idx'] = (game['current_player_idx'] + 1) % game['num_players']
                    game['dart_count'] = 0
                    game['marks_this_turn'] = 0
                    st.rerun()
            else:
                st.markdown(f"<div class='turn-banner'>🎯 {current_player}'s Turn - Dart {game['dart_count'] + 1}/3</div>", unsafe_allow_html=True)
                st.caption(f"Marks this turn: {game['marks_this_turn']}")
        
        # --- PLAYER BOARDS ---
        cols = st.columns(game['num_players'])
        
        for i in range(game['num_players']):
            p_key = f"P{i+1}"
            with cols[i]:
                st.subheader(game['player_names'][i])
                
                # KO Number display
                ko_num = game['ko_numbers'][p_key]
                skip_badge = " 💀" if game['ko_skipped'][p_key] else ""
                st.markdown(f"<span class='ko-number-badge'>KO: {ko_num}{skip_badge}</span>", unsafe_allow_html=True)
                
                # Cricket board
                board_html = "<div class='cricket-board'>"
                for num in CRICKET_NUMBERS:
                    marks = game['cricket_boards'][p_key][num]
                    symbol = get_mark_symbol(marks)
                    closed_class = "closed" if marks >= 3 else ""
                    
                    board_html += f"""
                    <div class='cricket-row {closed_class}'>
                        <span class='cricket-label'>{num}</span>
                        <span class='cricket-marks'>{symbol}</span>
                    </div>
                    """
                board_html += "</div>"
                st.markdown(board_html, unsafe_allow_html=True)
                
                # Pin display
                if game['board_closed'][p_key] or game['pin_progress'][p_key]:
                    pin = game['pin_progress'][p_key]
                    pin_html = "<div class='pin-container'><strong>🎖️ PIN</strong><br>"
                    for num in [1, 2, 3]:
                        hit_class = "hit" if num in pin else ""
                        pin_html += f"<span class='pin-circle {hit_class}'>{num}</span>"
                    pin_html += "</div>"
                    st.markdown(pin_html, unsafe_allow_html=True)
                    
                    if pin == [1, 2, 3]:
                        st.success(f"🏆 {game['player_names'][i]} WINS!")
                        game['game_over'] = True
                        game['winner'] = game['player_names'][i]
        
        st.divider()
        
        # --- INPUT SECTION ---
        if not game['game_over'] and not game['ko_skipped'][player_key]:
            st.subheader("📝 Record Dart")
            
            # Determine available targets
            if game['board_closed'][player_key]:
                # Pin phase
                next_pin = len(game['pin_progress'][player_key]) + 1
                target_options = ["Miss"] + [str(i) for i in range(1, 4)]
                
                # Add KO options
                for j in range(game['num_players']):
                    if j != game['current_player_idx']:
                        ko_target = game['ko_numbers'][f"P{j+1}"]
                        target_options.append(f"KO: {game['player_names'][j]} ({ko_target})")
                
                st.info(f"📌 Board closed! Next pin number: **{next_pin}**")
            else:
                # Cricket phase
                target_options = ["Miss"] + [str(n) for n in CRICKET_NUMBERS]
                
                # Add KO options
                for j in range(game['num_players']):
                    if j != game['current_player_idx']:
                        ko_target = game['ko_numbers'][f"P{j+1}"]
                        target_options.append(f"KO: {game['player_names'][j]} ({ko_target})")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                dart_hit = st.selectbox("Target Hit", target_options, key=f"dart_{game['dart_count']}")
            
            with col2:
                if "KO:" not in dart_hit and dart_hit != "Miss":
                    marks = st.number_input("Marks", min_value=1, max_value=3, value=1)
                else:
                    marks = 0
            
            with col3:
                st.write("")
                st.write("")
                if st.button("✅ Record Dart", use_container_width=True):
                    # Process dart
                    if "KO:" in dart_hit:
                        # Extract player index from KO hit
                        target_name = dart_hit.split(": ")[1].split(" (")[0]
                        target_idx = game['player_names'].index(target_name)
                        target_key = f"P{target_idx + 1}"
                        
                        # Apply skip if not already skipped
                        if game['ko_skip_count'][target_key] == 0:
                            game['ko_skipped'][target_key] = True
                            game['ko_skip_count'][target_key] = 1
                            st.toast(f"💀 {target_name} will skip their next turn!")
                        else:
                            st.toast(f"⚠️ {target_name} can't be skipped again")
                    
                    elif dart_hit != "Miss":
                        if game['board_closed'][player_key]:
                            # Pin phase
                            hit_num = int(dart_hit)
                            expected_next = len(game['pin_progress'][player_key]) + 1
                            
                            if hit_num == expected_next:
                                game['pin_progress'][player_key].append(hit_num)
                                game['marks_this_turn'] += 1
                                st.toast(f"✅ Pin progress: {game['pin_progress'][player_key]}")
                                
                                # Check for win
                                if game['pin_progress'][player_key] == [1, 2, 3]:
                                    game['game_over'] = True
                                    game['winner'] = current_player
                        else:
                            # Cricket phase
                            try:
                                target = int(dart_hit) if dart_hit.isdigit() else dart_hit
                            except:
                                target = dart_hit
                            
                            if target in game['cricket_boards'][player_key]:
                                game['cricket_boards'][player_key][target] += marks
                                game['marks_this_turn'] += marks
                                
                                # Check if board just closed
                                if check_board_closed(game['cricket_boards'][player_key]):
                                    game['board_closed'][player_key] = True
                                    st.toast(f"🎉 {current_player} closed their board!")
                    
                    # Increment dart count
                    game['dart_count'] += 1
                    
                    # Check end of turn
                    if game['dart_count'] >= 3:
                        # Check for bonus turn
                        if game['marks_this_turn'] >= 3:
                            st.toast(f"🔥 BONUS TURN! {current_player} goes again!")
                            game['dart_count'] = 0
                            game['marks_this_turn'] = 0
                        else:
                            # Reset skip counters for all players
                            for pk in game['ko_skip_count']:
                                if game['ko_skip_count'][pk] > 0:
                                    game['ko_skip_count'][pk] = 0
                            
                            # Next player
                            game['current_player_idx'] = (game['current_player_idx'] + 1) % game['num_players']
                            game['dart_count'] = 0
                            game['marks_this_turn'] = 0
                    
                    st.rerun()
        
        elif game['game_over']:
            st.balloons()
            st.success(f"🏆 {game['winner']} WINS THE GAME!")
            
            if st.button("🎲 Play Again", type="primary", use_container_width=True):
                st.session_state.cricket_game = initialize_cricket_game(
                    game['num_players'],
                    game['player_names']
                )
                st.rerun()