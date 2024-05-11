"""
Yuli Tshuva
Building a file compression tool using LZW algorithm
"""

# Imports
from struct import *
from flask import Flask, render_template, request, redirect, url_for
import os
from os.path import join
import secrets
import datetime

# Constants setup
# Number of optimal bits for the code
BITS_NUM = 12
# Calculating the maximum table size
MAX_TABLE_SIZE = pow(2, int(BITS_NUM))

# Create an instance of the Flask class, with the name of the running
# application and the paths for the static files and templates
app = Flask(__name__, static_folder='static', template_folder="templates")

# Set the upload folder to the absolute path of the "upload_folder" directory
app.config['UPLOAD_FOLDER'] = os.path.abspath("upload_folder")

# Set the lifetime of a session to one hour
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(hours=1)

# Set the secret key to a random string generated by the secrets module
app.config["SECRET_KEY"] = secrets.token_hex()


def encode(input_file, save_path):
    """
    A function for LZW encoding.
    :param save_path: The path for saving the compressed file
    :param input_file: The path for the input file
    :return: None
    """
    # Opening the input file
    with open(input_file, "r") as file:
        data = file.read()

    # Building and initializing the dictionary
    dictionary_size = 256
    dictionary = {chr(i): i for i in range(dictionary_size)}

    # Setup initial algorithm variables
    string = ""
    compressed_data = []  # variable to store the compressed data

    # Iterating through the input symbols
    for symbol in data:
        # Add the symbol to the string
        string_plus_symbol = string + symbol
        # Check if the string + symbol is in the dictionary
        if string_plus_symbol in dictionary:
            # Reassign the string
            string = string_plus_symbol
        # If not, add the string + symbol to the dictionary
        else:
            compressed_data.append(dictionary[string])
            # Check we didn't reach the maximum table size
            if len(dictionary) <= MAX_TABLE_SIZE:
                dictionary[string_plus_symbol] = dictionary_size
                dictionary_size += 1
            # Reassign the string
            string = symbol

    # Final correction
    if string in dictionary:
        compressed_data.append(dictionary[string])

    # Save the compressed data to a file
    with open(save_path, "wb") as output_file:
        for data in compressed_data:
            output_file.write(pack('>H', int(data)))


def decode(input_file, save_path):
    """
    A function for LZW decoding.
    :param save_path: The path for saving the compressed file
    :param input_file: The path for the input file
    :return: None
    """
    # Setup initial variables
    compressed_data = []
    next_code = 256
    decompressed_data = ""
    string = ""

    # Open the compressed file - binary (since it has been encoded to be binary)
    with open(input_file, "rb") as file:
        # Read the compressed file chunk by chunk
        while True:
            # Read 2 bytes
            rec = file.read(2)
            # Break condition
            if len(rec) != 2:
                break
            # Unpack the 2 bytes to a number
            (data,) = unpack('>H', rec)
            # Add to the data variable
            compressed_data.append(data)

    # Build and initialize the dictionary
    dictionary_size = 256
    dictionary = dict([(x, chr(x)) for x in range(dictionary_size)])

    # Iterate through the codes
    for code in compressed_data:
        # Check if the code isn't in the dictionary
        if not (code in dictionary):
            # Add the string + string[0] to the dictionary
            dictionary[code] = string + (string[0])
        # Add to the decompressed data
        decompressed_data += dictionary[code]
        # Check we didn't just start the loop
        if not (len(string) == 0):
            # Add to dictionary
            dictionary[next_code] = string + (dictionary[code][0])
            next_code += 1
        # Reassign the string
        string = dictionary[code]

    # Save the output to a file
    with open(save_path, "w") as output_file:
        for data in decompressed_data:
            output_file.write(data)


def get_file_size(file_path: str):
    """Get a file path and return file size in bytes."""
    # Check if the file exists
    if not os.path.isfile(file_path):
        print("File not found:", file_path)
        return None

    # Get the size of the file
    file_size = os.path.getsize(file_path)

    return file_size


@app.route("/", methods=["GET"])
@app.route("/Home", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/Example", methods=["GET"])
def example():
    return render_template("example.html")


@app.route("/About", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/process_form", methods=["POST", "GET"])
def process_form():
    try:
        # Get the requested action
        action = request.form["action"]

        if action == "None":
            return render_template("index.html", error="Please choose an action")

        # Get the posted file
        file = request.files["file"]

        # Check if the file is empty
        if file.filename == "":
            return render_template("index.html", error="Please choose a file")

        if action == "Encode" and file.filename.split(".")[-1] == "lzw":
            return render_template("index.html", error="The file is already compressed.")
        if action == "Decode" and file.filename.split(".")[-1] == "txt":
            return render_template("index.html", error="The file is already decompressed.")

        # Save the file
        save_path = join("static", file.filename)
        file.save(save_path)

        # Check if the file is empty
        if os.stat(save_path).st_size == 0:
            return render_template("index.html", error="The file is empty")

        # Extract the file name without the extension
        name_without_extension = file.filename.split(".")[0]

        # Encode/Decode the file

        if action == "Encode":
            success = "Encoded successfully!"
            output_name = name_without_extension + "_compressed.lzw"
            output_path = join("static", output_name)
            encode(input_file=save_path, save_path=output_path)

        if action == "Decode":
            success = "Decoded successfully!"
            output_name = name_without_extension + "_decompressed.txt"
            output_path = join("static", output_name)
            decode(input_file=save_path, save_path=output_path)

        # Calculate the files sizes
        input_size = get_file_size(save_path)
        output_size = get_file_size(output_path)

        return render_template("index.html", output_path=output_path, output_name=output_name,
                               success=success, input_size=input_size, output_size=output_size)
    except Exception as e:
        return render_template("index.html", error=f"The following error occurred: {e}.")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
