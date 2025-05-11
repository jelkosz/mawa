def get_users(league: str) -> dict:
    """Retrieves the list of all users per league.

        Args:
            league (str): The name of the league (e.g., "Brno", "Hradec").

        Returns:
            dict: A dictionary containing a 'status' key ('success' or 'error') and a list of users.
                  If the status is 'success', includes a list of users in a form of: {"id": "user id", "name": "user name", "score": 123}
                  If 'error', includes an 'error_message' key.
        """
    league_normalized = league.lower().replace(" ", "")
    mock_users_data = {
        "brno": [
            {"id": "id1", "name": "User One", "score": 1234},
            {"id": "id2", "name": "Other User", "score": 82},
            {"id": "id3", "name": "Player Three", "score": 187},
        ],
        "hradec": [
            {"id": "id4", "name": "Other Name", "score": 1234},
            {"id": "id5", "name": "Yet Another", "score": 1234},
        ]
    }

    if league_normalized in mock_users_data:
        return {"status": "success", "users": mock_users_data[league_normalized]}
    else:
        return {"status": "error", "error_message": f"No league information for the league: '{league}'"}

def add_game(league: str, score: int) -> bool:
    """Adds a new game to the list of games.

        Args:
            league (str): The name of the league (e.g., "Brno", "Hradec").
            score (int): The score to store

        Returns:
            bool: True if success, False if failed
        """
    league_normalized = league.lower().replace(" ", "")
    print(f"storing: {score} to league: {league_normalized}")
    return True
