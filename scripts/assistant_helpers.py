# assistants_helpers.py
from scripts.csv_db import get_shopping_session, get_product_pages_by_session_id


def create_chat_thread(client, user_preferences, intent):
    """
    Creates a new Thread using the Assistants API and pre-populates it with two assistant messages.
    
    Args:
        user_demographics (dict): e.g., {"Name": "Alice", "Email": "alice@example.com"}
        user_preferences (list): List of dicts, e.g., [{"preference_key": "budget", "preference_value": "$100-$200"}, ...]
        intent (str): What the user is looking to buy.
        assistant_id (str): The ID of your pre-created Assistant.
    
    Returns:
        thread_id (str): The ID of the newly created thread.
        initial_messages (list): The list of messages that were added.
    """
    # Step 1: Create a new thread.
    thread = client.beta.threads.create()
    thread_id = thread.id

    # Step 2: Prepare the content for the first assistant message.
    preferences_info = "\n".join(
        f"{pref['preference_key']}: {pref['preference_value']}" for pref in user_preferences
    )
    message1_content = (
        f"User Preferences:\n{preferences_info}\n\n"
        f"User Intent: {intent}"
    )

    # Add the first assistant message.
    msg1 = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="assistant",
        content=message1_content
    )

    # Step 3: Add a second assistant message that asks clarifying questions.
    clarifying_questions = (
        "To better assist you, could you please answer a few questions:\n"
        "1. What is your price range?\n"
        "2. Are there any specific brands or features you're looking for?\n"
        "3. Any other details that are important to you?"
    )
    msg2 = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="assistant",
        content=clarifying_questions
    )

    initial_messages = [msg1, msg2]
    return thread_id, initial_messages




class ChatAgent:
    def __init__(self, client, assistant_id):
        """
        Initialize with an OpenAI client and the assistant_id.
        
        Args:
            client: Your OpenAI client instance.
            assistant_id (str): The ID of your chat assistant.
        """
        self.client = client
        self.assistant_id = assistant_id

    def add_message(self, thread_id, user_message):
        """
        Adds a new user message to the given thread, runs the Assistant, 
        and returns the updated messages.

        Args:
            thread_id (str): The thread ID (from the shopping session).
            user_message (str): The content of the user’s new message.
        
        Returns:
            list: The updated list of messages from the thread, or a dict with status if not completed.
        """
        # Add the user's message to the thread.
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Create a run on the thread to generate a response from the assistant.
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Check if the run has completed.
        if run.status == "completed":
            response = self.client.beta.threads.messages.list(thread_id=thread_id)
            messages = []
            # Iterate over the message objects from the response.
            for msg in response.data:
                text_value = ""
                # Each message's content is a list of items.
                for item in msg.content:
                    if item.type == "text":
                        text_value += item.text.value
                messages.append({
                    "id": msg.id,
                    "role": msg.role,
                    "created_at": msg.created_at,
                    "content": text_value,
                })
            return messages
        else:
            return {"status": run.status}



class ProductDescriptionAgent:
    def __init__(self, client, product_description_assistant_id):
        """
        Initialize the ProductDescriptionAgent with an OpenAI client and 
        the product description assistant ID.
        
        Args:
            client: Your OpenAI client instance.
            product_description_assistant_id (str): The assistant ID for your product description assistant.
        """
        self.client = client
        self.product_description_assistant_id = product_description_assistant_id

    def generate_description(self, session_id, product_page):
        """
        Generates a tailored product description using the product description assistant.
        
        Args:
            session_id (str): The shopping session ID.
            product_page (str): A string containing the product webpage information.
        
        Returns:
            list: A list of dictionaries representing the messages generated by the product description assistant,
                  or a dict with the run status if not completed.
        """
        # Retrieve the shopping session to get the main conversation's thread_id.
        session = get_shopping_session(session_id)
        if not session:
            return {"error": "Session not found."}

        main_thread_id = session.get("thread_id")
        if not main_thread_id:
            return {"error": "No thread_id found in session."}

        # Retrieve the conversation from the main thread.
        conversation_response = self.client.beta.threads.messages.list(thread_id=main_thread_id)
        conversation_text = ""
        for msg in conversation_response.data[::-1]:
            for item in msg.content:
                if item.type == "text":
                    conversation_text += item.text.value + "\n"

        # Compose the prompt by combining the pre-shopping conversation and the product page.
        prompt = (
            f"Pre-shopping conversation with User:\n{conversation_text}\n"
            f"Product Page:\n{product_page}\n\n"
            "Create a tailored product description for this user..."
        )

        # Create a new thread for the product description generation.
        new_thread = self.client.beta.threads.create()
        new_thread_id = new_thread.id

        # Add the composed prompt as a message to the new thread.
        self.client.beta.threads.messages.create(
            thread_id=new_thread_id,
            role="user",  # You can adjust the role as needed.
            content=prompt
        )

        # Run the thread using the product description assistant.
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=new_thread_id,
            assistant_id=self.product_description_assistant_id,
            instructions=""
        )

        if run.status == "completed":
            response = self.client.beta.threads.messages.list(thread_id=new_thread_id)
            messages = []
            for msg in response.data:
                text_value = ""
                for item in msg.content:
                    if item.type == "text":
                        text_value += item.text.value
                messages.append({
                    "id": msg.id,
                    "role": msg.role,
                    "created_at": msg.created_at,
                    "content": text_value,
                })
            return messages
        else:
            return {"status": run.status}


