
import streamlit as st

import streamlit.components.v1 as components

import google.generativeai as genai

import json

import re



st.set_page_config(page_title="TEPCode Engine", layout="wide")



genai.configure(api_key="AIzaSyAoAC77K6X5XYBKlmeevRNx0yW0rEfxxDo")



model = genai.GenerativeModel("gemini-1.5-flash")



# Initialize session state variables

for key in ["responseLLM", "response4", "responseComparision", "responseArchitectReview", "responseFinal", "uploaded_json"]:

    if key not in st.session_state:

        st.session_state[key] = ""



st.title("TEPCode Engine")



user_prompt = st.text_area("Enter your Prompt to generate code:", "Generate code to validate customer names")



uploaded_file = st.file_uploader("Upload an Organization specific coding standards JSON file (Optional)", type=["json"])

if uploaded_file is not None:

    try:

        st.session_state.uploaded_json = json.load(uploaded_file)

    except json.JSONDecodeError as e:

        st.error(f"Invalid JSON file: {e}")



st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

st.markdown("<p style='font-size:14px;'>Select below to generate specifically (Optional)</p>", unsafe_allow_html=True)





@st.cache_data(show_spinner=False)

def generate_code(prompt):  # More generic function name

    try:

        response = model.generate_content(prompt)

        return response

    except Exception as e:

        return f"An error occurred: {e}"



# Input selection columns

col1, col2, col3 = st.columns(3)

with col1:

    selected_language = st.selectbox("Language", ["Java 8", "Java 11", "Java 17", "Java 21", "Python 3","PL/SQL 19c", "COBOL 6.4"],index=3)

with col2:

    domain = st.selectbox("Domain",["Generic","Banking", "Insurance", "Retail","Manufacturing","Life sciences"])

with col3:

    geo = st.selectbox("Geo",["Global","US", "Europe", "India","MiddleEast"]) # lowercase geo





def get_language_name(language_with_version):

    """Extracts the language name from the full language string (e.g., "Java 8" -> "Java")."""

    return language_with_version.split()[0]



def precheck_prompt(prompt, selected_language_full):

    # Extract only the language name

    selected_language = get_language_name(selected_language_full)



    precheck_response = model.generate_content("Is the following prompt relevant to code generation, respond only with yes or no." + prompt)

    is_relevant = precheck_response.text.strip().lower() == "yes"



    language_in_prompt = extract_language_from_prompt(prompt)

    print(f"The value in prompt is {language_in_prompt} and in dropdown is {selected_language}")

    if language_in_prompt:

        # Trim version numbers from prompt-extracted language if needed

        language_in_prompt = get_language_name(language_in_prompt)  

        if language_in_prompt.lower() != selected_language.lower():

            st.error(f"Language conflict: Prompt specifies {language_in_prompt}, but dropdown is set to {selected_language}. Please correct the mismatch.")

            return False

    return is_relevant



def extract_language_from_prompt(prompt):

    # Use regex to find common language mentions

    match = re.search(r"(Java|Python|COBOL|PL/SQL)(\s+\d+(?:\.\d+)?(?:[c\w]+)?)?", prompt, re.IGNORECASE)  # Add more languages as needed

    return match.group(1) if match else None







# Button actions

btcol1, btcol2 = st.columns(2)



def generate_button_action(full_prompt): # Consolidated generation logic

    st.session_state.responseLLM = generate_code(full_prompt)





