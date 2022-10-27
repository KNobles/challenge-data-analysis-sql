import os
import sqlite3
import pandas as pd
from pyparsing import Optional
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

def make_pie_chart(query: sqlite3.Cursor | str, markdown_text: str, pie_legend_labels: str, pie_values: str, 
                    pull_biggest_value: bool=False, pull_size: float=0.2):
    """
    QUERY PARAMETER MUST HAVE BEEN EXECUTED BEFOREHAND
    """
    st.markdown(markdown_text)
    if isinstance(query, str) is True:
        # Executes the string type query
        query = get_cursor().execute(query)
    
    cols = get_column_names(query)
    query_list = query.fetchall()
    df = pd.DataFrame.from_records(data=query_list, columns=cols)
    if pull_biggest_value is True:
        pull_sector = [0] * len(df)
        pull_sector[df[pie_values].idxmax()] = pull_size
        fig = go.Figure(data=[go.Pie(labels=df[pie_legend_labels].values, values=df[pie_values].values, pull=pull_sector)])
    else:
        fig = go.Figure(data=[go.Pie(labels=df[pie_legend_labels].values, values=df[pie_values].values)])

    fig.update_layout(width=800, height=800, font_size=20, hoverlabel_font_size=20)
    st.plotly_chart(fig)

def get_juridical_form():
    st.markdown("# Percentage of juridical form in enterprises")
    form_query = get_cursor().execute("""
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
    df_form.loc[df_form["form"].astype(str) == "None", "form"] = "NULL"
    ind = df_form.groupby("form").filter(lambda x: x["form"] != "NULL")["count"].idxmax()
    pull_sector = [0] * len(df_form)
    pull_sector[ind] = 0.2
    fig = go.Figure(data=[go.Pie(labels=df_form['form'].values, values=df_form['count'].values, pull=pull_sector)])
    fig.update_layout(width=800, height=800, font_size=20, hoverlabel_font_size=20)
    st.plotly_chart(fig)

def get_company_status():
    markdown = "# Percentage of statuses in companies"
    company_status_query = get_cursor().execute("""
        SELECT enterprise.Status,
        CASE 
            WHEN DATETIME("now") > address.DateStrikingOff
                THEN "STRIKED OFF"
            WHEN DATETIME("now") < address.DateStrikingOff
                THEN "LIQUIDATION"
            ELSE "NO STRIKE" 
        END AS strike, COUNT(*) as strike_count from address
        INNER JOIN enterprise ON address.EntityNumber = enterprise.EnterpriseNumber group by strike;
        """)
    make_pie_chart(query=company_status_query, markdown_text=markdown, pie_legend_labels="strike", pie_values="strike_count")

def get_enterprise_type():
    markdown = "# Percentage of type of enterprise"
    # Apparently a Natural Person doesn't have a JuridicalForm
    enterprise_type_query = get_cursor().execute("""
        SELECT CASE 
            WHEN TypeOfEnterprise = 1
                THEN "Natural person" 
            WHEN TypeOfEnterprise = 2
                THEN "Legal person"
            ELSE "Other"
        END AS type, COUNT(TypeOfEnterprise) as type_count FROM enterprise 
        GROUP BY JuridicalForm;
        """)
    make_pie_chart(query=enterprise_type_query, markdown_text=markdown, pie_legend_labels="type", pie_values="type_count")

pages = {
    "Forms percentages" : get_juridical_form,
    "Status percentages" : get_company_status,
    "Enterprise type percentages": get_enterprise_type,
}

selected_page = st.sidebar.selectbox("Select a page", pages.keys())
pages[selected_page]()