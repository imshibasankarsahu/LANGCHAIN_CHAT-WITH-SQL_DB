import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits  import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq

st.set_page_config(page_title="LANGCHAIN CHAT WITH SQLDB",page_icon="🗄️")
st.title("langchain chat with sqldatabase")

LOCAL_DB="USE_LOCALDB"
MYSQL="USE_MYSQL"

radio_opt=["use student.db","connect to mysql"]

selected_opt=st.sidebar.radio(label="select database",options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_url=MYSQL
    mysql_host=st.sidebar.text_input("provide mysql host")
    mysql_user=st.sidebar.text_input("mysql user")
    mysql_password=st.sidebar.text_input("mysql password",type="password")
    mysql_db=st.sidebar.text_input("Msql databse")

else:
    db_url=LOCAL_DB

api_key=st.sidebar.text_input("ENTER GROQ API KEY",type="password")

if not db_url:
    st.info("please select a database")

if not api_key:
    st.info("please enter api key")
    st.stop()

#llm model
llm=ChatGroq(model_name="qwen/qwen3-32b",groq_api_key=api_key,streaming=True)

@st.cache_resource(ttl="2h")
def config_db(db_url,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_url==LOCAL_DB:
       dbfilepath=(Path(__file__).parent/"student.db").absolute()
       creator=lambda:sqlite3.connect(f"file:{dbfilepath}?mode=ro",uri=True)
       return SQLDatabase(create_engine("sqlite://",creator=creator))
    elif db_url==MYSQL:
        if not(mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("please enter all mysql details")
            st.stop()
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"))
if db_url==MYSQL:
    db=config_db(db_url,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=config_db(db_url)

#toolkit
toolkit=SQLDatabaseToolkit(db=db,llm=llm)

agent=create_sql_agent(llm=llm,toolkit=toolkit,verbose=True,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION)

if "messages" not in st.session_state or st.sidebar.button("reset chat"):
    st.session_state["messages"]=[{"role":"assistant","content":"how can i help you"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query=st.chat_input(placeholder="ask any question from")

if user_query:
    st.session_state.messages.append({"role":"user","content":user_query})
    st.chat_message("user").write(user_query)
    
    with st.chat_message("assistant"):
        Streamlit_callback=StreamlitCallbackHandler(st.container())
        resp=agent.run(user_query,callbacks=[Streamlit_callback])
        st.write(resp)





    
       
      