class ComparisonAgent:
    def __init__(self, client, comparison_assistant_id):
        """
        Initialize the ComparisonAgent with an OpenAI client and 
        the comparison assistant ID.
        
        Args:
            client: Your OpenAI client instance.
            comparison_assistant_id (str): The assistant ID for your comparison assistant.
        """
        self.client = client
        self.comparison_assistant_id = comparison_assistant_id

    def generate_comparison(self, session_id):
        """
        Generates a comparison table for all products in the current session.
        
        The method performs the following steps:
        1. Retrieves all product pages saved for the session.
        2. Retrieves the conversation thread for the session.
        3. Appends to a new prompt the text for each product page in the format "Product X: {text}".
        4. Appends an instruction message: "Create a comparison table for these products and output the markdown."
        5. Creates a new thread, adds the composed prompt as a message, runs the thread using the comparison assistant,
           and returns the model's response (formatted as markdown).
        
        Args:
            session_id (str): The shopping session ID.
        
        Returns:
            A list of dictionaries representing the assistant's response messages, or a dict with run status if not completed.
        """
        # Retrieve the shopping session to get the main conversation's thread_id.
        session = get_shopping_session(session_id)
        if not session:
            return {"error": "Session not found."}
        
        main_thread_id = session.get("thread_id")
        if not main_thread_id:
            return {"error": "No thread_id found in session."}
        
        # Retrieve the conversation from the main thread.
        conversation_response = self.client.beta.threads.messages.list(thread_id=main_thread_id)
        conversation_text = ""
        for msg in conversation_response.data[::-1]:
            for item in msg.content:
                if item.type == "text":
                    conversation_text += item.text.value + "\n"
        
        product_pages = get_product_pages_by_session_id(session_id)
        products_text = ""
        for idx, record in enumerate(product_pages, start=1):
            products_text += f"#Start: Product {idx} Description#\n: {record['product_page']}\n\n"
            products_text += f"#End: Product {idx} Description#\n\n"
        # Compose the prompt.
        prompt = (
            f"#Start: Pre-shopping conversation with User:\n{conversation_text}#\n\n"
            "#End: Pre-shopping conversation with User\n\n"
            f"{products_text}"
            "Remove duplicates and pick at most 4 products that best match user needs to create a comparison table for them."
        )

        print(prompt)
        
        # Create a new thread for the comparison task.
        new_thread = self.client.beta.threads.create()
        new_thread_id = new_thread.id
        
        # Add the composed prompt as a message to the new thread.
        self.client.beta.threads.messages.create(
            thread_id=new_thread_id,
            role="user",
            content=prompt
        )
        
        # Run the thread using the comparison assistant.
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=new_thread_id,
            assistant_id=self.comparison_assistant_id
        )
        
        if run.status == "completed":
            response = self.client.beta.threads.messages.list(thread_id=new_thread_id)
            messages = []
            # Filter to only the assistant's responses.
            for msg in response.data:
                if msg.role == "assistant":
                    text_value = ""
                    for item in msg.content:
                        if item.type == "text":
                            text_value += item.text.value
                    messages.append({
                        "id": msg.id,
                        "role": msg.role,
                        "created_at": msg.created_at,
                        "content": text_value,
                    })
            return messages
        else:
            return {"status": run.status}