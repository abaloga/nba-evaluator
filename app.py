# NBA Evaluator
# This application will evaluate NBA players against a target player/archetype

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from nba_api.stats.endpoints import (
    playercareerstats, shotchartdetail, playerprofilev2, 
    leaguedashplayerstats, playerdashboardbyyearoveryear,
    shotchartdetail, playerdashboardbygeneralsplits
)
from nba_api.stats.static import players, teams
import time
import json
import os
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="NBA Player Evaluator",
    page_icon="🏀",
    layout="wide"
)

# Cache file for player data
CACHE_FILE = "nba_player_cache.json"
CACHE_DURATION = timedelta(hours=6)  # Cache for 6 hours

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_active_players():
    """Get all active NBA players"""
    try:
        # Get all players from NBA API
        all_players = players.get_players()
        
        # Filter for active players more accurately
        active_players = []
        current_year = 2024  # Current NBA season
        
        for player in all_players:
            # Check if player is marked as active OR has recent activity
            if player.get('is_active', False):
                active_players.append(player)
            elif player.get('to_year', 0) >= current_year - 1:  # Played recently
                active_players.append(player)
        
        # Remove duplicates and sort
        seen_names = set()
        unique_active_players = []
        for player in active_players:
            if player['full_name'] not in seen_names:
                seen_names.add(player['full_name'])
                unique_active_players.append(player)
        
        st.info(f"Found {len(unique_active_players)} active NBA players")
        return unique_active_players
        
    except Exception as e:
        st.error(f"Error fetching players: {e}")
        return []

@st.cache_data(ttl=3600)
def get_player_stats(player_id, season="2023-24"):
    """Get comprehensive player stats from NBA API"""
    try:
        # Get basic season stats
        career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
        season_stats = career_stats.get_data_frames()[0]
        
        # Get current season stats if available
        current_season = season_stats[season_stats['SEASON_ID'].str.contains(season.replace('-', '-'))]
        if current_season.empty:
            # Fallback to most recent season
            current_season = season_stats.iloc[-1:] if not season_stats.empty else None
        
        if current_season is None or current_season.empty:
            return None
            
        stats = current_season.iloc[0]
        
        # Get more detailed stats
        try:
            player_dashboard = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
                player_id=player_id, season=season, season_type_all_star='Regular Season'
            )
            general_splits = player_dashboard.get_data_frames()[0]
            if not general_splits.empty:
                detailed_stats = general_splits.iloc[0]
            else:
                detailed_stats = stats
        except:
            detailed_stats = stats
        
        # Process and return stats
        processed_stats = {
            'ppg': float(stats.get('PTS', 0)) / max(float(stats.get('GP', 1)), 1),
            'rpg': float(stats.get('REB', 0)) / max(float(stats.get('GP', 1)), 1),
            'apg': float(stats.get('AST', 0)) / max(float(stats.get('GP', 1)), 1),
            'fg_pct': float(stats.get('FG_PCT', 0)) if stats.get('FG_PCT') else 0,
            'three_pct': float(stats.get('FG3_PCT', 0)) if stats.get('FG3_PCT') else 0,
            'ft_pct': float(stats.get('FT_PCT', 0)) if stats.get('FT_PCT') else 0,
            # Estimated values for situational stats (would need more specific endpoints)
            'paint_fg': float(stats.get('FG_PCT', 0)) * 1.15 if stats.get('FG_PCT') else 0.5,
            'midrange_fg': float(stats.get('FG_PCT', 0)) * 0.85 if stats.get('FG_PCT') else 0.4,
            'corner_three': float(stats.get('FG3_PCT', 0)) * 1.1 if stats.get('FG3_PCT') else 0.35,
            'clutch_fg': float(stats.get('FG_PCT', 0)) * 0.9 if stats.get('FG_PCT') else 0.45,
            'fast_break_fg': float(stats.get('FG_PCT', 0)) * 1.2 if stats.get('FG_PCT') else 0.6,
            'games_played': float(stats.get('GP', 0)),
            'minutes_per_game': float(stats.get('MIN', 0)) / max(float(stats.get('GP', 1)), 1)
        }
        
        # Cap percentages at 100%
        for key in ['fg_pct', 'three_pct', 'ft_pct', 'paint_fg', 'midrange_fg', 'corner_three', 'clutch_fg', 'fast_break_fg']:
            if processed_stats[key] > 1.0:
                processed_stats[key] = min(processed_stats[key], 1.0)
        
        return processed_stats
        
    except Exception as e:
        st.error(f"Error fetching stats for player {player_id}: {e}")
        return None

