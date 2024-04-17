### Scrabble Game

This project is a Flask application that allows users to perform certain actions related to a game. You can use this README as a guide to set up the project and run it locally.

##### Prerequisites
Before running the application, make sure you have the following installed on your system:
- Python (version 3.6 or higher)
- Docker (optional, if you want to run the application in a container)

##### Setup Instructions
1. Clone the repository to your local machine:
` git clone <repository_url> `

2. Navigate into the project directory
`  git clone <repository_url> ` 

3. Install dependencies using pip:
`  pip install -r requirements.txt ` 

##### Running the Application
To run the application locally, follow these steps:
1. Start the Flask development server:
`  flask run `

2. The application should now be running at http://localhost:5000.

##### Using Docker
Alternatively, you can run the application using Docker:

1. Build the Docker image:
` docker build -t scrabble-name . `

2. Run the Docker container:
` docker run -p 5000:5000 scrabble-name `

3. The application should now be accessible at http://localhost:5000.

##### Using Postman
To interact with the API endpoints using Postman, follow these steps:
1. Open Postman.
2. Set the request method (GET, POST, etc.) and enter the URL of the endpoint you want to test (e.g., http://localhost:5000/place_word).
3. Add any required headers or request body parameters.
4. Click on the "Send" button to make the request.
5. View the response from the server.

##### API Endpoints
- ` /place_word: ` Endpoint to place a word on the board.
- `/game_status: ` Endpoint to get the current game status.