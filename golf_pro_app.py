import streamlit as st
import os
import pandas as pd
from datetime import datetime
import json
import uuid
import plotly.express as px
from streamlit_gsheets import GSheetsConnection


# 1. This MUST be the first Streamlit command
st.set_page_config(
    page_title="Dart Golf Pro", 
    layout="wide", 
    initial_sidebar_state="auto" # 'auto' allows the sidebar to be found
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




# --- 1. SETTINGS & DATA HELPERS ---
st.set_page_config(page_title="Darts Golf Pro", layout="wide")
PROFILE_FILE = "profiles.txt"
# We keep this for backward compatibility if you still want a local copy, 
# but the app will now prioritize GSheets.
HISTORY_FILE = "golf_history_v2.csv"

def get_profiles():
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f: f.write("Brad\nGuest")
    with open(PROFILE_FILE, "r") as f:
        return sorted(list(set([l.strip() for l in f.readlines() if l.strip()])))

def save_profile(name):
    if name.strip() and name.strip() != "Guest":
        with open(PROFILE_FILE, "a") as f: f.write(f"\n{name.strip()}")

# --- GOOGLE SHEETS SAVE FUNCTION ---
def save_match_data(match_id, player_names, player_scores, venue):
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Read existing data
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
    
    # Update GSheets
    updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
    conn.update(worksheet="Matches", data=updated_df)
    st.success("✅ Match Synced to Google Sheets!")

# --- 2. NAVIGATION ---
st.sidebar.title("🎮 Navigation")
page = st.sidebar.radio("Go to:", ["Live Game", "Stats Dashboard"])

# --- 3. PAGE 1: LIVE GAME ---
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
else:
    st.title("📊 Elite Darts Golf Analytics")
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try:
        df = conn.read(worksheet="Matches", ttl="1m")
        
        if df.empty:
            st.info("No match history found in Google Sheets.")
        else:
            # Data Formatting
            df['Hole_Scores'] = df['Hole_Scores'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            df['Total'] = pd.to_numeric(df['Total'])
            df['Rank'] = df.groupby('Match_ID')['Total'].rank(method='min', ascending=True)
            df['Is_Winner'] = df['Rank'] == 1

            # --- SIDEBAR FILTERS ---
            st.sidebar.header("Filter Statistics")
            all_players = sorted(df['Player'].unique())
            all_venues = sorted(df['Venue'].unique())
            
            selected_players = st.sidebar.multiselect("Select Players", options=all_players, default=all_players)
            selected_venues = st.sidebar.multiselect("Select Venues", options=all_venues, default=all_venues)

            # Apply Filters
            filtered_df = df[(df['Player'].isin(selected_players)) & (df['Venue'].isin(selected_venues))]

            # 1. VENUE RECORDS
            st.subheader("📍 Venue Course Records")
            venue_records = df.loc[df.groupby('Venue')['Total'].idxmin()][['Venue', 'Player', 'Total', 'Date']]
            v_recs = venue_records[venue_records['Venue'].isin(selected_venues)]
            cols = st.columns(min(len(v_recs), 4))
            for idx, row in enumerate(v_recs.itertuples()):
                cols[idx % len(cols)].metric(row.Venue, f"{row.Total} pts", f"By {row.Player}")

            st.divider()

            # 2. SCORES OVER TIME (Restored Tracker)
            st.subheader("📈 Performance Trends")
            if not filtered_df.empty:
                # Prepare data for the chart: We want Date on X, Score on Y, and colored by Player
                # Sort by date so the line connects properly
                chart_data = filtered_df.sort_values('Date')
                
                st.line_chart(
                    chart_data, 
                    x='Date', 
                    y='Total', 
                    color='Player',
                    use_container_width=True
                )
                st.caption("Lower scores are better. Use the sidebar to isolate specific players.")
            else:
                st.warning("Adjust filters to view trend data.")

            # 3. PLAYER WIN MATRIX
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

            # 4. HOLE ANALYSIS
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

            # 5. MATCH HISTORY
            st.divider()
            st.subheader("📜 Detailed Match History")
            history_df = filtered_df[['Date', 'Venue', 'Player', 'Total', 'Opponents']].sort_values('Date', ascending=False)
            st.dataframe(history_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error generating stats: {e}")