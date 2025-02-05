import openai


import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def convert_metadata(metadata_text):
    prompt = (
        "Convert the following metadata into a key-value dictionary in JSON format. "
        "Only output the dictionary. For example, if the metadata is 'title: Report, date: 2024-08-01', "
        'return {"title": "Report", "date": "2024-08-01"}.\n\n'
        f"Metadata: {metadata_text}"
    )
    response = openai.beta.chat.completions.parse(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": "You are a Python assistant that converts plain text metadata into a JSON dictionary.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content


def theorize_about_data(metadata_text):
    prompt = (
        "You will be given certain metadata about a dataframe. Your job is to ask 3 questions about the dataset. "
        "The dataset is designed for causal inference so all questions must be about cause-and-effect relationships; "
        "for example, a business may ask: did low salary cause high attrition? or what would have been the effect on "
        "sales last year had we increased advertising expenditure targeted at women? Similarly, an academic might ask: "
        "did improved educational attainment cause wage increase? or a member of the public: did lack of exercise lead "
        "to my weight gain? Do not output any other text than the questions. Return your answer as a JSON object with a "
        "single key 'questions' whose value is a list of the 3 questions.\n"
        f"Metadata: {metadata_text}"
    )
    response = openai.beta.chat.completions.parse(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": "You are a Python assistant that converts plain text metadata into a JSON dictionary.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    # Expecting OpenAI to return JSON like: {"questions": ["Question 1", "Question 2", "Question 3"]}
    return response.choices[0].message.content
