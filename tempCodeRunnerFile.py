import streamlit as st
from dharma_ai import generate_response

st.title("🧘 Dharma AI")

query = st.text_input("Ask your question:")

mode = st.selectbox("Choose Mode", [
    "Calm", "Logical", "Ethical", "Motivational", "Direct"
])

if st.button("Get Guidance"):
    if query:
        response = generate_response(query, mode)
        st.write("### 🪷 Dharma AI Says:")
        st.write(response)