def load_cached_data():
    """Load cached player data"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
            if datetime.now() - cache_time < CACHE_DURATION:
                return cache_data.get('players', {})
        except:
            pass
    return {}

def save_cached_data(players_data):
    """Save player data to cache"""
    try:
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'players': players_data
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        st.warning(f"Could not save cache: {e}")

@st.cache_data(ttl=3600)
def get_player_by_name(player_name):
    """Get player ID by name"""
    try:
        all_players = players.get_players()
        for player in all_players:
            if player['full_name'].lower() == player_name.lower():
                return player
        return None
    except:
        return None

# Initialize session state for player data
if 'player_cache' not in st.session_state:
    st.session_state.player_cache = load_cached_data()

if 'available_players' not in st.session_state:
    st.session_state.available_players = []

# Fallback sample players (in case API fails)
FALLBACK_PLAYERS = {
    "LeBron James": {
        "ppg": 25.3, "rpg": 7.3, "apg": 7.4,
        "fg_pct": 0.505, "three_pct": 0.347, "ft_pct": 0.731,
        "paint_fg": 0.612, "midrange_fg": 0.398, "corner_three": 0.367,
        "clutch_fg": 0.478, "fast_break_fg": 0.721
    },
    "Stephen Curry": {
        "ppg": 29.5, "rpg": 5.1, "apg": 6.3,
        "fg_pct": 0.493, "three_pct": 0.427, "ft_pct": 0.915,
        "paint_fg": 0.641, "midrange_fg": 0.452, "corner_three": 0.456,
        "clutch_fg": 0.462, "fast_break_fg": 0.589
    },
    "Luka Dončić": {
        "ppg": 28.4, "rpg": 9.1, "apg": 8.0,
        "fg_pct": 0.453, "three_pct": 0.346, "ft_pct": 0.786,
        "paint_fg": 0.587, "midrange_fg": 0.425, "corner_three": 0.389,
        "clutch_fg": 0.487, "fast_break_fg": 0.623
    },
    "Giannis Antetokounmpo": {
        "ppg": 31.1, "rpg": 11.8, "apg": 5.7,
        "fg_pct": 0.553, "three_pct": 0.294, "ft_pct": 0.644,
        "paint_fg": 0.672, "midrange_fg": 0.378, "corner_three": 0.324,
        "clutch_fg": 0.534, "fast_break_fg": 0.745
    },
    "Kevin Durant": {
        "ppg": 29.7, "rpg": 6.7, "apg": 5.0,
        "fg_pct": 0.525, "three_pct": 0.383, "ft_pct": 0.885,
        "paint_fg": 0.634, "midrange_fg": 0.512, "corner_three": 0.412,
        "clutch_fg": 0.498, "fast_break_fg": 0.687
    }
}

def get_available_players():
    """Get list of available players (from API or fallback)"""
    try:
        if not st.session_state.available_players:
            with st.spinner("Loading NBA players..."):
                active_players = get_all_active_players()
                if active_players:
                    # Sort by full name and include ALL active players
                    sorted_players = sorted(active_players, key=lambda x: x['full_name'])
                    st.session_state.available_players = [p['full_name'] for p in sorted_players]
                    st.success(f"Loaded {len(st.session_state.available_players)} active NBA players!")
                else:
                    st.session_state.available_players = list(FALLBACK_PLAYERS.keys())
                    st.warning("Using fallback player data (API unavailable)")
        
        return st.session_state.available_players
    except Exception as e:
        st.error(f"Error loading players: {e}")
        return list(FALLBACK_PLAYERS.keys())

def get_player_stats_cached(player_name):
    """Get player stats with caching"""
    # Check cache first
    if player_name in st.session_state.player_cache:
        return st.session_state.player_cache[player_name]
    
    # Try to get from API
    player_info = get_player_by_name(player_name)
    if player_info:
        with st.spinner(f"Loading stats for {player_name}..."):
            stats = get_player_stats(player_info['id'])
            if stats:
                # Cache the result
                st.session_state.player_cache[player_name] = stats
                save_cached_data(st.session_state.player_cache)
                return stats
    
    # Fallback to hardcoded data
    return FALLBACK_PLAYERS.get(player_name)

# Predefined archetypes
ARCHETYPES = {
    "Elite Scorer": {
        "ppg": 28.0, "rpg": 5.0, "apg": 4.0,
        "fg_pct": 0.480, "three_pct": 0.370, "ft_pct": 0.850,
        "paint_fg": 0.600, "midrange_fg": 0.450, "corner_three": 0.400,
        "clutch_fg": 0.460, "fast_break_fg": 0.650
    },
    "Playmaker": {
        "ppg": 18.0, "rpg": 5.0, "apg": 10.0,
        "fg_pct": 0.450, "three_pct": 0.350, "ft_pct": 0.800,
        "paint_fg": 0.550, "midrange_fg": 0.420, "corner_three": 0.380,
        "clutch_fg": 0.440, "fast_break_fg": 0.620
    },
    "Two-Way Wing": {
        "ppg": 22.0, "rpg": 7.0, "apg": 5.0,
        "fg_pct": 0.470, "three_pct": 0.360, "ft_pct": 0.820,
        "paint_fg": 0.580, "midrange_fg": 0.430, "corner_three": 0.390,
        "clutch_fg": 0.450, "fast_break_fg": 0.640
    },
    "Interior Force": {
        "ppg": 24.0, "rpg": 12.0, "apg": 3.0,
        "fg_pct": 0.560, "three_pct": 0.250, "ft_pct": 0.720,
        "paint_fg": 0.680, "midrange_fg": 0.380, "corner_three": 0.300,
        "clutch_fg": 0.520, "fast_break_fg": 0.720
    }
}

def calculate_similarity_score(player_stats, target_stats):
    """Calculate a similarity score between two sets of stats (0-100)"""
    weights = {
        'ppg': 0.20, 'rpg': 0.15, 'apg': 0.15,
        'fg_pct': 0.15, 'three_pct': 0.10, 'ft_pct': 0.05,
        'paint_fg': 0.05, 'midrange_fg': 0.05, 'corner_three': 0.05, 
        'clutch_fg': 0.03, 'fast_break_fg': 0.02
    }
    
    total_diff = 0
    for stat, weight in weights.items():
        if stat in ['ppg', 'rpg', 'apg']:
            # For counting stats, normalize by dividing by target value
            diff = abs(player_stats[stat] - target_stats[stat]) / max(target_stats[stat], 1)
        else:
            # For percentages, direct difference
            diff = abs(player_stats[stat] - target_stats[stat])
        
        total_diff += diff * weight
    
    # Convert to similarity score (higher is better)
    similarity = max(0, 100 - (total_diff * 200))
    return round(similarity, 1)

def create_comparison_chart(player_stats, target_stats, player_name, target_name):
    """Create a radar chart comparing player stats"""
    categories = ['PPG', 'RPG', 'APG', 'FG%', '3P%', 'FT%', 'Paint FG%', 'Mid-Range FG%']
    
    player_values = [
        player_stats['ppg'], player_stats['rpg'], player_stats['apg'],
        player_stats['fg_pct'] * 100, player_stats['three_pct'] * 100, 
        player_stats['ft_pct'] * 100, player_stats['paint_fg'] * 100,
        player_stats['midrange_fg'] * 100
    ]
    
    target_values = [
        target_stats['ppg'], target_stats['rpg'], target_stats['apg'],
        target_stats['fg_pct'] * 100, target_stats['three_pct'] * 100,
        target_stats['ft_pct'] * 100, target_stats['paint_fg'] * 100,
        target_stats['midrange_fg'] * 100
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line_color='rgb(255, 0, 0)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=categories,
        fill='toself',
        name=target_name,
        line_color='rgb(0, 0, 255)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(player_values), max(target_values)) * 1.1]
            )),
        showlegend=True,
        title=f"{player_name} vs {target_name} Comparison"
    )
    
    return fig

def display_detailed_stats(stats, title):
    """Display detailed stats in a formatted way"""
    st.subheader(title)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Points per Game", f"{stats['ppg']:.1f}")
        st.metric("Rebounds per Game", f"{stats['rpg']:.1f}")
        st.metric("Assists per Game", f"{stats['apg']:.1f}")
    
    with col2:
        st.metric("Field Goal %", f"{stats['fg_pct']:.1%}")
        st.metric("Three Point %", f"{stats['three_pct']:.1%}")
        st.metric("Free Throw %", f"{stats['ft_pct']:.1%}")
    
    with col3:
        st.metric("Paint FG%", f"{stats['paint_fg']:.1%}")
        st.metric("Mid-Range FG%", f"{stats['midrange_fg']:.1%}")
        st.metric("Corner 3 FG%", f"{stats['corner_three']:.1%}")

# Advanced statistics functions
def get_advanced_player_stats(player_id, season="2023-24"):
    """Get advanced player statistics using multiple endpoints"""
    advanced_stats = {}
    
    try:
        # Shooting splits for detailed shooting data
        from nba_api.stats.endpoints import playerdashboardbyshootingsplits
        shooting_splits = playerdashboardbyshootingsplits.PlayerDashboardByShootingSplits(
            player_id=player_id, season=season
        )
        shooting_data = shooting_splits.get_data_frames()
        
        if shooting_data and len(shooting_data) > 1:
            shot_areas = shooting_data[1]  # Shot areas data frame
            if not shot_areas.empty:
                # Extract specific shooting zones
                for _, row in shot_areas.iterrows():
                    zone = row.get('GROUP_VALUE', '').lower()
                    if 'paint' in zone:
                        advanced_stats['paint_fg'] = float(row.get('FG_PCT', 0)) if row.get('FG_PCT') else 0
                    elif 'mid-range' in zone or 'midrange' in zone:
                        advanced_stats['midrange_fg'] = float(row.get('FG_PCT', 0)) if row.get('FG_PCT') else 0
                    elif 'corner 3' in zone:
                        advanced_stats['corner_three'] = float(row.get('FG_PCT', 0)) if row.get('FG_PCT') else 0
        
        # Clutch performance
        from nba_api.stats.endpoints import playerdashboardbyclutch
        clutch_stats = playerdashboardbyclutch.PlayerDashboardByClutch(
            player_id=player_id, season=season
        )
        clutch_data = clutch_stats.get_data_frames()
        
        if clutch_data and len(clutch_data) > 0:
            clutch_overall = clutch_data[0]
            if not clutch_overall.empty:
                advanced_stats['clutch_fg'] = float(clutch_overall.iloc[0].get('FG_PCT', 0)) if clutch_overall.iloc[0].get('FG_PCT') else 0
        
        # Add rate limiting
        time.sleep(0.6)
        
    except Exception as e:
        st.warning(f"Could not fetch advanced stats: {e}")
    
    return advanced_stats

def create_advanced_comparison_chart(player_stats, target_stats, player_name, target_name):
    """Create enhanced radar chart with more categories"""
    categories = [
        'PPG', 'RPG', 'APG', 'FG%', '3P%', 'FT%', 
        'Paint FG%', 'Mid-Range FG%', 'Corner 3%', 'Clutch FG%'
    ]
    
    def get_stat_value(stats, stat_key, is_percentage=False):
        value = stats.get(stat_key, 0)
        return value * 100 if is_percentage and value <= 1 else value
    
    player_values = [
        get_stat_value(player_stats, 'ppg'),
        get_stat_value(player_stats, 'rpg'),
        get_stat_value(player_stats, 'apg'),
        get_stat_value(player_stats, 'fg_pct', True),
        get_stat_value(player_stats, 'three_pct', True),
        get_stat_value(player_stats, 'ft_pct', True),
        get_stat_value(player_stats, 'paint_fg', True),
        get_stat_value(player_stats, 'midrange_fg', True),
        get_stat_value(player_stats, 'corner_three', True),
        get_stat_value(player_stats, 'clutch_fg', True)
    ]
    
    target_values = [
        get_stat_value(target_stats, 'ppg'),
        get_stat_value(target_stats, 'rpg'),
        get_stat_value(target_stats, 'apg'),
        get_stat_value(target_stats, 'fg_pct', True),
        get_stat_value(target_stats, 'three_pct', True),
        get_stat_value(target_stats, 'ft_pct', True),
        get_stat_value(target_stats, 'paint_fg', True),
        get_stat_value(target_stats, 'midrange_fg', True),
        get_stat_value(target_stats, 'corner_three', True),
        get_stat_value(target_stats, 'clutch_fg', True)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=player_values,
        theta=categories,
        fill='toself',
        name=player_name,
        line_color='rgb(255, 0, 0)',
        fillcolor='rgba(255, 0, 0, 0.1)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=categories,
        fill='toself',
        name=target_name,
        line_color='rgb(0, 0, 255)',
        fillcolor='rgba(0, 0, 255, 0.1)'
    ))
    
    max_value = max(max(player_values), max(target_values)) * 1.1
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max_value],
                tickmode='linear',
                tick0=0,
                dtick=max_value/5
            )),
        showlegend=True,
        title=f"{player_name} vs {target_name} - Advanced Comparison",
        height=600
    )
    
    return fig

def get_shot_chart_data(player_id, season="2023-24"):
    """Get shot chart data for visualization"""
    try:
        from nba_api.stats.endpoints import shotchartdetail
        
        shot_chart = shotchartdetail.ShotChartDetail(
            player_id=player_id,
            team_id=0,
            season_nullable=season,
            context_measure_simple='FGA',
            season_type_all_star='Regular Season'
        )
        
        shot_data = shot_chart.get_data_frames()[0]
        
        if shot_data.empty:
            return None
            
        # Add rate limiting
        time.sleep(0.6)
        
        return shot_data
        
    except Exception as e:
        st.error(f"Error fetching shot chart data: {e}")
        return None

def create_shot_chart(shot_data, player_name):
    """Create interactive shot chart visualization"""
    if shot_data is None or shot_data.empty:
        st.warning(f"No shot chart data available for {player_name}")
        return None
    
    # Convert coordinates (NBA API uses 1/10th feet, origin at basket)
    shot_data['X_COORD'] = shot_data['LOC_X'] / 10
    shot_data['Y_COORD'] = shot_data['LOC_Y'] / 10
    
    # Create color mapping for makes/misses
    shot_data['COLOR'] = shot_data['SHOT_MADE_FLAG'].map({1: 'Made', 0: 'Missed'})
    shot_data['SIZE'] = 8  # Uniform size for all shots
    
    # Create the plot
    fig = px.scatter(
        shot_data,
        x='X_COORD',
        y='Y_COORD',
        color='COLOR',
        color_discrete_map={'Made': '#00FF00', 'Missed': '#FF0000'},
        hover_data={
            'SHOT_DISTANCE': True,
            'SHOT_TYPE': True,
            'ACTION_TYPE': True,
            'PERIOD': True,
            'MINUTES_REMAINING': True,
            'SECONDS_REMAINING': True,
            'X_COORD': False,
            'Y_COORD': False
        },
        title=f"{player_name} - Shot Chart",
        labels={'X_COORD': 'Court Position (X)', 'Y_COORD': 'Court Position (Y)'}
    )
    
    # Add court outline (simplified)
    # Basketball court dimensions: 50 feet wide, 94 feet long (half court ~47 feet)
    court_shapes = []
    
    # Three-point line (simplified arc)
    theta = np.linspace(-np.pi/2, np.pi/2, 100)
    three_point_x = 23.75 * np.cos(theta)  # 23.75 feet from basket
    three_point_y = 23.75 * np.sin(theta) + 5.25  # 5.25 feet from baseline
    
    # Add three-point arc
    fig.add_trace(go.Scatter(
        x=three_point_x,
        y=three_point_y,
        mode='lines',
        line=dict(color='black', width=2),
        name='3-Point Line',
        showlegend=False
    ))
    
    # Add court boundaries
    fig.add_hline(y=-2.5, line_dash="solid", line_color="black", line_width=2)  # Baseline
    fig.add_vline(x=-25, line_dash="solid", line_color="black", line_width=2)   # Left sideline
    fig.add_vline(x=25, line_dash="solid", line_color="black", line_width=2)    # Right sideline
    fig.add_hline(y=47, line_dash="solid", line_color="black", line_width=2)    # Half court
    
    # Free throw circle
    theta_ft = np.linspace(0, 2*np.pi, 100)
    ft_circle_x = 6 * np.cos(theta_ft)
    ft_circle_y = 6 * np.sin(theta_ft) + 19
    
    fig.add_trace(go.Scatter(
        x=ft_circle_x,
        y=ft_circle_y,
        mode='lines',
        line=dict(color='black', width=1),
        name='Free Throw Circle',
        showlegend=False
    ))
    
    # Paint/key area
    fig.add_shape(
        type="rect",
        x0=-8, y0=-2.5, x1=8, y1=19,
        line=dict(color="black", width=2),
        fillcolor="rgba(0,0,0,0)"
    )
    
    # Update layout for better court appearance
    fig.update_layout(
        xaxis=dict(
            range=[-30, 30],
            showgrid=False,
            zeroline=False,
            title="",
            showticklabels=False
        ),
        yaxis=dict(
            range=[-5, 50],
            showgrid=False,
            zeroline=False,
            title="",
            showticklabels=False,
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor='lightgray',
        paper_bgcolor='white',
        height=700,
        width=600,
        title=dict(
            text=f"{player_name} - Shot Chart ({len(shot_data)} shots)",
            x=0.5
        )
    )
    
    return fig

def create_nba_style_zone_chart(shot_data, player_name):
    """Create NBA-style zone-based shot chart with colored regions"""
    if shot_data is None or shot_data.empty:
        st.warning(f"No shot chart data available for {player_name}")
        return None
    
    # Define the exact zones from the reference image
    def get_shot_zone(x, y, distance):
        """Categorize shots into NBA zones based on court position"""
        # Convert to feet (if not already)
        x_ft = x / 10 if abs(x) > 100 else x
        y_ft = y / 10 if abs(y) > 100 else y
        
        # Zone definitions based on NBA court areas
        if distance <= 8:  # Close range/Paint
            if abs(x_ft) <= 8 and y_ft <= 19:
                return "Paint"
            else:
                return "Close Range"
        elif distance <= 16:  # Mid-range areas
            if y_ft <= 14:
                if x_ft < -8:
                    return "Left Baseline Mid"
                elif x_ft > 8:
                    return "Right Baseline Mid"
                else:
                    return "Mid-Range Center"
            else:
                if x_ft < -6:
                    return "Left Mid-Range"
                elif x_ft > 6:
                    return "Right Mid-Range"
                else:
                    return "Top of Key"
        else:  # Three-point range
            # Corner 3s
            if abs(x_ft) > 22 and y_ft <= 14:
                return "Left Corner 3" if x_ft < 0 else "Right Corner 3"
            # Wing 3s
            elif 14 < y_ft <= 26:
                return "Left Wing 3" if x_ft < 0 else "Right Wing 3"
            # Top of arc
            else:
                return "Top of Arc 3"
    
    # Categorize all shots
    shot_data['ZONE'] = shot_data.apply(
        lambda row: get_shot_zone(row['LOC_X'], row['LOC_Y'], row['SHOT_DISTANCE']), 
        axis=1
    )
    
    # Calculate zone statistics
    zone_stats = shot_data.groupby('ZONE').agg({
        'SHOT_MADE_FLAG': ['count', 'sum', 'mean']
    })
    
    # Flatten the MultiIndex columns properly
    zone_stats.columns = zone_stats.columns.droplevel(0)
    zone_stats.columns = ['Attempts', 'Makes', 'FG_PCT']
    zone_stats = zone_stats.reset_index()
    zone_stats = zone_stats.round(3)
    
    # Create the court figure
    fig = go.Figure()
    
    # Define zone coordinates and colors based on efficiency
    def get_zone_color(fg_pct):
        """Get color based on shooting percentage"""
        if fg_pct >= 0.50:
            return 'rgba(76, 175, 80, 0.8)'  # Green
        elif fg_pct >= 0.40:
            return 'rgba(255, 235, 59, 0.8)'  # Yellow
        elif fg_pct >= 0.30:
            return 'rgba(255, 152, 0, 0.8)'   # Orange
        else:
            return 'rgba(244, 67, 54, 0.8)'   # Red
    
    # Define zone shapes (simplified rectangles and polygons for each zone)
    zone_shapes = {
        "Paint": {"x": [-8, 8, 8, -8, -8], "y": [-2.5, -2.5, 19, 19, -2.5]},
        "Left Corner 3": {"x": [-25, -22, -22, -25, -25], "y": [-2.5, -2.5, 14, 14, -2.5]},
        "Right Corner 3": {"x": [22, 25, 25, 22, 22], "y": [-2.5, -2.5, 14, 14, -2.5]},
        "Left Baseline Mid": {"x": [-22, -8, -8, -22, -22], "y": [-2.5, -2.5, 14, 14, -2.5]},
        "Right Baseline Mid": {"x": [8, 22, 22, 8, 8], "y": [-2.5, -2.5, 14, 14, -2.5]},
        "Left Wing 3": {"x": [-25, -22, -8, -12, -25], "y": [14, 14, 19, 26, 26]},
        "Right Wing 3": {"x": [25, 22, 8, 12, 25], "y": [14, 14, 19, 26, 26]},
        "Left Mid-Range": {"x": [-22, -8, -8, -22, -22], "y": [14, 14, 19, 19, 14]},
        "Right Mid-Range": {"x": [8, 22, 22, 8, 8], "y": [14, 14, 19, 19, 14]},
        "Top of Key": {"x": [-8, 8, 8, -8, -8], "y": [19, 19, 26, 26, 19]},
        "Top of Arc 3": {"x": [-12, 12, 12, -12, -12], "y": [26, 26, 40, 40, 26]}
    }
    
    # Add court outline first
    # Three-point arc
    theta = np.linspace(-np.pi/2, np.pi/2, 100)
    three_point_x = 23.75 * np.cos(theta)
    three_point_y = 23.75 * np.sin(theta) + 5.25
    
    fig.add_trace(go.Scatter(
        x=three_point_x, y=three_point_y,
        mode='lines', line=dict(color='white', width=3),
        name='3-Point Line', showlegend=False
    ))
    
    # Add zone shapes with colors based on efficiency
    for _, row in zone_stats.iterrows():
        zone = row['ZONE']
        if zone in zone_shapes:
            coords = zone_shapes[zone]
            color = get_zone_color(row['FG_PCT'])
            
            # Add filled zone
            fig.add_trace(go.Scatter(
                x=coords['x'],
                y=coords['y'],
                fill='toself',
                fillcolor=color,
                line=dict(color='white', width=2),
                mode='lines',
                name=zone,
                showlegend=False,
                hovertemplate=f"<b>{zone}</b><br>" +
                            f"FG%: {row['FG_PCT']:.1%}<br>" +
                            f"Makes: {row['Makes']}<br>" +
                            f"Attempts: {row['Attempts']}<extra></extra>"
            ))
            
            # Add text annotations
            center_x = sum(coords['x'][:-1]) / len(coords['x'][:-1])
            center_y = sum(coords['y'][:-1]) / len(coords['y'][:-1])
            
            fig.add_annotation(
                x=center_x, y=center_y,
                text=f"{row['Makes']}/{row['Attempts']}<br>{row['FG_PCT']:.1%}",
                showarrow=False,
                font=dict(color='white', size=12, family='Arial Black'),
                bgcolor='rgba(0,0,0,0.7)',
                bordercolor='white',
                borderwidth=1
            )
    
    # Add court elements
    # Free throw circle
    theta_ft = np.linspace(0, 2*np.pi, 100)
    ft_circle_x = 6 * np.cos(theta_ft)
    ft_circle_y = 6 * np.sin(theta_ft) + 19
    
    fig.add_trace(go.Scatter(
        x=ft_circle_x, y=ft_circle_y,
        mode='lines', line=dict(color='white', width=2),
        name='Free Throw Circle', showlegend=False
    ))
    
    # Court boundaries
    fig.add_shape(type="rect", x0=-25, y0=-2.5, x1=25, y1=47,
                 line=dict(color="white", width=3), fillcolor="rgba(0,0,0,0)")
    
    # Center court circle
    fig.add_shape(type="circle", x0=-6, y0=41, x1=6, y1=53,
                 line=dict(color="white", width=2), fillcolor="rgba(0,0,0,0)")
    
    # Update layout to match NBA style
    fig.update_layout(
        title=dict(
            text=f"{player_name} - Zone Shooting Chart",
            x=0.5,
            font=dict(size=20, color='white', family='Arial Black')
        ),
        xaxis=dict(
            range=[-27, 27], showgrid=False, zeroline=False,
            showticklabels=False, title=""
        ),
        yaxis=dict(
            range=[-5, 50], showgrid=False, zeroline=False,
            showticklabels=False, title="", scaleanchor="x", scaleratio=1
        ),
        plot_bgcolor='rgba(139, 69, 19, 1)',  # Wood court color
        paper_bgcolor='rgba(139, 69, 19, 1)',
        height=700, width=700,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Add legend
    legend_data = [
        {"label": "Elite (50%+)", "color": 'rgba(76, 175, 80, 0.8)'},
        {"label": "Good (40-49%)", "color": 'rgba(255, 235, 59, 0.8)'},
        {"label": "Average (30-39%)", "color": 'rgba(255, 152, 0, 0.8)'},
        {"label": "Poor (<30%)", "color": 'rgba(244, 67, 54, 0.8)'}
    ]
    
    for i, item in enumerate(legend_data):
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(size=15, color=item['color']),
            name=item['label'],
            showlegend=True
        ))
    
    return fig

def create_zone_efficiency_summary(shot_data, player_name):
    """Create a summary table of zone efficiency"""
    if shot_data is None or shot_data.empty:
        return None
    
    # Use the same zone categorization as the chart
    def get_shot_zone(x, y, distance):
        x_ft = x / 10 if abs(x) > 100 else x
        y_ft = y / 10 if abs(y) > 100 else y
        
        if distance <= 8:
            if abs(x_ft) <= 8 and y_ft <= 19:
                return "Paint"
            else:
                return "Close Range"
        elif distance <= 16:
            if y_ft <= 14:
                if x_ft < -8:
                    return "Left Baseline Mid"
                elif x_ft > 8:
                    return "Right Baseline Mid"
                else:
                    return "Mid-Range Center"
            else:
                if x_ft < -6:
                    return "Left Mid-Range"
                elif x_ft > 6:
                    return "Right Mid-Range"
                else:
                    return "Top of Key"
        else:
            if abs(x_ft) > 22 and y_ft <= 14:
                return "Left Corner 3" if x_ft < 0 else "Right Corner 3"
            elif 14 < y_ft <= 26:
                return "Left Wing 3" if x_ft < 0 else "Right Wing 3"
            else:
                return "Top of Arc 3"
    
    shot_data['ZONE'] = shot_data.apply(
        lambda row: get_shot_zone(row['LOC_X'], row['LOC_Y'], row['SHOT_DISTANCE']), 
        axis=1
    )
    
    # Calculate comprehensive zone stats
    zone_stats = shot_data.groupby('ZONE').agg({
        'SHOT_MADE_FLAG': ['count', 'sum', 'mean']
    })
    
    # Flatten the MultiIndex columns properly
    zone_stats.columns = zone_stats.columns.droplevel(0)
    zone_stats.columns = ['Attempts', 'Makes', 'FG_PCT'] 
    zone_stats = zone_stats.reset_index()
    zone_stats = zone_stats.round(3)
    
    # Add efficiency rating
    def get_efficiency_rating(fg_pct):
        if fg_pct >= 0.50:
            return "🟢 Elite"
        elif fg_pct >= 0.40:
            return "🟡 Good"
        elif fg_pct >= 0.30:
            return "🟠 Average"
        else:
            return "🔴 Poor"
    
    zone_stats['Rating'] = zone_stats['FG_PCT'].apply(get_efficiency_rating)
    zone_stats['FG%'] = zone_stats['FG_PCT'].apply(lambda x: f"{x:.1%}")
    
    # Sort by attempts (most frequent zones first)
    zone_stats = zone_stats.sort_values('Attempts', ascending=False)
    
    return zone_stats[['ZONE', 'Attempts', 'Makes', 'FG%', 'Rating']]

def analyze_shot_chart_data(shot_data, player_name):
    """Analyze shot chart data and provide insights"""
    if shot_data is None or shot_data.empty:
        return {}
    
    analysis = {}
    
    # Overall shooting
    total_shots = len(shot_data)
    total_makes = shot_data['SHOT_MADE_FLAG'].sum()
    overall_fg_pct = total_makes / total_shots if total_shots > 0 else 0
    
    analysis['total_shots'] = total_shots
    analysis['overall_fg_pct'] = overall_fg_pct
    
    # Shot distance preferences
    avg_distance = shot_data['SHOT_DISTANCE'].mean()
    analysis['avg_shot_distance'] = avg_distance
    
    # Three-point vs two-point split
    three_pointers = shot_data[shot_data['SHOT_TYPE'] == '3PT Field Goal']
    two_pointers = shot_data[shot_data['SHOT_TYPE'] == '2PT Field Goal']
    
    analysis['three_point_attempts'] = len(three_pointers)
    analysis['three_point_pct'] = three_pointers['SHOT_MADE_FLAG'].mean() if len(three_pointers) > 0 else 0
    analysis['two_point_attempts'] = len(two_pointers)
    analysis['two_point_pct'] = two_pointers['SHOT_MADE_FLAG'].mean() if len(two_pointers) > 0 else 0
    
    # Shot selection analysis
    close_shots = shot_data[shot_data['SHOT_DISTANCE'] <= 8]
    analysis['close_shot_frequency'] = len(close_shots) / total_shots if total_shots > 0 else 0
    analysis['close_shot_pct'] = close_shots['SHOT_MADE_FLAG'].mean() if len(close_shots) > 0 else 0
    
    # Best shooting zone
    shot_data['ZONE'] = shot_data.apply(
        lambda row: 'Paint' if row['SHOT_DISTANCE'] <= 8
        else 'Mid-Range' if row['SHOT_DISTANCE'] <= 16
        else 'Corner 3' if 'Corner 3' in row['SHOT_TYPE']
        else '3-Point', axis=1
    )
    
    zone_stats = shot_data.groupby('ZONE')['SHOT_MADE_FLAG'].agg(['count', 'mean'])
    zone_stats = zone_stats[zone_stats['count'] >= 10]  # Minimum 10 attempts
    
    if not zone_stats.empty:
        best_zone = zone_stats['mean'].idxmax()
        analysis['best_shooting_zone'] = best_zone
        analysis['best_zone_pct'] = zone_stats.loc[best_zone, 'mean']
    
    return analysis

def display_shot_chart_insights(shot_data, player_name):
    """Display shot chart insights in the UI"""
    analysis = analyze_shot_chart_data(shot_data, player_name)
    
    if not analysis:
        return
    
    st.subheader(f"📈 {player_name} Shooting Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Shots",
            f"{analysis.get('total_shots', 0):,}",
            help="Total field goal attempts this season"
        )
    
    with col2:
        st.metric(
            "Overall FG%",
            f"{analysis.get('overall_fg_pct', 0):.1%}",
            help="Overall field goal percentage"
        )
    
    with col3:
        st.metric(
            "Avg Shot Distance",
            f"{analysis.get('avg_shot_distance', 0):.1f} ft",
            help="Average distance of all shot attempts"
        )
    
    with col4:
        if 'best_shooting_zone' in analysis:
            st.metric(
                "Best Zone",
                analysis['best_shooting_zone'],
                f"{analysis.get('best_zone_pct', 0):.1%}",
                help="Most efficient shooting zone (min 10 attempts)"
            )
        else:
            st.metric("Best Zone", "N/A", help="Insufficient data")
    
    # Additional insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Shot Distribution:**")
        three_pct = analysis.get('three_point_attempts', 0) / analysis.get('total_shots', 1) * 100
        two_pct = analysis.get('two_point_attempts', 0) / analysis.get('total_shots', 1) * 100
        st.write(f"• 3-Point Attempts: {three_pct:.1f}% ({analysis.get('three_point_pct', 0):.1%} FG%)")
        st.write(f"• 2-Point Attempts: {two_pct:.1f}% ({analysis.get('two_point_pct', 0):.1%} FG%)")
        st.write(f"• Close Range Frequency: {analysis.get('close_shot_frequency', 0):.1%}")
    
    with col2:
        st.write("**Shooting Tendencies:**")
        if analysis.get('avg_shot_distance', 0) > 18:
            st.write("• Perimeter-oriented shooter")
        elif analysis.get('avg_shot_distance', 0) < 12:
            st.write("• Paint-focused player")
        else:
            st.write("• Balanced shot selection")
            
        if analysis.get('close_shot_frequency', 0) > 0.4:
            st.write("• High close-range frequency")
        elif analysis.get('close_shot_frequency', 0) < 0.2:
            st.write("• Limited paint presence")
        
        if analysis.get('three_point_pct', 0) > 0.37:
            st.write("• Elite 3-point shooter")
        elif analysis.get('three_point_pct', 0) > 0.33:
            st.write("• Good 3-point shooter")

def display_player_database_info():
    """Display information about the player database"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Player Database")
    
    total_players = len(st.session_state.available_players) if st.session_state.available_players else 0
    cached_players = len(st.session_state.player_cache)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Total Players", total_players)
    with col2:
        st.metric("Cached Stats", cached_players)
    
    # Database status
    if total_players > 400:
        st.sidebar.success("🟢 Full NBA Database")
    elif total_players > 50:
        st.sidebar.warning("🟡 Partial Database")
    else:
        st.sidebar.error("🔴 Limited Database")
    
    # Cache efficiency
    if total_players > 0:
        cache_percentage = (cached_players / total_players) * 100
        st.sidebar.progress(cache_percentage / 100, f"Cache: {cache_percentage:.1f}%")

