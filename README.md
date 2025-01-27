# bidding_application_backend

# Project Title: A simple bidding Application

# Project description

The backend for building a bidding application. The application enables users, in this case, the customers for for a specific product, to view a catalogue of all the products available. Users can then place bids for a given product and the highest bidder wins after the bidding period.
The admin, being the overall overseer of the application, has the rights to add, update, or delete products from the application as well as managing the bidding end time.

## Installation

1. create a folder/directory on a local machine for the project.
2. Clone the repository: git clone [repository URL].
3. Navigate to the project directory: cd your_project-directory.
4. create a virtual environment[pip install && pip shell].
5. Install dependencies:

## Usage

1. initialize database [flask db init]
2. make migrations [flask db migrate -m"initial migrations"]
3. update the database [flask db upgrade head]
4. Seed any data if applicable for development environment [python seed.py]
5. To run the application, export the FLASK_App[export FLASK_APP=app.py]
6. configure port [export FLASK_RUN_PORT=5555]
7. Run the application locally[flask run]
