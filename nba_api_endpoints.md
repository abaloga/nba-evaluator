# NBA API Available Endpoints

## Core Player Data Endpoints

### 1. **Player Career Stats**
```python
from nba_api.stats.endpoints import playercareerstats
playercareerstats.PlayerCareerStats(player_id=player_id)
```
**Data:** Career totals, season-by-season breakdowns, playoff stats

### 2. **Player Profile**
```python
from nba_api.stats.endpoints import playerprofilev2
playerprofilev2.PlayerProfileV2(player_id=player_id)
```
**Data:** Season highlights, career highlights, next game info

### 3. **League Dashboard Player Stats**
```python
from nba_api.stats.endpoints import leaguedashplayerstats
leaguedashplayerstats.LeagueDashPlayerStats(season='2023-24')
```
**Data:** All active players' current season stats, sortable

### 4. **Player Dashboard by General Splits**
```python
from nba_api.stats.endpoints import playerdashboardbygeneralsplits
playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(player_id=player_id)
```
**Data:** Overall, location (home/away), wins/losses, pre/post all-star

### 5. **Player Dashboard by Opponent**
```python
from nba_api.stats.endpoints import playerdashboardbyopponent
playerdashboardbyopponent.PlayerDashboardByOpponent(player_id=player_id)
```
**Data:** Performance vs each NBA team

## Advanced Shooting Data

### 6. **Shot Chart Detail**
```python
from nba_api.stats.endpoints import shotchartdetail
shotchartdetail.ShotChartDetail(player_id=player_id, team_id=0, season_nullable='2023-24')
```
**Data:** Every shot attempted with X,Y coordinates, make/miss, distance

### 7. **Player Dashboard by Shooting Splits**
```python
from nba_api.stats.endpoints import playerdashboardbyshootingsplits
playerdashboardbyshootingsplits.PlayerDashboardByShootingSplits(player_id=player_id)
```
**Data:** 
- Shot areas (paint, mid-range, 3PT)
- Assisted vs unassisted
- Shot types (jump shots, layups, dunks)
- Shot clock ranges

### 8. **Player Dashboard by Clutch**
```python
from nba_api.stats.endpoints import playerdashboardbyclutch
playerdashboardbyclutch.PlayerDashboardByClutch(player_id=player_id)
```
**Data:** Performance in clutch time (last 5 min, score within 5)

### 9. **Player Dashboard by Game Splits**
```python
from nba_api.stats.endpoints import playerdashboardbygamesplits
playerdashboardbygamesplits.PlayerDashboardByGameSplits(player_id=player_id)
```
**Data:** By days rest, back-to-back games, game number ranges

## Situational Performance

### 10. **Player Dashboard by Last N Games**
```python
from nba_api.stats.endpoints import playerdashboardbylastnagames
playerdashboardbylastnagames.PlayerDashboardByLastNGames(player_id=player_id)
```
**Data:** Last 5, 10, 15, 20 games performance

### 11. **Player Dashboard by Plus Minus**
```python
from nba_api.stats.endpoints import playerdashboardbyplusminus
playerdashboardbyplusminus.PlayerDashboardByPlusMinus(player_id=player_id)
```
**Data:** Plus/minus splits, on/off court impact

### 12. **Player Dashboard by Team Performance**
```python
from nba_api.stats.endpoints import playerdashboardbyteamperformance
playerdashboardbyteamperformance.PlayerDashboardByTeamPerformance(player_id=player_id)
```
**Data:** Performance in wins vs losses, score differential

### 13. **Player Dashboard by Year Over Year**
```python
from nba_api.stats.endpoints import playerdashboardbyyearoveryear
playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player_id)
```
**Data:** Season comparison, career progression

## Tracking & Advanced Stats

### 14. **Player Tracking Stats**
```python
from nba_api.stats.endpoints import leaguedashptstats
leaguedashptstats.LeagueDashPtStats(player_or_team='Player')
```
**Data:** Speed, distance, touches, drives, catch & shoot

