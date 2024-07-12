from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
import pandas as pd
import streamlit as st
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static
from langchain_groq import ChatGroq
import geopandas as gpd

def get_df_code(llm, question):
    prompt = PromptTemplate(
        template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
        We have a dataframe df with the following columns:
            TOTPOP_CY	
            POPDENS_CY	
            POPPRM_CY	
            MALES_CY	
            FEMALES_CY	
            TOTHH_CY	
            AVGHHSZ_CY	
            PAGE01_CY	
            PAGE02_CY
            PAGE03_CY
            PAGE04_CY
            PAGE05_CY
            MAGE01_CY
            MAGE02_CY
            MAGE03_CY
            MAGE04_CY
            MAGE05_CY
            FAGE01_CY
            FAGE02_CY
            FAGE03_CY
            FAGE04_CY
            FAGE05_CY
            MRST01_CY
            MRST02_CY
            MRST03_CY
            MRST04_CY
            MRST_BASE
            EDUC01_CY
            EDUC02_CY
            EDUC03_CY
            EDUC04_CY
            EDUC05_CY
            EDUC_BASE
            UNEMP_CY
            PP_CY
            PPPRM_CY
            PPPC_CY
            PPIDX_CY
            ID
            AREA
            RG_NAME

        The following is the request from a user:    
        {question}

        Generate the python code for the request as one statement st.session_state.df = ... only without any explanation.

        Answer:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """,
        input_variables=["question"],
    )

    df_code_chain = prompt | llm | StrOutputParser()
    return df_code_chain.invoke({"question": question})


title = "Jordan Purchasing Power per Capita"
st.set_page_config(layout="wide", page_title=title)
st.markdown(f"### {title}")

# Set up LLM
llm = ChatGroq(temperature=0, model_name="llama3-70b-8192", api_key="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")

# Add a Chat history object to Streamlit session state
if "chat" not in st.session_state:
    st.session_state.chat = []

# Create a Kepler map
map1 = KeplerGl(height=400)

config = {
    "version": "v1",
    "config": {
        "mapState": {
            "bearing": 0,
            "latitude": 32.24,
            "longitude": 35.35,
            "pitch": 0,
            "zoom": 6,
        },
        "visState": {
          'layerBlending': "additive",
        }
    },
}
map1.config = config

# Load CSV file
df = gpd.read_file('dataset/Jordan Purchasing Power/governorate.geojson')
df = df.set_geometry('geometry')

if "df" in st.session_state:
    map1.add_data(data=st.session_state.df, name=title)
else:
    map1.add_data(data=df, name=title)

# Set up two columns for the map and chat interface
col1, col2 = st.columns([3, 2])

with col1:
    keplergl_static(map1)

# Set up the chat interface
with col2:
    # Create a container for the chat messages
    chat_container = st.container(height=355)

    # Show the chat history
    for message in st.session_state.chat:
        with chat_container:
            with st.chat_message(message['role']):
                st.markdown(message['content'])

    # Get user input
    user_input = st.chat_input("What can I help you with?")
    if user_input:
        with chat_container:
            st.chat_message("user").markdown(user_input)
            st.session_state.chat.append({"role": "user", "content": user_input})

            with st.chat_message("assistant"):
                with st.spinner("We are in the process of your request"):
                    try:
                        result = get_df_code(llm, user_input)
                        exec(result)
                        if isinstance(st.session_state.df, pd.Series):
                            st.session_state.df = st.session_state.df.to_frame().T
                        response = f"Your request was processed. {st.session_state.df.shape[0]} rows are found and displayed"
                    except:
                        response = "We are not able to process your request. Please refine your request and try again."
                    st.session_state.chat.append({"role": "assistant", "content": response})
                    st.rerun()

if "df" in st.session_state:
    showdf = st.session_state.df
    showdf['geometry'] = showdf['geometry'].astype(str)
    st.dataframe(showdf)
else:
    showdf = df
    showdf['geometry'] = showdf['geometry'].astype(str)
    st.dataframe(showdf)