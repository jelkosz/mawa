# This is THE database.
import uuid

mock_matches_data = {
        "brno": [
            {
                "id": "match_id1",
                "player1": "Jahodovy Knedlik",
                "player1_score": "5",
                "player2": "Nakladany Hermelin",
                "player2_score": "10",
            },
            {
                "id": "match_id2",
                "player1": "Tom",
                "player1_score": "0",
                "player2": "Hovezi Gulas",
                "player2_score": "9",
            },
            {
                "id": "match_id3",
                "player1": "Tom",
                "player1_score": "1",
                "player2": "Nakladany Hermelin",
                "player2_score": "9",
            },
        ],
        "hradec": [
            {
                "id": "match_id3",
                "player1": "Rizek",
                "player1_score": "10",
                "player2": "Kachna",
                "player2_score": "4",
            },
            {
                "id": "match_id4",
                "player1": "Salam",
                "player1_score": "10",
                "player2": "Kachna",
                "player2_score": "9",
            },
        ]
    }

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
                    "player1_score": "10",
                    "player2": "Kachna",
                    "player2_score": "4",
                }
                Each match is always held between two players marked as player1 and player1 in the output.
                The playerN_score means how many times the particular player scored in the game.

                If 'error', includes an 'error_message' key.
        """
    league_normalized = league.lower().replace(" ", "")

    if league_normalized in mock_matches_data:
        return {"status": "success", "users": mock_matches_data[league_normalized]}
    else:
        return {"status": "error", "error_message": f"No league information for the league: '{league}'"}

def add_match(league: str, player1: str, player1_score: int, player2: str, player2_score: int) -> bool:
    """Adds a new game to the list of games.

        Args:
            league (str): The name of the league (e.g., "Brno", "Hradec").
            player1 (str): The name of the player1
            player1_score (str): How many times the player1 scored in this game
            player2 (str): The name of the player2
            player2_score (str): How many times the player2 scored in this game

        Returns:
            bool: True if success, False if failed
        """
    league_normalized = league.lower().replace(" ", "")
    mock_matches_data[league_normalized].append(
        {
            "id": str(uuid.uuid4()),
            "player1": player1,
            "player1_score": player1_score,
            "player2": player2,
            "player2_score": player2_score,
        }
    )
    return True
