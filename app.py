from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
import random
import json
import os

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

# Connect to MongoDB
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

# Read the content of the letters.json file
with open('letters.json', 'r') as file:
    letters_data = json.load(file)

# Extract the letter list and the amount of letters from the JSON data
letter_list = list(letters_data['letters'].keys())
amount_of_letters = sum(item['tiles'] for item in letters_data['letters'].values())

# Function to check if word placement is valid
def is_valid_word_placement(word, row, col, direction, board):
    """Check if word placement is valid."""
    if direction not in ["horizontal", "vertical"]:
        return False  # Invalid direction
    if direction == "horizontal":
        if col + len(word) > 15:
            return False  # Word goes out of bounds
        for i in range(len(word)):
            if board[row][col+i] != ' ':
                return False  # Space already occupied
    elif direction == "vertical":
        if row + len(word) > 15:
            return False  # Word goes out of bounds
        for i in range(len(word)):
            if board[row+i][col] != ' ':
                return False  # Space already occupied
    return True

# Function to update player's deck after placing a word
def update_player_deck(player, word, row, col, direction, board):
    """Update player's deck after placing a word."""
    for i, _ in enumerate(word):
        if player == 'player1':
            if direction == "horizontal":
                board[row][col+i] = 'X'
            elif direction == "vertical":
                board[row+i][col] = 'X'
        else:
            if direction == "horizontal":
                board[row][col+i] = 'O'
            elif direction == "vertical":
                board[row+i][col] = 'O'

# Function to draw random tiles from the bag
def draw_random_tiles(player, num_tiles, letters_bag):
    """Draw random tiles from the bag."""
    tiles_drawn = []
    letters = list(letters_bag.keys())
    for _ in range(num_tiles):
        if letters:
            letter = random.choice(letters)
            tiles_drawn.append(letter)
            letters_bag[letter] -= 1  # Decrement the value
            if letters_bag[letter] == 0:
                del letters_bag[letter]
            letters.remove(letter)
    return tiles_drawn

# Function to calculate scores for each player
def calculate_scores(board):
    """Calculate scores for each player."""
    scores = {"player1": 0, "player2": 0}
    for row in board:
        for letter in row:
            if letter != ' ':
                if letter == 'X':
                    scores["player1"] += 1
                else:
                    scores["player2"] += 1
    return scores

# Function to get player decks
def get_player_decks(board):
    """Get player decks."""
    player_decks = {"player1": {}, "player2": {}}
    for row in board:
        for letter in row:
            if letter != ' ':
                player = "player1" if letter == "X" else "player2"
                if letter not in player_decks[player]:
                    player_decks[player][letter] = 0
                player_decks[player][letter] += 1
    return player_decks

# Example endpoint to place a word on the board
@app.route('/place_word', methods=['POST'])
def place_word():
    """Endpoint to place a word on the board."""
    data = request.json
    word = data.get('word')
    row = data.get('row')
    col = data.get('col')
    direction = data.get('direction')
    player = data.get('player')

    initial_board = [[' ']*15 for _ in range(15)]
    initial_letters_bag = {letter: letters_data['letters'][letter]['tiles'] for letter in letters_data['letters']}
    game_state_collection = {
        "board": initial_board,
        "letters_bag": initial_letters_bag,
        "word": word,
        "row": row,
        "col": col,
        "direction": direction,
        "player": player
    }
    mongo.db.game_state.insert_one(game_state_collection)

    if not all([word, row, col, direction, player]):
        return jsonify({"error": "Missing data"}), 400

    # Fetch the game state from the database
    game_state_collection = mongo.db.game_state.find_one()

    if not game_state_collection:
        return jsonify({"error": "Game state not found"}), 500

    board = game_state_collection.get('board')
    letters_bag_collection = game_state_collection.get('letters_bag')

    # Check if word placement is valid
    if not is_valid_word_placement(word, row, col, direction, board):
        return jsonify({"error": "Invalid word placement"}), 400

    # Place word on the board
    if direction == "horizontal":
        for i, letter in enumerate(word):
            board[row][col+i] = letter
    elif direction == "vertical":
        for i, letter in enumerate(word):
            board[row+i][col] = letter

    # Update player's deck (remove placed letters)
    update_player_deck(player, word, row, col, direction, board)

    # Draw random tiles for the player
    if letters_bag_collection:
        drawn_tiles = draw_random_tiles(player, len(word), letters_bag_collection)
    else:
        drawn_tiles = []
        return jsonify({"error": "Letters bag not found"}), 500

    # Update the game state in the database
    mongo.db.game_state.update_one({}, {"$set": {"board": board}})

    # Update player's data in the database
    player_data = mongo.db.players.find_one() or {
        'player1': {'letters': {}, 'score': 0},
        'player2': {'letters': {}, 'score': 0}
    }
    
    # Update player's letters and scores
    scores = calculate_scores(board)
    player_letters = player_data[player]['letters']
    player_letters[word] = player_letters.get(word, 0) + 1
    player_score = scores[player]
    player_data[player]['letters'] = player_letters
    player_data[player]['score'] = player_score
    
    mongo.db.players.update_one({}, {"$set": player_data}, upsert=True)

    return jsonify({"message": "Word placed successfully", "drawn_tiles": drawn_tiles}), 200


# Example endpoint to get the current game status
@app.route('/game_status', methods=['GET'])
def game_status():
    """Endpoint to get the current game status."""
    # Fetch the game state from the database
    game_state_collection = mongo.db.game_state.find_one()

    if not game_state_collection:
        return jsonify({"error": "Game state not found"}), 500

    board = game_state_collection.get('board')
    letters_bag_collection = game_state_collection.get('letters_bag')

    # Calculate scores for each player
    scores = calculate_scores(board)

    # Count tiles left in the bag
    tiles_left = sum(letters_bag_collection.values()) if letters_bag_collection else 0
    total_tiles_left = tiles_left + amount_of_letters

    # Get player decks
    player_decks = get_player_decks(board)

    return jsonify({
        "scores": scores,
        "total_tiles_left": total_tiles_left,
        "player_decks": player_decks
    }), 200

if __name__ == '__main__':
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)