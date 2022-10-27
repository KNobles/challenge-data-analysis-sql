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
    pull_arr = [0] * len(df_form["form"])
    # print(pull_arr)
    # print(df_form.loc[(df_form["count"] == df_form["count"].max()) & (df_form["form"] != "Null")])
    # print(df_form.max())
    fig = go.Figure(data=[go.Pie(labels=df_form['form'].values, values=df_form['count'].values, pull=[0,0,0,0,0,0,0.1,0])])
    st.plotly_chart(fig)

# st.bar_chart(data=recs, x="form", y="count")

def get_company_status():
    cursor = create_connection("bce.db").cursor()
    comp_status = cursor.execute("""
    SELECT enterprise.Status,
    CASE WHEN DATETIME("now") > address.DateStrikingOff
        THEN "STRIKED OFF"
        WHEN DATETIME("now") < address.DateStrikingOff
        THEN "LIQUIDATION"
        ELSE "NO STRIKE" 
    END AS strike, count(*) as strike_count from address
    INNER JOIN enterprise ON address.EntityNumber = enterprise.EnterpriseNumber group by strike;
    """)
    cols = [column[0] for column in comp_status.description]
    statuses = comp_status.fetchall()
    df_status = pd.DataFrame.from_records(statuses, columns=cols)
    pull = [0] * len(df_status)
    pull[df_status["strike_count"].idxmax()] = 0.2
    print(df_status['strike'].values)
    fig = go.Figure(data=[go.Pie(labels=df_status['strike'].values, values=df_status['strike_count'].values, pull=pull, hole=0.4)])
    fig.update_layout(width=800, height=800, font=dict(size=18))
    st.plotly_chart(fig)
    # print(df_status["strike_count"].idxmax())

pages = {
    "Forms percentages" : get_form,
    "Status percentages" : get_company_status,
}

selected_page = st.sidebar.selectbox("Select a page", pages.keys())
pages[selected_page]()
#select code.*, enterprise.EnterpriseNumber from code 
# inner join enterprise on code.Code = enterprise.JuridicalForm group by enterprise.JuridicalForm