from openai import OpenAI
import os

# Initialize the OpenAI client with your specific API key and base URL
client = OpenAI(
    api_key="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",
    base_url="https://integrate.api.nvidia.com/v1"
)

def read_file_content(file_path):
    """Reads the entire content of a file and returns it."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def send_to_mistral(text_content):
    """Sends the given text content to the Mistral AI model and prints the response."""
    try:
        completion = client.chat.completions.create(
          model="mistralai/mixtral-8x22b-instruct-v0.1",
          messages = [{"role": "user", "content": f"Write some code for all the important implementations within the following content: {text_content}"}],
          temperature=0.5,
          top_p=1,
          max_tokens=1024,
          stream=True
        )

        # Print out each piece of content received from the streaming response
        for chunk in completion:
          if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")

    except Exception as e:
        print("An error occurred:", e)

if __name__ == "_main_":
    file_path = r'C:\Users\allah\OneDrive\Documents\A_Data\NJM2113M.txt'  # Specify the path to your text file
    text_content = read_file_content(file_path)
    send_to_mistral(text_content)