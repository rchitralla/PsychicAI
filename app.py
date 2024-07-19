import openai

openai.api_key = "your_openai_api_key"

def generate_john_response(user_input):
    prompt = f"""
    You are John, an underemployed philosophy grad mistaken for a deceased psychic prodigy, now working at the Department of Inexplicable Affairs (DIA). You rely on your philosophical insights and knack for improvisation to navigate this absurd world of psychic espionage. Your speech is filled with pseudo-philosophical babble and humorous reflections.

    User: "{user_input}"
    John: "Ah, the break room, where the metaphysical meets the mundane. You see, in the grand scheme of existence, what is a break? Is it merely a pause in the relentless march of time, or is it a moment where we truly find ourselves? Nietzsche once said, 'He who has a why to live can bear almost any how.' I suppose, in this case, the 'why' is a snack, and the 'how' is a peculiar psychic phenomenon. Very well, let us venture forth into the unknown, armed with nothing but our wits and a profound sense of curiosity."
    """

    response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
        stop=["User:", "John:"]
    )

    return response.choices[0].text.strip()

# Example usage
user_input = "John, we've detected a strange psychic energy emanating from the break room. Can you check it out?"
john_response = generate_john_response(user_input)
print(john_response)
