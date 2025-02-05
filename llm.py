import openai
import json


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


def theorize_about_data(input):
    prompt = (
        "You will be given certain metadata about a dataframe. Your job is to ask 3 questions about the dataset. "
        "The dataset is designed for causal inference so all questions must be about cause-and-effect relationships; "
        "for example, a business may ask: did low salary cause high attrition? or what would have been the effect on "
        "sales last year had we increased advertising expenditure targeted at women? Similarly, an academic might ask: "
        "did improved educational attainment cause wage increase? or a member of the public: did lack of exercise lead "
        "to my weight gain? Do not output any other text than the questions. Return your answer as a JSON object with a "
        "single key 'questions' whose value is a list of the 3 questions.\n"
        f"Metadata: {input}"
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


def get_variables_from_metadata(input):
    prompt = (
        "You will be given certain text metadata"
        "We will be using the dataframe to study causal inference"
        "Your job is to return 3 things, - "
        "1. The outcome variable"
        "2. The Treatment variable"
        "3. The confounder variables"
        "In causal inference, a confounding variable is a variable that influences both the independent and dependent variables, creating a spurious association. Confounding variables are a threat to internal validity"
        f"Metadata: {input}"
    )
    response = openai.beta.chat.completions.parse(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": "You are a Python assistant that converts plain text metadata into a Python dictionary. Do not say anything other than the resultant python dictionary",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    res = response.choices[0].message.content
    res.replace("json", "")
    return res


test = """A data frame with 614 observations (185 treated, 429 control). There are 10 variables measured for each individual:

treat is the treatment assignment (1=treated, 0=control).
age is age in years.
educ is education in number of years of schooling.
black is an indicator for African-American (1=African-American, 0=not).
hispan is an indicator for being of Hispanic origin (1=Hispanic, 0=not).
married is an indicator for married (1=married, 0=not married).
nodegree is an indicator for whether the individual has a high school degree (1=no degree, 0=degree).
re74 is income in 1974, in U.S. dollars.
re75 is income in 1975, in U.S. dollars.
re78 is income in 1978, in U.S. dollars."""
result = get_variables_from_metadata(convert_metadata(test))

result = json.loads(result)
for k, v in result.items():
    print(k, v)
