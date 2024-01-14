"""
This module serves an application that defines and calls a currency conversion API
by a ChatGPT function.
"""
from flask import Flask
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import json

app = Flask(__name__)
load_dotenv()
openai_api_key = os.environ['OPENAI_API_KEY']
openai_client = OpenAI(api_key=openai_api_key)


# First step is to define the function that is supposed to be called
# by ChatGPT through the prompt.
def get_exchange(amount, currency_from, currency_to):
    response = requests.get("https://open.er-api.com/v6/latest/" + currency_from)
    exchange_rate = response.json()['rates'][currency_to]
    return amount * exchange_rate


# Secondly, the definition of the function structure is needed
# including the arguments to be parsed in.
functions = [
    {
        "name": "get_exchange",
        "description": "Calculate the exchange by given currencies",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The amount of the currency",
                },
                "currency_from": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
                "currency_to": {"type": "string", "enum": ["USD", "EUR", "GBP"]}
            },
            "required": ["amount", "currency_from", "currency_to"],
        },
    }
]


# Thirdly, the ChatGPT chat is created and the prompt filled out by a question
# that considers the function call.
@app.route('/exchange')
def exchange():
    messages = [{"role": "user", "content": "How much is 100 US Dollar in Euro?"}]

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        functions=functions,
        function_call="auto")

    response_message = response.choices[0].message
    if response_message.function_call:
        available_functions = {
            "get_exchange": get_exchange,
        }
        function_name = response_message.function_call.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(response_message.function_call.arguments)
        function_response = function_to_call(
            amount=function_args.get("amount"),
            currency_from=function_args.get("currency_from"),
            currency_to=function_args.get("currency_to")
        )
        return str(function_response) + " " + function_args.get("currency_to")


if __name__ == '__main__':
    app.run()
