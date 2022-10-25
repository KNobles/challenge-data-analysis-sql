import os
import sqlite3
import pandas as pd
import streamlit as st


def create_connection(db_file: str):
    sqlite_connection = None
    try:
        sqlite_connection = sqlite3.connect(db_file)
    except Exception as e:
        st.write(e)
    return sqlite_connection

def run_query():
    st.markdown("# Run Query")
    sqlite_dbs = [file for file in os.listdir(".") if file.endswith(".db")]
    db_filename = st.selectbox("Database File", sqlite_dbs)

    qery = st.text_area("SQL query", height=50)
    conn = create_connection(db_filename)

    submitted = st.button("submit")
    
    if submitted:
        pass
    pass

sqlite_connection = sqlite3.connect("bce.db")

cursor = sqlite_connection.cursor()
a = cursor.execute("select JuridicalForm, count(JuridicalForm) from enterprise group by JuridicalForm;")
cols = [column[0] for column in a.description]
# print(a.fetchall())
juridical = a.fetchall()
juridical.remove(juridical[0])
recs = pd.DataFrame.from_records(data=juridical, columns=cols)
st.dataframe(recs)

st.write(sqlite_connection)