def tepcode_button_action(user_prompt, selected_language, domain):  # Consolidated TEPCode logic

    responses = []

    my_bar = st.progress(0, text="Initializing...")  # Initial progress bar



    steps = [

        "Analysing the Requirement",

        "Groomimg the Requirement",

        "Breaking into tasks",

        "Designing the code",

        "Generating the code",

        "Validating the code",

        "Checking for Readability",

        "Idenfying Security Issues",

        "Regenerating the code"

    ]

    total_steps = len(steps)



    for i, step_text in enumerate(steps):

        my_bar.progress((i + 1) / total_steps, text=step_text)  # Update progress

        if i == 0:

            current_prompt = f"Rewrite the following prompt to improve its structure and detail for better LLM comprehension: {user_prompt}.  Break down the prompt into smaller, more manageable parts if necessary.  Add any missing context or information that might be crucial for accurate interpretation.  Prioritize clarity and explicit instructions, minimizing any room for ambiguity.  Respond only with prompt and no explanations." 

            responses.append(model.generate_content(current_prompt))

        elif i == 1:

            current_prompt = f"Give me the test scripts first for the described code in {selected_language} and for {domain} domain." + user_prompt

            responses.append(model.generate_content(current_prompt))

        elif i == 2:

            current_prompt = responses[-1].text + f"In this response make sure all the scenarios relevant to the {domain} domain are covered and respond only with updated unit test code"

            responses.append(model.generate_content(current_prompt))

        elif i == 3:

            current_prompt = responses[-1].text + f"Generate code in {selected_language} for unit test cases of above response and make sure unit test passes"

            responses.append(model.generate_content(current_prompt))

        elif i == 4:

            current_prompt = responses[-1].text + "Refactor the above code for readability, maintainability, performance and vulnerability and dont provide explanations. Add detailed comments in code. Seperate the code from unit test cases and repond with code and its unit tests in the order mentioned"



            if st.session_state.uploaded_json:

                current_prompt += f" Adhere to the following coding standards: {st.session_state.uploaded_json}"

            st.session_state.response4 = model.generate_content(current_prompt)

        elif i == 5:

            current_prompt = st.session_state.response4.text + "Review the above code from perspective of a senior technical architect and modify it as needed. Respond with complete updated code and its unit test cases and dont provide explanations.Seperate the code from unit test cases and repond with code and its unit tests in the order mentioned"

            st.session_state.responseArchitectReview = model.generate_content(current_prompt)

        elif i == 6:

            if st.session_state.uploaded_json:

                current_prompt = st.session_state.responseArchitectReview.text +f"Make sure the above code covers all the functionality mentioned in the following prompt {user_prompt} and modify it to cover the functionality extensively and it is high performant. Respond only with updated code(with code comments) and dont provide explanations. Make sure the code adheres to the standards defined in the JSON: {json.dumps(st.session_state.uploaded_json)}"

            else:

                current_prompt = st.session_state.responseArchitectReview.text +f"Make sure the above code covers all the functionality mentioned in the following prompt {user_prompt} and modify it to cover the functionality extensively and it is high performant. Respond only with updated code(with code comments) and dont provide explanations."

            st.session_state.responseFinal = model.generate_content(current_prompt)

        elif i == 7:

            full_prompt_4LLM = f"{user_prompt} in {selected_language} for {domain} domain. Respond only with code"

            st.session_state.responseLLM = generate_code(full_prompt_4LLM)

        elif i == 8:

            #comparisionPrompt = f"For the prompt {full_prompt_4LLM} give a detailed comparision  and tabular summary of LLM generated code: {st.session_state.responseLLM.text} and TEPCode: {st.session_state.responseFinal.text}. Respond with only the comparision and tabular summary not the code.In the tabular summary in addition to your comparision include the following rows time to process the code(in nanoseconds and assume it process very large input), lines of code (excluding unit tests), readability, code comments, coding standards, duplicated code, cyclometric complexity, scenario coverage. Split the tabular summary into two. Only the significant differences between LLMResponse and TEPCode diplay in table 1(Provide detailed explanantion of the difference against each attributes. Mention the code references as well). Minor differences display in table 2. "

            comparisionPrompt = f"For the prompt {full_prompt_4LLM} give a  tabular summary of LLM generated code: {st.session_state.responseLLM.text} and TEPCode: {st.session_state.responseFinal.text}. Compare and respond in a tabular summary without code.In the tabular summary in addition to your comparision include the following rows time to process the code(in nanoseconds and assume it process very large input), lines of code (excluding unit tests), readability, code comments, coding standards, cyclometric complexity, scenario coverage. Split the tabular summary into two. Only the significant differences between LLMResponse and TEPCode diplay in table 1(Provide detailed explanantion of the difference against each attributes. Mention the code references as well). Minor differences display in table 2. Also dont show the output of the comparision if it is very minimal or similar "

            st.session_state.responseComparision = generate_code(comparisionPrompt)



    my_bar.empty()  # Clear the progress bar





with btcol1:

    if st.button("Generate via LLM"):

        if precheck_prompt(user_prompt, selected_language): # Pass selected_language here

            full_prompt = f"{user_prompt} in {selected_language} for {domain} domain. Respond only with code"

            generate_button_action(full_prompt)

        else:

            st.error("This is coding assistant please provide relevant prompt")



with btcol2:

    if st.button("Generate via TEPCode Engine"):

        if precheck_prompt(user_prompt, selected_language): # Pass selected_language here

            tepcode_button_action(user_prompt, selected_language, domain)

        else:

            st.error("This is coding assistant please provide relevant prompt")







st.markdown(

    """

    <style>

     div.stButton > button {

            width: 75%; 

        }

    </style>

    """,

    unsafe_allow_html=True,

)



# Output columns

col_ratio = st.slider("Column Width Ratio (LLM:Rawen)", 0.1, 0.9, 0.5, 0.01, label_visibility="collapsed")

rtcol1, rtcol2 = st.columns([col_ratio, 1 - col_ratio])



with rtcol1:

    if st.session_state.responseLLM:

        # Escape the response text for safe inclusion in JavaScript

        escaped_response_text_LLM = st.session_state.responseLLM.text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")



        # Construct the HTML and JavaScript

        html_string = f"""

        <div>

          <button onclick="openPopup()">View Code in Popup Window</button>

          <script>

            function openPopup() {{

              var popup = window.open('', '_blank', 'width=800,height=600');

              popup.document.write('<pre>{escaped_response_text_LLM}</pre>');  // Use escaped text here

              popup.document.close();

            }}

          </script>

        </div>

        """

        components.html(html_string, height=50)  # Adjust height as needed

        st.write(st.session_state.responseLLM.text)



with rtcol2:

    if st.session_state.responseFinal:

                # Escape the response text for safe inclusion in JavaScript

        escaped_response_text_TEP = st.session_state.responseFinal.text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")



        # Construct the HTML and JavaScript

        html_string = f"""

        <div>

          <button onclick="openPopup()">View Code in Popup Window</button>

          <script>

            function openPopup() {{

              var popup = window.open('', '_blank', 'width=800,height=600');

              popup.document.write('<pre>{escaped_response_text_TEP}</pre>');  // Use escaped text here

              popup.document.close();

            }}

          </script>

        </div>

        """

        components.html(html_string, height=50)  # Adjust height as needed

        st.write(st.session_state.responseFinal.text)



if st.session_state.responseComparision:

    st.write(st.session_state.responseComparision.text)



