"""
MLB API Tools for the MLB Analytics Agent

This module provides custom functions for accessing MLB Stats API data
including player stats, team information, and visual assets.
"""

import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Base URL for MLB Stats API
MLB_API_BASE = "https://statsapi.mlb.com"

# Helper function for API calls
def _make_api_call(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make an API call with error handling."""
    try:
        response = requests.get(
            f"{MLB_API_BASE}{endpoint}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed for {endpoint}: {e}")
        return {"error": f"API call failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {e}")
        return {"error": f"Unexpected error: {str(e)}"}

# Search Functions

def search_player(name: str, only_active: bool = True) -> Dict[str, Any]:
    """
    Search for players by name using the MLB Stats API.

    Args:
        name: Player name to search for (e.g., "Aaron Judge")
        only_active: If True, filter results to only active players

    Returns:
        Dict containing list of matching players with IDs and useful info
    """
    data = _make_api_call(
        "/api/v1/people/search",
        params={"names": name}
    )

    if "error" in data:
        return data

    players = []
    for person in data.get("people", []):
        if only_active and not person.get("active", False):
            continue

        players.append({
            "id": person["id"],
            "full_name": person.get("fullName"),
            "position": person.get("primaryPosition", {}).get("name", "Unknown"),
            "position_abbr": person.get("primaryPosition", {}).get("abbreviation", ""),
            "team": person.get("currentTeam", {}).get("name", "Free Agent"),
            "team_id": person.get("currentTeam", {}).get("id"),
            "jersey_number": person.get("primaryNumber", ""),
            "birth_date": person.get("birthDate"),
            "age": person.get("currentAge"),
            "height": person.get("height"),
            "weight": person.get("weight"),
            "bat_side": person.get("batSide", {}).get("description", "Unknown"),
            "throw_hand": person.get("pitchHand", {}).get("description", "Unknown"),
            "nickname": person.get("nickName"),
            "is_player": person.get("isPlayer", False),
            "is_verified": person.get("isVerified", False),
            "mlb_debut": person.get("mlbDebutDate")
        })

    return {
        "found": len(players),
        "players": players,
        "search_term": name,
        "active_only": only_active
    }


def search_team(name: str) -> Dict[str, Any]:
    """
    Search for MLB teams by name, city, abbreviation, or location.

    Args:
        name: Team name, city, or abbreviation to search for

    Returns:
        Dict containing list of matching teams with their details
    """
    data = _make_api_call(
        "/api/v1/teams",
        params={"sportId": 1, "activeStatus": "ACTIVE"}
    )

    if "error" in data:
        return data

    search_term = name.strip().lower()
    matches = []

    for team in data.get("teams", []):
        match_field = None
        fields = {
            "name": team.get("name", ""),
            "team_name": team.get("teamName", ""),
            "abbreviation": team.get("abbreviation", ""),
            "location": team.get("locationName", ""),
            "short_name": team.get("shortName", ""),
            "franchise_name": team.get("franchiseName", "")
        }

        for field_name, field_value in fields.items():
            if search_term in field_value.lower():
                match_field = field_name
                break

        if match_field:
            matches.append({
                "id": team["id"],
                "name": team["name"],
                "team_name": team["teamName"],
                "abbreviation": team["abbreviation"],
                "location": team["locationName"],
                "short_name": team.get("shortName", ""),
                "franchise_name": team.get("franchiseName", ""),
                "first_year": team.get("firstYearOfPlay", ""),
                "venue": team.get("venue", {}).get("name", ""),
                "league": team.get("league", {}).get("name", ""),
                "division": team.get("division", {}).get("name", ""),
                "match_field": match_field
            })

    return {
        "found": len(matches),
        "teams": matches,
        "search_term": name
    }


# Player Data Functions

from typing import List, Dict, Any
from datetime import datetime

def get_player_stats(
    player_id: int,
    include: List[str] = ["season", "career", "recent"],
    groups: List[str] = ["hitting", "pitching"],
    include_raw: bool = False
) -> Dict[str, Any]:
    """
    Get player statistics using MLB StatsAPI hydration.

    Args:
        player_id: MLB player ID.
        include: List of stat types to include: "season", "career", "recent".
        groups: List of stat groups to include: "hitting", "pitching".
        include_raw: If True, includes raw hydration payload in result.

    Returns:
        A dictionary of stats and metadata.
    """
    current_year = datetime.now().year

    # Prepare hydrations
    hydrations = ["currentTeam"]
    stat_types = []
    if "season" in include:
        stat_types.append("season")
    if "career" in include:
        stat_types.append("career")
    if "recent" in include:
        stat_types.append("last10Games")

    if stat_types:
        hydrations.append(
            f"stats(group=[{','.join(groups)}],type=[{','.join(stat_types)}],season={current_year})"
        )

    # API call
    data = _make_api_call(
        f"/api/v1/people/{player_id}",
        params={"hydrate": ",".join(hydrations)}
    )

    if "error" in data:
        return data
    if not data.get("people"):
        return {"error": f"Player with ID {player_id} not found"}

    player = data["people"][0]

    result = {
        "player_id": player_id,
        "full_name": player.get("fullName", "Unknown"),
        "team": player.get("currentTeam", {}).get("name", "Free Agent"),
        "team_id": player.get("currentTeam", {}).get("id"),
        "position": player.get("primaryPosition", {}).get("abbreviation", ""),
        "position_full": player.get("primaryPosition", {}).get("name", ""),
        "jersey_number": player.get("primaryNumber", ""),
        "stats": {
            "season": {},
            "career": {},
            "recent": {}
        },
        "stat_source": "MLB StatsAPI"
    }

    def _parse_stat_block(stat_group: Dict[str, Any]) -> None:
        stat_type = stat_group.get("type", {}).get("displayName", "").lower()
        group_name = stat_group.get("group", {}).get("displayName", "").lower()
        splits = stat_group.get("splits", [])

        if not splits or stat_type not in include or group_name not in groups:
            return

        stats = splits[0].get("stat", {})
        summary = {}

        # Dynamically select core stats based on group
        if group_name == "hitting":
            summary = {
                "avg": stats.get("avg", ".000"),
                "ops": stats.get("ops", ".000"),
                "home_runs": stats.get("homeRuns", 0),
                "rbi": stats.get("rbi", 0),
                "hits": stats.get("hits", 0),
                "stolen_bases": stats.get("stolenBases", 0),
                "games": stats.get("gamesPlayed", 0)
            }
        elif group_name == "pitching":
            summary = {
                "era": stats.get("era", "0.00"),
                "whip": stats.get("whip", "0.00"),
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "saves": stats.get("saves", 0),
                "strikeouts": stats.get("strikeOuts", 0),
                "innings": stats.get("inningsPitched", "0.0")
            }

        if summary:
            result["stats"][stat_type][group_name] = summary

    # Parse all stat groups
    for stat_group in player.get("stats", []):
        _parse_stat_block(stat_group)

    # Optionally return the raw payload for agent debugging/logging
    if include_raw:
        result["raw"] = data

    return result


# NOTE: get_player_headshot() was removed due to MLB deprecating direct access to player headshots.
# See: https://img.mlbstatic.com/mlb-photos/ and https://content.mlb.com/


# Team Data Functions

def get_team_info(team_id: int) -> Dict[str, Any]:
    """
    Get comprehensive team information including metadata, standings,
    recent performance, and current season hitting stats.

    Args:
        team_id: MLB team ID

    Returns:
        Dict containing team details, standings, recent form, and stats
    """
    current_year = datetime.now().year
    result = {"team_id": team_id}

    # --- 1. Get basic team metadata ---
    team_data = _make_api_call(f"/api/v1/teams/{team_id}")
    if "error" in team_data:
        return team_data
    if not team_data.get("teams"):
        return {"error": f"Team with ID {team_id} not found"}

    team = team_data["teams"][0]
    result.update({
        "name": team.get("name", "Unknown"),
        "team_name": team.get("teamName", ""),
        "abbreviation": team.get("abbreviation", ""),
        "location": team.get("locationName", ""),
        "league": team.get("league", {}).get("name", ""),
        "league_id": team.get("league", {}).get("id"),
        "division": team.get("division", {}).get("name", ""),
        "division_id": team.get("division", {}).get("id"),
        "venue": team.get("venue", {}).get("name", ""),
        "established": team.get("firstYearOfPlay", "")
    })

    # --- 2. Get standings and recent performance ---
    standings_data = _make_api_call(
        "/api/v1/standings",
        params={
            "leagueId": team.get("league", {}).get("id"),
            "season": current_year,
            "standingsTypes": "regularSeason",
            "hydrate": "team"
        }
    )

    standings = {}
    recent_form = {}

    if "error" not in standings_data:
        for record in standings_data.get("records", []):
            for team_record in record.get("teamRecords", []):
                if team_record.get("team", {}).get("id") == team_id:
                    standings = {
                        "wins": team_record.get("wins", 0),
                        "losses": team_record.get("losses", 0),
                        "pct": team_record.get("winningPercentage", ".000"),
                        "division_rank": team_record.get("divisionRank", "?"),
                        "league_rank": team_record.get("leagueRank", "?"),
                        "games_back": team_record.get("gamesBack", "?")
                    }

                    # Try to extract last 10 games if available
                    for split in team_record.get("records", {}).get("splitRecords", []):
                        if split.get("type") == "lastTen":
                            recent_form = {
                                "last_10_wins": split.get("wins", 0),
                                "last_10_losses": split.get("losses", 0),
                                "last_10_pct": split.get("pct", ".000")
                            }

                    break

    result["standings"] = standings
    result["recent_form"] = recent_form

    # --- 3. Get current season hitting stats ---
    stat_data = _make_api_call(
        "/api/v1/teams/stats",
        params={
            "teamId": team_id,
            "stats": "season",
            "group": "hitting"
        }
    )

    if "error" in stat_data:
        result["stats"] = {"error": "Could not fetch stats"}
    else:
        splits = stat_data.get("stats", [{}])[0].get("splits", [])
        if splits:
            stats = splits[0].get("stat", {})
            result["stats"] = {
                "avg": stats.get("avg", ".000"),
                "home_runs": stats.get("homeRuns", 0),
                "runs": stats.get("runs", 0),
                "hits": stats.get("hits", 0),
                "ops": stats.get("ops", ".000"),
                "games_played": stats.get("gamesPlayed", 0)
            }

    return result



def get_team_roster(team_id: int) -> Dict[str, Any]:
    """
    Get current active roster for a team.
    
    Args:
        team_id: MLB team ID
        
    Returns:
        Dict containing roster organized by position type
    """
    data = _make_api_call(f"/api/v1/teams/{team_id}/roster/active")
    
    if "error" in data:
        return data
    
    roster = {
        "team_id": team_id,
        "pitchers": [],
        "catchers": [],
        "infielders": [],
        "outfielders": [],
        "designated_hitters": [],
        "total": 0
    }
    
    for player in data.get("roster", []):
        player_info = {
            "id": player["person"]["id"],
            "name": player["person"]["fullName"],
            "jersey": player.get("jerseyNumber", ""),
            "position": player["position"]["abbreviation"]
        }
        
        position_type = player["position"]["type"]
        if position_type == "Pitcher":
            roster["pitchers"].append(player_info)
        elif position_type == "Catcher":
            roster["catchers"].append(player_info)
        elif position_type == "Infielder":
            roster["infielders"].append(player_info)
        elif position_type == "Outfielder":
            roster["outfielders"].append(player_info)
        elif position_type == "Hitter":
            roster["designated_hitters"].append(player_info)
        elif player["position"]["abbreviation"] == "DH":
            roster["designated_hitters"].append(player_info)
        else:
            roster.setdefault("other", []).append(player_info)

        for key in ["pitchers", "catchers", "infielders", "outfielders", "designated_hitters"]:
            roster[key].sort(key=lambda x: int(x["jersey"]) if x["jersey"].isdigit() else 999)

    
    roster["total"] = len(data.get("roster", []))
    
    return roster

def get_team_logo(team_id: int, style: str = "light") -> Dict[str, str]:
    """
    Get team logo URLs in various formats.
    
    Args:
        team_id: MLB team ID
        style: "light" or "dark" background
        
    Returns:
        Dict containing URLs and formatted images
    """
    logos = {
        "light": f"https://www.mlbstatic.com/team-logos/team-cap-on-light/{team_id}.svg",
        "dark": f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg",
        "primary": f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    }
    
    logo_url = logos.get(style, logos["light"])
    
    return {
        "url": logo_url,
        "markdown": f"![Team Logo]({logo_url})",
        "markdown_inline": f'<img src="{logo_url}" alt="Team" style="width:30px;height:30px;vertical-align:middle;margin:0 5px;">',
        "html": f'<img src="{logo_url}" alt="Team logo" width="30" height="30">',
        "all_styles": logos
    }

# At the end of mlb_tools.py, replace or add after __all__:

def get_all_tools():
    """
    Returns a list of all MLB API tools for easy integration with agents.
    
    Returns:
        List of all tool functions
    """
    return [
        search_player,
        search_team,
        get_player_stats,
        get_team_info,
        get_team_roster,
        get_team_logo
    ]

# Keep __all__ for standard Python imports
__all__ = [
    "search_player",
    "search_team",
    "get_player_stats",
    "get_team_info",
    "get_team_roster",
    "get_team_logo",
    "get_all_tools"  # Add this to exports
]

if __name__ == "__main__":
    print("🧪 Testing MLB API Tools...")
    print("=" * 50)

    # Test 1: Search for a player
    print("\n1. 🔍 Testing player search...")
    player_result = search_player("Aaron Judge")
    found = player_result.get("found", 0)
    print(f"   Found {found} players")

    if found > 0:
        player = player_result["players"][0]
        player_id = player["id"]
        print(f"   ✅ First result: {player['full_name']} - {player['position']} ({player['team']})")

        # Test 2: Get player stats (current season only)
        print("\n2. 📊 Testing player stats (current season only)...")
        stats = get_player_stats(player_id, include=["season"])

        if "error" in stats:
            print(f"   ❌ Error: {stats['error']}")
        else:
            print(f"   ✅ Player: {stats['full_name']} ({stats['team']})")

            hitting = stats.get("stats", {}).get("season", {}).get("hitting", {})
            if hitting:
                print(f"   ⚾ 2025 Hitting: AVG: {hitting.get('avg')}, HR: {hitting.get('home_runs')}, RBI: {hitting.get('rbi')}")
            else:
                print("   ⚠️ No hitting stats found")

    else:
        print("   ❌ No player found, skipping stat test")
    
    # Test 3: Search for a team
    print("\n3. Testing team search...")
    team_result = search_team("Yankees")
    found_teams = team_result.get("found", 0)
    print(f"   Found {found_teams} teams")

    if found_teams > 0:
        team = team_result["teams"][0]
        print(f"   ✅ First result: {team['name']}/{team['id']} ({team['abbreviation']}) - {team['league']}/{team['division']}")
    else:
        print("   ❌ No teams found")
    

    # Test 4: Get team info and stats
    print("\n4. Testing team info for New York Yankees (team_id=147)...")
    team_info = get_team_info(147)

    if "error" in team_info:
        print(f"   Error: {team_info['error']}")
    else:
        print(f"   Team: {team_info['name']} ({team_info['abbreviation']}) - {team_info['league']} / {team_info['division']}")
        if "standings" in team_info:
            s = team_info["standings"]
            print(f"   Standings: {s['wins']}-{s['losses']} ({s['pct']}) GB: {s['games_back']}")
        else:
            print("   No standings data found.")

        if "stats" in team_info:
            st = team_info["stats"]
            print(f"   2025 Stats: AVG: {st.get('avg')}, HR: {st.get('home_runs')}, OPS: {st.get('ops')}")
        else:
            print("   No team stats found.")

    # Test 5: Get team roster
    print("\n5. Testing team roster for New York Yankees (team_id=147)...")
    roster = get_team_roster(147)
    
    if "error" in roster:
        print(f"   Error: {roster['error']}")
    else:
        print(f"   Total players: {roster['total']}")
        for group in ["pitchers", "catchers", "infielders", "outfielders", "designated_hitters"]:
            players = roster.get(group, [])
            if players:
                print(f"   {group.capitalize()}: {len(players)} players")
                for p in players[:3]:  # Show up to 3 sample players per group
                    print(f"     - #{p['jersey']} {p['name']} ({p['position']})")

    # Test 6: Get team logo for Yankees
    print("\n6. Testing get_team_logo for New York Yankees (team_id=147)...")
    logo = get_team_logo(147, style="light")
    print(f"   Logo URL: {logo['url']}")
    print(f"   Markdown: {logo['markdown']}")
    print(f"   HTML tag: {logo['html']}")
