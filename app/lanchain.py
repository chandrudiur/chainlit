import pandas as pd
import streamlit as st

CSV_FILE = "chat_history.csv"

try:
    chat_history_df = pd.read_csv(CSV_FILE)
except FileNotFoundError:
    chat_history_df = pd.DataFrame(columns=["ChatID", "Role", "Content"])

def get_button_label(chat_df, chat_id):
    first_message = chat_df[(chat_df["ChatID"] == chat_id) & (chat_df["Role"] == "User")].iloc[0]["Content"]
    return f"Chat {chat_id[0:7]}: {' '.join(first_message.split()[:5])}..."

st.sidebar.title("Chat History")

for chat_id in chat_history_df["ChatID"].unique():
    button_label = get_button_label(chat_history_df, chat_id)
    if st.sidebar.button(button_label):
        current_chat_id = chat_id
        loaded_chat = chat_history_df[chat_history_df["ChatID"] == chat_id]
        loaded_chat_string = "\n".join(f"{row['Role']}: {row['Content']}" for _, row in loaded_chat.iterrows())
        st.text_area("Chat History", value=loaded_chat_string, height=300)
