def generate_response(query, mode="Calm"):
    # Retrieve knowledge
    results = collection.query(
        query_texts=[query],
        n_results=5
    )