def get_popular_teams():
    """Get list of popular NBA teams for better player filtering"""
    popular_teams = [
        'Los Angeles Lakers', 'Golden State Warriors', 'Boston Celtics',
        'Miami Heat', 'Chicago Bulls', 'San Antonio Spurs',
        'Los Angeles Clippers', 'Brooklyn Nets', 'Philadelphia 76ers',
        'Milwaukee Bucks', 'Denver Nuggets', 'Phoenix Suns'
    ]
    return popular_teams

# Main app
def main():
    st.title("🏀 NBA Player Evaluator")
    st.markdown("Compare NBA players against targets to evaluate fit and potential")
    
    # Sidebar for selections
    st.sidebar.header("Player & Target Selection")
    
    # Advanced stats option
    use_advanced_stats = st.sidebar.checkbox(
        "Use Advanced Stats (slower, more detailed)", 
        value=False,
        help="Fetches detailed shooting zones and clutch performance data"
    )
    
    # Shot chart option
    show_shot_charts = st.sidebar.checkbox(
        "Show Shot Charts", 
        value=False,
        help="Display interactive shot charts and shooting analysis"
    )
    
    # Display player database info
    display_player_database_info()
    
    # Get available players
    available_players = get_available_players()
    
    # Add search functionality for better UX with many players
    st.sidebar.subheader("🔍 Player Search")
    search_term = st.sidebar.text_input(
        "Search for a player:",
        placeholder="Type player name...",
        help="Search through all active NBA players"
    )
    
    # Filter players based on search
    if search_term:
        filtered_players = [
            player for player in available_players 
            if search_term.lower() in player.lower()
        ]
        if filtered_players:
            available_players_list = filtered_players
        else:
            st.sidebar.warning(f"No players found matching '{search_term}'")
            available_players_list = available_players[:20]  # Show first 20 as fallback
    else:
        # Show popular players first, then all others
        popular_players = [p for p in available_players if p in FALLBACK_PLAYERS.keys()]
        other_players = [p for p in available_players if p not in FALLBACK_PLAYERS.keys()]
        available_players_list = popular_players + other_players
    
    # Select project player
    project_player = st.sidebar.selectbox(
        "Select Project Player:",
        available_players_list,
        help=f"Choose from {len(available_players)} active NBA players"
    )
    
    # Select comparison type
    comparison_type = st.sidebar.radio(
        "Compare against:",
        ["Another Player", "Archetype"]
    )
    
    if comparison_type == "Another Player":
        # Filter target players (exclude selected project player)
        target_players_list = [p for p in available_players_list if p != project_player]
        
        target = st.sidebar.selectbox(
            "Select Target Player:",
            target_players_list,
            help="Choose a player to compare against"
        )
        target_stats = get_player_stats_cached(target)
        target_name = target
    else:
        target = st.sidebar.selectbox(
            "Select Target Archetype:",
            list(ARCHETYPES.keys())
        )
        target_stats = ARCHETYPES[target]
        target_name = f"{target} Archetype"
    
    # Get player stats
    player_stats = get_player_stats_cached(project_player)
    
    # Get advanced stats if requested
    if use_advanced_stats and comparison_type == "Another Player":
        player_info = get_player_by_name(project_player)
        target_info = get_player_by_name(target)
        
        if player_info and target_info:
            with st.spinner("Loading advanced statistics..."):
                advanced_player_stats = get_advanced_player_stats(player_info['id'])
                advanced_target_stats = get_advanced_player_stats(target_info['id'])
                
                # Merge advanced stats with basic stats
                if advanced_player_stats:
                    player_stats.update(advanced_player_stats)
                if advanced_target_stats:
                    target_stats.update(advanced_target_stats)
    
    # Check if we have valid stats for both players
    if not player_stats:
        st.error(f"Could not load stats for {project_player}. Please try another player.")
        return
    
    if not target_stats:
        st.error(f"Could not load stats for {target}. Please try another player.")
        return
    
    # Calculate similarity
    similarity = calculate_similarity_score(player_stats, target_stats)
    
    # Main content
    st.header(f"Evaluating: {project_player}")
    
    # Similarity score
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(
            f"Similarity to {target_name}",
            f"{similarity}%",
            help="Similarity score based on weighted comparison of key stats"
        )
    
    # Detailed stats comparison
    col1, col2 = st.columns(2)
    
    with col1:
        display_detailed_stats(player_stats, f"{project_player} Stats")
    
    with col2:
        display_detailed_stats(target_stats, f"{target_name} Stats")
    
    # Radar chart comparison
    st.header("Visual Comparison")
    
    # Use advanced chart if advanced stats are enabled and we have player vs player
    if use_advanced_stats and comparison_type == "Another Player":
        chart = create_advanced_comparison_chart(player_stats, target_stats, project_player, target_name)
    else:
        chart = create_comparison_chart(player_stats, target_stats, project_player, target_name)
    
    st.plotly_chart(chart, use_container_width=True)
    
    # Shot Charts Section
    if show_shot_charts and comparison_type == "Another Player":
        st.header("🎯 Shot Chart Analysis")
        
        # Get player IDs for shot chart data
        player_info = get_player_by_name(project_player)
        target_info = get_player_by_name(target)
        
        if player_info and target_info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{project_player} Shot Chart")
                with st.spinner(f"Loading shot chart for {project_player}..."):
                    player_shot_data = get_shot_chart_data(player_info['id'])
                    if player_shot_data is not None:
                        # NBA-style zone chart
                        zone_chart_fig = create_nba_style_zone_chart(player_shot_data, project_player)
                        if zone_chart_fig:
                            st.plotly_chart(zone_chart_fig, use_container_width=True)
                            
                            # Zone efficiency summary table
                            zone_summary = create_zone_efficiency_summary(player_shot_data, project_player)
                            if zone_summary is not None:
                                st.subheader("📊 Zone Efficiency Summary")
                                st.dataframe(zone_summary, use_container_width=True)
                            
                            # Shot insights
                            display_shot_chart_insights(player_shot_data, project_player)
                    else:
                        st.warning(f"No shot chart data available for {project_player}")
            
            with col2:
                st.subheader(f"{target} Shot Chart")
                with st.spinner(f"Loading shot chart for {target}..."):
                    target_shot_data = get_shot_chart_data(target_info['id'])
                    if target_shot_data is not None:
                        # NBA-style zone chart
                        target_zone_chart_fig = create_nba_style_zone_chart(target_shot_data, target)
                        if target_zone_chart_fig:
                            st.plotly_chart(target_zone_chart_fig, use_container_width=True)
                            
                            # Zone efficiency summary table
                            target_zone_summary = create_zone_efficiency_summary(target_shot_data, target)
                            if target_zone_summary is not None:
                                st.subheader("📊 Zone Efficiency Summary")
                                st.dataframe(target_zone_summary, use_container_width=True)
                            
                            # Shot insights
                            display_shot_chart_insights(target_shot_data, target)
                    else:
                        st.warning(f"No shot chart data available for {target}")
            
            # Combined zone comparison
            if player_shot_data is not None and target_shot_data is not None:
                st.subheader("📊 Zone Efficiency Comparison")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**{project_player} Zone Summary**")
                    player_zone_summary = create_zone_efficiency_summary(player_shot_data, project_player)
                    if player_zone_summary is not None:
                        st.dataframe(player_zone_summary, use_container_width=True)
                
                with col2:
                    st.write(f"**{target} Zone Summary**")
                    target_zone_summary = create_zone_efficiency_summary(target_shot_data, target)
                    if target_zone_summary is not None:
                        st.dataframe(target_zone_summary, use_container_width=True)
        else:
            st.error("Could not load player information for shot charts")
    elif show_shot_charts and comparison_type == "Archetype":
        st.info("Shot charts are only available for player vs player comparisons")
    
    # Detailed breakdown
    st.header("Detailed Analysis")
    
    # Strengths and weaknesses
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Relative Strengths")
        strengths = []
        for stat in ['ppg', 'rpg', 'apg', 'fg_pct', 'three_pct', 'ft_pct']:
            if player_stats[stat] > target_stats[stat]:
                diff = ((player_stats[stat] - target_stats[stat]) / target_stats[stat]) * 100
                stat_name = stat.replace('_', ' ').replace('pct', '%').upper()
                strengths.append(f"**{stat_name}**: +{diff:.1f}% vs target")
        
        if strengths:
            for strength in strengths[:5]:  # Show top 5
                st.write(f"• {strength}")
        else:
            st.write("No significant statistical advantages identified")
    
    with col2:
        st.subheader("⚠️ Areas for Improvement")
        weaknesses = []
        for stat in ['ppg', 'rpg', 'apg', 'fg_pct', 'three_pct', 'ft_pct']:
            if player_stats[stat] < target_stats[stat]:
                diff = ((target_stats[stat] - player_stats[stat]) / target_stats[stat]) * 100
                stat_name = stat.replace('_', ' ').replace('pct', '%').upper()
                weaknesses.append(f"**{stat_name}**: -{diff:.1f}% vs target")
        
        if weaknesses:
            for weakness in weaknesses[:5]:  # Show top 5
                st.write(f"• {weakness}")
        else:
            st.write("No significant statistical disadvantages identified")
    
    # Shot chart analysis (separate section for single player analysis)
    if st.checkbox("Show Individual Shot Analysis"):
        st.header("🎯 Individual Shot Chart Analysis")
        
        # Get shot chart data for the project player
        player_info = get_player_by_name(project_player)
        if player_info:
            shot_data = get_shot_chart_data(player_info['id'])
            
            if shot_data is not None:
                # Create NBA-style zone chart
                zone_chart = create_nba_style_zone_chart(shot_data, project_player)
                if zone_chart:
                    st.plotly_chart(zone_chart, use_container_width=True)
                
                # Zone efficiency summary
                zone_summary = create_zone_efficiency_summary(shot_data, project_player)
                if zone_summary is not None:
                    st.subheader("📊 Detailed Zone Analysis")
                    st.dataframe(zone_summary, use_container_width=True)
                
                # Shot analysis insights
                shot_analysis = analyze_shot_chart_data(shot_data, project_player)
                if shot_analysis:
                    display_shot_chart_insights(shot_data, project_player)
            else:
                st.warning(f"No shot chart data available for {project_player}")
        else:
            st.error("Could not find player information")
    
    # Add debug info in sidebar
    if st.sidebar.checkbox("Show Debug Info"):
        st.sidebar.subheader("Debug Information")
        st.sidebar.write(f"Cache size: {len(st.session_state.player_cache)} players")
        st.sidebar.write(f"Total available players: {len(available_players)}")
        st.sidebar.write(f"Displayed players: {len(available_players_list)}")
        
        if search_term:
            st.sidebar.write(f"Search results: {len([p for p in available_players if search_term.lower() in p.lower()])}")
        
        # Show API status
        if len(available_players) > len(FALLBACK_PLAYERS):
            st.sidebar.success("✅ NBA API Connected")
        else:
            st.sidebar.error("❌ Using Fallback Data")
            
        if st.sidebar.button("Clear Cache"):
            st.session_state.player_cache = {}
            st.session_state.available_players = []
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.sidebar.success("Cache cleared!")
            st.rerun()
            
        if st.sidebar.button("Reload Players"):
            st.session_state.available_players = []
            st.rerun()

if __name__ == "__main__":
    main()
