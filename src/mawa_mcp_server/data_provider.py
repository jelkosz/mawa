from mcp.server.fastmcp import FastMCP
import uuid
import json
import os

mcp = FastMCP("Mawa Data Provider")
DATA_FILE = "/tmp/matches_data.json"

def load_data():
    """Loads the data from the JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        # Initialize with mock data if the file doesn't exist
        mock_matches_data = {
            "brno": [
                {
                    "id": "match_id1",
                    "player1": "Jahodovy Knedlik",
                    "player1_score": 15,
                    "player2": "Nakladany Hermelin",
                    "player2_score": 10,
                },
                {
                    "id": "match_id2",
                    "player1": "Tom",
                    "player1_score": 0,
                    "player2": "Hovezi Gulas",
                    "player2_score": 9,
                },
                {
                    "id": "match_id3",
                    "player1": "Tom",
                    "player1_score": 1,
                    "player2": "Nakladany Hermelin",
                    "player2_score": 9,
                },
            ],
            "hradec": [
                {
                    "id": "match_id3",
                    "player1": "Rizek",
                    "player1_score": 10,
                    "player2": "Kachna",
                    "player2_score": 4,
                },
                {
                    "id": "match_id4",
                    "player1": "Salam",
                    "player1_score": 10,
                    "player2": "Kachna",
                    "player2_score": 9,
                },
            ]
        }
        with open(DATA_FILE, "w") as f:
            json.dump(mock_matches_data, f, indent=4)
        return mock_matches_data

def save_data(data):
    """Saves the data to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@mcp.tool()
def get_matches(league: str) -> dict:
    """Retrieves the list of matches per league.

        Args:
            league (str): The name of the league (e.g., "Brno", "Hradec").

        Returns:
            dict: A dictionary containing a 'status' key ('success' or 'error') and a list of matches.
                If the status is 'success', includes a list of games in a form of:
                {
                    "id": "match_id3",
                    "player1": "Rizek",
                    "player1_score": 10,
                    "player2": "Kachna",
                    "player2_score": 4,
                }
                Each match is always held between two players marked as player1 and player1 in the output.
                The playerN_score means how many times the particular player scored in the game.

                If 'error', includes an 'error_message' key.
    """
    matches_data = load_data()
    league_normalized = league.lower().replace(" ", "")

    if league_normalized in matches_data:
        return {"status": "success", "users": matches_data[league_normalized]}
    else:
        return {"status": "error", "error_message": f"No league information for the league: '{league}'"}

@mcp.tool()
def add_match(league: str, player1: str, player1_score: int, player2: str, player2_score: int) -> dict:
    """Adds a new game to the list of games.

        Args:
            league (str): The name of the league (e.g., "Brno", "Hradec").
            player1 (str): The name of the player1
            player1_score (int): How many times the player1 scored in this game
            player2 (str): The name of the player2
            player2_score (int): How many times the player2 scored in this game

        Returns:
            dict: A dictionary containing a 'status' key ('success' or 'error') and an optional error_message.
            If the status is "success", the response looks like this:
             {"status": "success"}
            If the status is "error", the response looks like this:
             {"status": "success", "error_message": "Unknown league."}
    """
    matches_data = load_data()
    league_normalized = league.lower().replace(" ", "")
    if league_normalized in matches_data:
        matches_data[league_normalized].append(
            {
                "id": str(uuid.uuid4()),
                "player1": player1,
                "player1_score": player1_score,
                "player2": player2,
                "player2_score": player2_score,
            }
        )
        save_data(matches_data)
        return {"status": "success"}
    else:
        return {"status": "error", "error_message": f"No league information for the league: '{league}'"}