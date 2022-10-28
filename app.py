import os
import sqlite3
import pandas as pd
from pyparsing import Optional
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re

def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None

def create_connection(db_file: str):
    sqlite_connection = None
    try:
        sqlite_connection = sqlite3.connect(db_file)
        sqlite_connection.create_function("REGEXP", 2, regexp)
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
    get_cursor().execute("""DROP VIEW IF EXISTS view_form;""")
    form_second_query = get_cursor().execute("""
        CREATE VIEW view_form as SELECT coalesce(form, "None") as form,SUM(count) count
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
    form_last_query = get_cursor().execute("""
    select view_form.*, view_form.form || " - " || coalesce(code.Description, "No Description") as Description 
    from view_form left join code on view_form.form = code.Code and code.Language = "FR" group by form;""")
    cols = get_column_names(form_last_query)
    forms = form_last_query.fetchall()
    df_form = pd.DataFrame.from_records(data=forms, columns=cols)
    df_form.loc[df_form["form"].astype(str) == "others", "Description"] = "Others"
    df_form.loc[df_form["form"].astype(str) == "None", "form"] = "None"
    ind = df_form.groupby("form").filter(lambda x: x["form"] != "None")["count"].idxmax()
    pull_sector = [0] * len(df_form)
    pull_sector[ind] = 0.2
    fig = go.Figure(data=[go.Pie(labels=df_form['Description'].values, values=df_form['count'].values, pull=pull_sector)])
    fig.update_layout(width=1000, height=1000, font_size=18, hoverlabel_font_size=18)
    st.plotly_chart(fig)
    # percentage = ((df_form["count"] / df_form["count"].sum()) * 100)
    # df_form.insert(loc=2, column="percentage", value=percentage)
    # df_form["percentage"] = df_form["percentage"].round(2)
    # print(df_form)
    # st.table(data=df_form)

def get_company_status():
    markdown = "# Percentage of statuses in companies"
    markdown_strike = "# Percentage of Strike type of enterprise"
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
    status_query = get_cursor().execute("""
    select Status, count(*) as "count" from enterprise group by Status;
    """)
    make_pie_chart(query=status_query, markdown_text=markdown, pie_legend_labels="Status", pie_values="count")

    make_pie_chart(query=company_status_query, markdown_text=markdown_strike, pie_legend_labels="strike", pie_values="strike_count")

def get_enterprise_type():
    markdown = "# Percentage of type of enterprise"
    # Apparently a Natural Person doesn't have a JuridicalForm
    enterprise_type_query = get_cursor().execute("""
        SELECT CASE 
            WHEN TypeOfEnterprise = 1
                THEN "Natural Person" 
            WHEN TypeOfEnterprise = 2
                THEN "Legal Person"
            ELSE "Other"
        END AS type, COUNT(TypeOfEnterprise) as type_count FROM enterprise 
        GROUP BY JuridicalForm;
        """)
    make_pie_chart(query=enterprise_type_query, markdown_text=markdown, pie_legend_labels="type", pie_values="type_count")
    st.markdown("## Natural Person")
    st.markdown("#### Natural Person is a human being and is a real and living person.")
    st.markdown("## Legal Person")
    st.markdown("#### Legal Person is being, real or imaginary whom the law regards as capable of rights and duties")

def in_csv():
    nace_query = get_cursor().execute("""
    select view_act_ent.*, code.Description from view_act_ent inner join code on view_act_ent.version = Code.Category;
    """)
    cols = get_column_names(nace_query)
    nace_list = nace_query.fetchall()
    df_nace = pd.DataFrame.from_records(data=nace_list, columns=cols)
    df_nace.to_csv("nace.csv")

def get_company_age_avg():
    age_avg_query = get_cursor().execute("""
    select nace_avg.avg_age, nace_avg.subcode, code.Code, code.Description from nace_avg 
    inner join code on nace_avg.version = code.Category group by nace_avg.avg_age order by nace_avg.subcode;
    """)
    cols = get_column_names(age_avg_query)
    age_avg_list = age_avg_query.fetchall()
    df_avg = pd.DataFrame.from_records(data=age_avg_list, columns=cols)
    df_avg["subcode"] = df_avg["subcode"].astype(int)
    # print(df_avg.dtypes)
    df_avg.loc[df_avg["subcode"] < 5, "Description"] = "Agriculture, forestry and fishing"
    df_avg.loc[(df_avg["subcode"] >= 5) & (df_avg["subcode"] < 10), "Description"] = "Mining and quarrying"
    df_avg.loc[(df_avg["subcode"] >= 10) & (df_avg["subcode"] < 35), "Description"] = "Manufacturing"
    df_avg.loc[(df_avg["subcode"] >= 35) & (df_avg["subcode"] < 36), "Description"] = "Electricity, gas, steam and air conditioning supply"
    df_avg.loc[(df_avg["subcode"] >= 36) & (df_avg["subcode"] < 41), "Description"] = "Water supply; sewerage; waste managment and remediation activities"
    df_avg.loc[(df_avg["subcode"] >= 41) & (df_avg["subcode"] < 45), "Description"] = "Construction"
    df_avg.loc[(df_avg["subcode"] >= 45) & (df_avg["subcode"] < 49), "Description"] = "Wholesale and retail trade; repair of motor vehicles and motorcycles"
    df_avg.loc[(df_avg["subcode"] >= 49) & (df_avg["subcode"] < 55), "Description"] = "Transporting and storage"
    df_avg.loc[(df_avg["subcode"] >= 55) & (df_avg["subcode"] < 58), "Description"] = "Accommodation and food service activities"
    df_avg.loc[(df_avg["subcode"] >= 58) & (df_avg["subcode"] < 64), "Description"] = "Information and communication"
    df_avg.loc[(df_avg["subcode"] >= 64) & (df_avg["subcode"] < 68), "Description"] = "Financial and insurance activities"
    df_avg.loc[(df_avg["subcode"] >= 68) & (df_avg["subcode"] < 69), "Description"] = "Real estate activities"
    df_avg.loc[(df_avg["subcode"] >= 69) & (df_avg["subcode"] < 77), "Description"] = "Professional, scientific and technical activities"
    df_avg.loc[(df_avg["subcode"] >= 77) & (df_avg["subcode"] < 85), "Description"] = "Administrative and support service activities"
    df_avg.loc[(df_avg["subcode"] >= 85) & (df_avg["subcode"] < 86), "Description"] = "Education"
    df_avg.loc[(df_avg["subcode"] >= 86) & (df_avg["subcode"] < 90), "Description"] = "Human health and social work activities"
    df_avg.loc[(df_avg["subcode"] >= 90) & (df_avg["subcode"] < 94), "Description"] = "Arts, entertainment and recreation"
    df_avg.loc[(df_avg["subcode"] >= 94) & (df_avg["subcode"] < 97), "Description"] = "Other services activities"
    df_avg.loc[(df_avg["subcode"] >= 97) & (df_avg["subcode"] < 99), "Description"] = "Activities of households as employers; undifferentiated goods - and services - producing activities of households for own use"
    df_avg.loc[(df_avg["subcode"] >= 99) & (df_avg["subcode"] < 101), "Description"] = "Activities of extraterritorial organisations and bodies"
    print(df_avg["Description"])
    fig = px.bar(data_frame=df_avg, y="Description", x="avg_age")
    fig.update_layout(width=1400, height=500, font_size=14)
    st.plotly_chart(fig)
    # df_avg.groupby("Description")
    # st.table(df_avg)



pages = {
    "Forms percentages" : get_juridical_form,
    "Status percentages" : get_company_status,
    "Enterprise type percentages": get_enterprise_type,
    "Company's nace code age average": get_company_age_avg,
}

selected_page = st.sidebar.selectbox("Select a page", pages.keys())
pages[selected_page]()