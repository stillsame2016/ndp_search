import json
import os

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv

# load_dotenv()
# GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

safe = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]


# Gemini uses 'model' for assistant; Streamlit uses 'assistant'
def role_to_streamlit(role):
    if role == "model":
        return "assistant"
    else:
        return role


# Add a Gemini Chat history object to Streamlit session state
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Display Form Title
st.title("Chat with NDP")

# Display chat messages from history above current input box
for message in st.session_state.chat.history:
    with st.chat_message(role_to_streamlit(message.role)):

        if message.role == 'user':
            prompt = message.parts[0].text
            start_index = prompt.find("[--- Start ---]") + len("[--- Start ---]")
            end_index = prompt.find("[--- End ---]")
            prompt = prompt[start_index:end_index].strip()
            st.markdown(prompt)
        else:
            answer = message.parts[0].text
            print('-'*70, 'raw answer in history')
            print(answer)

            if answer.startswith('```json'):
                json_part = answer.split("\n", 1)[1].rsplit("\n", 1)[0]
                data = json.loads(json_part)
            else:
                data = json.loads(answer)

            print('-' * 70, 'json answer in history')
            print(data)

            if not data["is_search_data"]:
                assistant_response = data["alternative_answer"]
            else:
                answer = "Searching NDP catalog by the terms:"
                for term in data['search_terms']:
                    answer = f"{answer}\n - {term}"
                assistant_response = answer

            st.markdown(assistant_response)

        # st.markdown(message.parts[0].text)

# Accept user's next message, add to context, resubmit context to Gemini
if prompt := st.chat_input("I'm the NDP Catalog Assistant. Need data or have questions? Just ask!"):
    # Display user's last message
    st.chat_message("user").markdown(prompt)

    query = f"""
      You are an expert of the national data platform catalog for scientific datasets. 
      You also have general knowledge.
      Our catalog provides the information about datasets. The following is a question 
      the user is asking:
       
       [--- Start ---]
       {prompt}
       [--- End ---]

        Please judge whether this user is searching for datasets. If yes, please extract 
        the real search terms asked by this user. Provide your answer in the valid JSON format 
        as "is_search_data" and a list of "search_terms" if the user is asking for datasets. 
        Please do your best to give a positive answer to the user's question in the 
        "alternative_answer" field of the JSON string even if the user is not asking for datasets.

       """

    # Send user entry to Gemini and read the response
    response = st.session_state.chat.send_message(query, safety_settings=safe, )

    # Display last
    with st.chat_message("assistant"):

        data = response.text
        print('-'*70, 'raw data')
        print(data)

        if data.startswith('```json'):
            json_part = data.split("\n", 1)[1].rsplit("\n", 1)[0]
            data = json.loads(json_part)
        else:
            data = json.loads(data)

        print('-' * 70, 'json data')
        print(data)

        if not data["is_search_data"]:
            assistant_response = data["alternative_answer"]
        else:
            answer = "Searching NDP catalog by the terms:"
            for term in data['search_terms']:
                answer = f"{answer}\n - {term}"
            assistant_response = answer

        st.markdown(assistant_response)
