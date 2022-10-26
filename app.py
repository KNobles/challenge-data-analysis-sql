import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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

    query = st.text_area("SQL query", height=50)
    conn = create_connection("bce.db")

    submitted = st.button("submit")
    
    if submitted:
        try:
            query = conn.execute(query)
            cols = [column[0] for column in query.description]
            results_df = pd.DataFrame.from_records(
                data = query.fetchall(), 
                columns = cols
            )
            st.dataframe(results_df)
        except Exception as e:
            st.write(e)

    st.sidebar.markdown("# Run Query")

sqlite_connection = sqlite3.connect("bce.db")

def get_form():
    st.markdown("# Percentage of juridical form in enterprises")
    cursor = create_connection("bce.db").cursor()
    form_list = cursor.execute("""
            SELECT form,SUM(count) count
            FROM
            (
                SELECT CASE WHEN COUNT(*) > 50000 THEN JuridicalForm ELSE 'others' 
                END form, COUNT(*) count 
                FROM enterprise 
                GROUP BY JuridicalForm
            )
            GROUP BY form
            ORDER BY form = 'others', count;
            """)
    cols = [column[0] for column in form_list.description]
    forms = form_list.fetchall()
    df_form = pd.DataFrame.from_records(data=forms, columns=cols)
    df_form.loc[df_form["form"].astype(str) == "None", "form"] = "Null"
    # print(df_form["form"].values)
    # fig = px.pie(df_form, values='count', names='form', title='Percentage of form')
    pull_arr = [0] * len(df_form["form"].array)
    # print(pull_arr)
    # print(df_form.loc[(df_form["count"] == df_form["count"].max()) & (df_form["form"] != "Null")])
    print(df_form.max())
    fig = go.Figure(data=[go.Pie(labels=df_form['form'].values, values=df_form['count'].values, pull=[0,0,0,0,0,0,0.1,0])])
    st.plotly_chart(fig)

# st.bar_chart(data=recs, x="form", y="count")

pages = {
    "Run Query" : run_query(),
    "Forms percentages" : get_form(),
}

selected_page = st.sidebar.selectbox("Select a page", pages.keys())