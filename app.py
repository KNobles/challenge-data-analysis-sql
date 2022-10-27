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

def get_cursor():
    return create_connection("bce.db").cursor()

def get_column_names(query_cursor: sqlite3.Cursor):
    return [column[0] for column in query_cursor.description]

def get_juridical_form():
    st.markdown("# Percentage of juridical form in enterprises")
    cursor = get_cursor()
    form_query = cursor.execute("""
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
    cols = get_column_names(form_query)
    forms = form_query.fetchall()
    df_form = pd.DataFrame.from_records(data=forms, columns=cols)
    df_form.loc[df_form["form"].astype(str) == "None", "form"] = "Null"
    ind = df_form.groupby("form").filter(lambda x: x["form"] != "Null")["count"].idxmax()
    pull_sector = [0] * len(df_form)
    pull_sector[ind] = 0.2
    fig = go.Figure(data=[go.Pie(labels=df_form['form'].values, values=df_form['count'].values, pull=pull_sector)])
    fig.update_layout(width=800, height=800, font_size=20)
    st.plotly_chart(fig)

def get_company_status():
    st.markdown("# Percentage of statuses in companies")
    cursor = get_cursor()
    company_status_query = cursor.execute("""
    SELECT enterprise.Status,
    CASE WHEN DATETIME("now") > address.DateStrikingOff
        THEN "STRIKED OFF"
        WHEN DATETIME("now") < address.DateStrikingOff
        THEN "LIQUIDATION"
        ELSE "NO STRIKE" 
    END AS strike, COUNT(*) as strike_count from address
    INNER JOIN enterprise ON address.EntityNumber = enterprise.EnterpriseNumber group by strike;
    """)
    cols = get_column_names(company_status_query)
    statuses = company_status_query.fetchall()
    df_status = pd.DataFrame.from_records(statuses, columns=cols)
    pull_sector = [0] * len(df_status)
    pull_sector[df_status["strike_count"].idxmax()] = 0.2
    fig = go.Figure(data=[go.Pie(labels=df_status['strike'].values, values=df_status['strike_count'].values, pull=pull_sector, hole=0.4)])
    fig.update_layout(width=800, height=800, font_size=20)
    st.plotly_chart(fig)

def get_enterprise_type():
    cursor = get_cursor()
    st.markdown("# Percentage of type of enterprise")
    # Apparently a Natural Person doesn't have a JuridicalForm
    enterprise_type_query = cursor.execute("""
    SELECT CASE 
    WHEN TypeOfEnterprise = 1
        THEN "Natural person" 
    WHEN TypeOfEnterprise = 2
        THEN "Legal person"
        ELSE "Other"
    END AS type, COUNT(TypeOfEnterprise) as count FROM enterprise 
    GROUP BY JuridicalForm;
    """)
    cols = get_column_names(enterprise_type_query)
    enterprise_types = enterprise_type_query.fetchall()
    df_type = pd.DataFrame.from_records(enterprise_types, columns=cols)
    fig = px.pie(data_frame=df_type, values="count", names="type")
    fig.update_layout(width=800, height=800, font_size=20)
    st.plotly_chart(fig)

pages = {
    "Forms percentages" : get_juridical_form,
    "Status percentages" : get_company_status,
    "Enterprise type percentages": get_enterprise_type,
}

selected_page = st.sidebar.selectbox("Select a page", pages.keys())
pages[selected_page]()
#select code.*, enterprise.EnterpriseNumber from code 
# inner join enterprise on code.Code = enterprise.JuridicalForm group by enterprise.JuridicalForm