### 15. **Hustle Stats**
```python
from nba_api.stats.endpoints import hustlestatsplayer
hustlestatsplayer.HustleStatsPlayer()
```
**Data:** Deflections, loose balls, charges drawn, screen assists

### 16. **Defense Dashboard**
```python
from nba_api.stats.endpoints import leaguedashptdefend
leaguedashptdefend.LeagueDashPtDefend(defense_category='Overall')
```
**Data:** Defensive impact, opponent FG% when defended

## Specific Stat Categories

### 17. **Rebounds Dashboard**
```python
from nba_api.stats.endpoints import leaguedashplayerptshot
# Part of tracking stats - rebounding data
```
**Data:** Offensive/defensive rebounds, contested rebounds

### 18. **Assists Dashboard**
```python
from nba_api.stats.endpoints import playerdashptpass
playerdashptpass.PlayerDashPtPass(player_id=player_id)
```
**Data:** Passes made, assists, secondary assists, potential assists

### 19. **Usage & Efficiency**
```python
from nba_api.stats.endpoints import playerestimatedmetrics
playerestimatedmetrics.PlayerEstimatedMetrics()
```
**Data:** Usage rate, efficiency metrics, advanced calculations

## Game-Level Data

### 20. **Player Game Log**
```python
from nba_api.stats.endpoints import playergamelog
playergamelog.PlayerGameLog(player_id=player_id, season='2023-24')
```
**Data:** Every game played with full box score

### 21. **Player vs Player**
```python
from nba_api.stats.endpoints import playervsplayer
playervsplayer.PlayerVsPlayer(player_id=player_id, vs_player_id=vs_player_id)
```
**Data:** Head-to-head matchup statistics

## Team Context

### 22. **Team Player Dashboard**
```python
from nba_api.stats.endpoints import teamplayerdashboard
teamplayerdashboard.TeamPlayerDashboard(team_id=team_id)
```
**Data:** All players on a team, their roles and performance

### 23. **Lineups**
```python
from nba_api.stats.endpoints import teamdashlineups
teamdashlineups.TeamDashLineups(team_id=team_id)
```
**Data:** 5-man lineup statistics, on/off court combinations

## Historical & Comparison

### 24. **Career Comparisons**
```python
from nba_api.stats.endpoints import playercompare
playercompare.PlayerCompare(player_id_list=[id1, id2, id3])
```
**Data:** Side-by-side career comparison

### 25. **Awards & Achievements**
```python
from nba_api.stats.endpoints import playerawards
playerawards.PlayerAwards(player_id=player_id)
```
**Data:** All-Star selections, awards, achievements

## Static Data (No API calls needed)

### 26. **All Players List**
```python
from nba_api.stats.static import players
players.get_players()  # All players ever
players.get_active_players()  # Current season only
```

### 27. **Teams List**
```python
from nba_api.stats.static import teams
teams.get_teams()
```

## Usage Examples for Your App

### Most Useful for Player Evaluation:

1. **Basic Stats**: `leaguedashplayerstats` - Current season averages
2. **Shooting Detail**: `playerdashboardbyshootingsplits` - Shot location data
3. **Clutch Performance**: `playerdashboardbyclutch` - High-pressure situations
4. **Efficiency**: `playerestimatedmetrics` - Advanced efficiency metrics
5. **Game-by-Game**: `playergamelog` - Consistency analysis
6. **Defense**: `leaguedashptdefend` - Defensive impact
7. **Tracking**: `leaguedashptstats` - Modern analytics (speed, distance, etc.)

### Rate Limits & Best Practices:
- NBA API has rate limits (~600 requests/10 minutes)
- Cache aggressively (data doesn't change frequently)
- Use `time.sleep(0.6)` between requests
- Handle exceptions gracefully
- Consider using `season_type_all_star='Regular Season'` for current data

### Most Detailed Endpoints for Your Use Case:
1. `playerdashboardbyshootingsplits` - Exact shooting zones
2. `shotchartdetail` - Individual shot data
3. `playerdashboardbygeneralsplits` - Home/away, monthly splits
4. `leaguedashptstats` - Speed, touches, drives data
5. `hustlestatsplayer` - Effort metrics
