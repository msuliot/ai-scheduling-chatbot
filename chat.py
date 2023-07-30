# import necessary libraries
import openai as ai
import gradio as gr
import Helper as hp
import copy as cp
import json

# get API key from .env file
import os
from dotenv import load_dotenv
load_dotenv()
ai.api_key = os.getenv('OPENAI_API_KEY')

# set path to database file
database = "data/data.json"

# function to determine which step of the chatbot to take
def chat_step(prompt_address,prompt_question,prompt_request):
    p1 = len(prompt_address.strip()) > 0
    p2 = len(prompt_question.strip()) > 0
    p3 = len(prompt_request.strip()) > 0

    if p1 and p2 and p3:
        return "bookit"
    elif p1 and p2:
        return "question"
    elif p1:
        return "address"
    else:
        return None

# function to handle the "address" step of the chatbot
def step_address(prompt_address):
    result = hp.query_database_by_address(database,prompt_address)
    if result:
        return "Listing found:\nAddress: " + result["address"] + "\nPrice: " + result["price"] + "\nContact: " + result["contact"] + "\n\nHow can I help?"
    else:
        return "Listing not found."

# function to handle the "question" step of the chatbot
def step_question(prompt_address, prompt_question):
    messages = []

    result = hp.query_database_by_address(database, prompt_address)
    
    # Read the JSON data from the file
    data_dict = result["showings"]

    # create system prompt
    system_prompt = hp.create_system_prompt()
    messages = hp.add_prompt_messages("system", system_prompt , messages)
    
    # create user prompt
    user_prompt = hp.create_user_prompt(prompt_question,data_dict)
    messages = hp.add_prompt_messages("user", user_prompt , messages)
    response = hp.get_chat_completion_messages(messages) 
    return response

# function to handle the "bookit" step of the chatbot
def step_bookit(prompt_address,prompt_question,prompt_request):
    if prompt_request != "yes":
        return "Okay, let me know if you change your mind."
    
    messages = []
    # create system prompt
    system_prompt = hp.create_system_prompt()
    messages = hp.add_prompt_messages("system", system_prompt , messages)

    sidebar_prompt = hp.create_user_prompt_break_down(prompt_question + prompt_address)
    messages = hp.add_prompt_messages("user", sidebar_prompt , messages)
    response_sidebar = hp.get_chat_completion_messages(messages) 

    data = json.loads(response_sidebar)

    new_start = str(hp.parse_date(data["date"])) + " " + str(hp.parse_time(data["time"]))
    new_end = str(hp.parse_date(data["date"])) + " " + str(hp.format_end_time(data))

    data = hp.query_database_by_file(database)

    success, data = hp.append_showing(data, prompt_address, new_start, new_end)

    if success:
        hp.save_data(data, database)
        return f"New showing added successfully!\n\nAddress: {prompt_address}\nStart: {new_start}\nEnd: {new_end}"
    else:
         return "Address not found, new showing not added." 

# main function to start the chatbot
def start(prompt_address,prompt_question,prompt_request):
    chat = chat_step(prompt_address,prompt_question,prompt_request)
    if chat == "address":
        return step_address(prompt_address)
    if chat == "question":
        return step_question(prompt_address, prompt_question)
    if chat == "bookit":
        return step_bookit(prompt_address,prompt_question,prompt_request)

# create Gradio interface for the chatbot
gr.close_all()
demo = gr.Interface(fn=start,
                    inputs=[gr.Textbox(label="Address?", lines=1,placeholder="123 main st"),
                            gr.Textbox(label="How can I help?", lines=1, placeholder="I would like to schedule a showing on July 28 at 1 PM for 30 minutes"),
                            gr.Textbox(label="Schedule it?", lines=1,placeholder="yes or no")],
                    outputs=[gr.Textbox(label="response", lines=30)],
                    title="Showings ChatBot",
                    description="A chatbot that schedules showings on properties for a real estate agent.",
                    allow_flagging="never")
demo.launch(server_name="localhost", server_port=8888)