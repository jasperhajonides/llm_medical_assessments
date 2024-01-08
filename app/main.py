# Importing necessary libraries
import dash
import os
import sys
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import Dash, html, dcc, Output, Input, State, callback
import dash_bootstrap_components as dbc
import base64
import dash_table
import threading


## llama index functions
import logging

from llama_index import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms import LlamaCPP
from llama_index.llms.llama_utils import messages_to_prompt, completion_to_prompt
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index import ServiceContext
from llama_index.embeddings import LangchainEmbedding

## other custom functions
from functions.styling_functions import get_button_style
from functions.medical_assessment import run_assessment


# Global variable, this is what we will use to answer all our questions.
global query_engine
query_engine = None

# results will be written to
temp_csv = "temp_results.csv"


# Create a Dash application
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        # Store component to keep track of the model state
        dcc.Store(id="model-ready", storage_type="memory"),
        # first part of the page:

        html.Div(
            [
                html.H1("Assessment of Recommended Procedure", style={
                    "textAlign": "center", 
                    "fontSize": "68px",
                    "color": "#005073",  # Darker shade of blue
                    "fontFamily": "'Segoe UI', sans-serif",  # Modern font
                }),
                html.P(
                    "The first step is to select your pdf and we will assess the recommended procedure. "
                    "A .pdf file needs to be present before loading your model.",
                    style={
                        "textAlign": "center",
                        "fontFamily": "'Segoe UI', sans-serif",
                    },
                ),
                dcc.Upload(
                    id="upload-file",
                    children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px",
                    },
                    # Allow multiple files to be uploaded
                    multiple=False,
                ),
                html.Div(id="output-upload"),
            ],
            style={"width": "80%", "margin": "auto", "padding": "20px"},
        ),  # Container styling for the first part of the page
        # New section for 'Initialise llama index'
        html.Div(
            [
                html.H2("Initialise llama index", style={
                    "textAlign": "center", 
                    "fontSize": "32px",
                    "color": "#005073",  # Darker shade of blue
                    "fontFamily": "'Segoe UI', sans-serif",  # Modern font
                }),
                html.P("""Press to initialise llama-index with Mistral 7B quantised instruct mode and GTE-large (thenlper/gte-large) for the embeddings. 
                       These models will be used to query the relevant parts of data from the documents."""),
                html.P("""We will sometimes run the query multiple times because the model is not deterministic and 
                       re-running it will get rid of some string formatting issues we may otherwise encouter in this approach.
                       We'll use the multi-iteration approach as a confidence metric. """),
                html.P("""When you're ready you can press 'Load Model',
                        if you run it for the first time it may need to download the models which takes a little while. 
                       (See terminal for progress in this case.)"""),
                       
                html.P("""Also note that the models run on CPU only due to time constraints for this exercise. """),
                html.Button(
                    "Load Model",
                    id="load-model-button",
                    n_clicks=0,
                    style=get_button_style("grey"),
                ),
                html.Div(id="button-output"),
                # Interval component for periodic checks
                dcc.Interval(
                    id="interval-component",
                    interval=1 * 1000,
                    n_intervals=0,
                    disabled=True,
                ),
                # print the status of hte medical report assessment
                html.Div(
                    id="status-display",
                    style={
                        "height": "360px",
                        "background-color": "#d4f1f9",  # Very light blue
                        "font-family": "'Courier New', monospace",
                        "text-align": "left",
                        "display": "flex",
                        "justify-content": "center",
                        "align-items": "center",
                        "padding": "20px",
                        "border-radius": "10px",  # Rounded corners
                        "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",  # Box shadow for depth
                    },
                ),
                # Table to display results
                dash_table.DataTable(
                    id="results-table",
                    columns=[
                        {"name": "Description", "id": "desc"},
                        {"name": "Confidence", "id": "confidence"},
                        {"name": "Output", "id": "output"},
                    ],
                    data=[],
                ),
            ],
            style={"width": "80%", "margin": "auto"},
        ), 
    ],
    style={
        "textAlign": "center",
        "fontFamily": "'Segoe UI', sans-serif",  # Apply this font to the whole page
    },
)  


##### now define the callbacks #####
@app.callback(
    Output("output-upload", "children"),
    Input("upload-file", "filename"),
    Input("upload-file", "contents"),
)
def update_output(uploaded_filename, uploaded_file_contents):
    """ define the dropzone callback function"""
    if uploaded_filename is None or uploaded_file_contents is None:
        raise PreventUpdate

    # Check if the file is a PDF
    if not uploaded_filename.lower().endswith(".pdf"):
        return "File is not a PDF. Please upload a PDF file."

    # Clear existing files in ./app/data
    folder = "./app/data"
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)

    # Decode and save the uploaded PDF file
    content_type, content_string = uploaded_file_contents.split(",")
    decoded = base64.b64decode(content_string)
    file_path = os.path.join(folder, uploaded_filename)
    with open(file_path, "wb") as f:
        f.write(decoded)

    return "Upload completed!"


@app.callback(
    Output("model-ready", "data"),
    Output("load-model-button", "children"),
    Output("load-model-button", "style"),
    Output("button-output", "children"),
    Input("load-model-button", "n_clicks"),
    prevent_initial_call=True,
)
def load_model(n_clicks):
    """ 
    When the load-model button is pressed we remove any previous data from the table and start
    the new model.
    """
    global query_engine
    if n_clicks > 0:
        # Check if temp_results.csv exists, and delete it if it does
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

        try:
            # Configure logging
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
            logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

            # Load documents
            documents = SimpleDirectoryReader("./app/data/").load_data()

            # Initialize the LlamaCPP model
            llm = LlamaCPP(
                model_url="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
                model_path=None,
                temperature=0.1,
                max_new_tokens=256,
                context_window=3900,
                generate_kwargs={},
                model_kwargs={"n_gpu_layers": -1},
                messages_to_prompt=messages_to_prompt,
                completion_to_prompt=completion_to_prompt,
                verbose=True,
            )

            # Initialize the embedding model
            embed_model = LangchainEmbedding(
                HuggingFaceEmbeddings(model_name="thenlper/gte-large")
            )

            # Set up the service context
            service_context = ServiceContext.from_defaults(
                chunk_size=1024, llm=llm, embed_model=embed_model
            )

            # Create an index from documents
            index = VectorStoreIndex.from_documents(
                documents, service_context=service_context
            )

            # Create a query engine
            query_engine = index.as_query_engine()

            return True, "Model Loaded", get_button_style("green"), ""
        except Exception as e:
            return False, "Loading Failed", get_button_style("red"), str(e)

    raise PreventUpdate


# Callback to update the interval component
@app.callback(
    Output("interval-component", "disabled"),
    Input("model-ready", "data"),
)
def update_interval(model_ready):
    if model_ready:
        thread = threading.Thread(target=run_assessment, args=(query_engine, temp_csv))
        thread.daemon = True
        thread.start()
    return not model_ready


# Callback to update the table
@app.callback(
    Output("results-table", "data"), Input("interval-component", "n_intervals")
)
def update_table(n_intervals):
    if os.path.exists(temp_csv):
        df = pd.read_csv(temp_csv)
        return df.to_dict("records")
    return []


# Callback to update the status display
@app.callback(
    Output("status-display", "children"), Input("interval-component", "n_intervals")
)
def update_status(n_intervals):
    if os.path.exists("status.txt"):
        with open("status.txt", "r") as file:
            status = file.read()
            # Use html.Pre to preserve the formatting with new line characters
            return html.Pre(status, style={"white-space": "pre-wrap"})
    return "No status update"


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=80)
