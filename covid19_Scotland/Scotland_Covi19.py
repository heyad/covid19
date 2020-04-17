#!/usr/bin/env python
# coding: utf-8

# ### Covid 19 Confirmed Cases in Scotland 
# 
# * Data Loaded from https://github.com/watty62/Scot_covid19 
# * and from https://github.com/watty62/Scot_covid19 to get uk indicator 
# * Thanks to Ian Watt for putting it together 

# In[267]:


# relevant libraries
# essential libraries
import pandas as pd
import numpy as np
import seaborn as sns
import datetime

from matplotlib import pyplot as plt
from datetime import date
import plotly.graph_objects as go
from fbprophet import Prophet
import pycountry
import plotly
import plotly.express as px
import plotly.io as pio
from functools import reduce 
import streamlit as st

# ### Confirmed Cases

# In[268]:
# In[2]:
st.title('Covid19-Scotland')
#stdate =pd.to_datetime(max(covid19['Date']))

read_and_cache_csv = st.cache(pd.read_csv)

#st.write ('Covid19')

# cash this function 
@st.cache  #  This function will be cached
def load_prepare_data():


    # load files from github more details on https://github.com/watty62/Scot_covid19
    dail_url = 'https://raw.githubusercontent.com/watty62/Scot_covid19/master/data/processed/new_daily_cases.csv'
    nat_cases_url ='https://raw.githubusercontent.com/watty62/Scot_covid19/master/data/processed/regional_cases.csv'
    uk_indicators ='https://raw.githubusercontent.com/tomwhite/covid-19-uk-data/master/data/covid-19-indicators-uk.csv'
    scot_conf = pd.read_csv(dail_url)
    nat_cases_df = pd.read_csv(nat_cases_url)
    scot_conf.columns=['Date','Confirmed']
    scot_conf.head()
    df_uk = pd.read_csv(uk_indicators)



    # add cummulative sum column 
    scot_conf['Cum_sum'] = scot_conf['Confirmed'].cumsum()
    #scot_conf.head()
    nat_cases_df.drop('Grand Total', axis=1, inplace=True)
    #nat_cases_df.head()
    # tidy the data 
    temp = nat_cases_df.transpose().copy()
    temp = temp.reset_index()

    # Chagne names of the columns 

    temp.columns = temp.iloc[0, 0:]
    temp.rename(columns={'Date':'Region'}, inplace=True)

    # drop first row (contains the names of the orginal df)
    temp = temp.iloc[1:]
    dates_list = temp.columns.to_list()[1:]

    # tidy data df_confirmed 
    tempM = pd.melt(temp, id_vars='Region',     value_vars=dates_list, var_name='Date', value_name='Confirmed')


    tempM['Deaths']=0
    #tempM.head()


    tempM['Date'] = pd.to_datetime(tempM['Date'], errors='raise')
    tempM['Date'] = pd.to_datetime(tempM['Date'],format='%d/%m/%y', errors='raise')


    # In[270]:


    # test cases / death cases 
    deaths_url ='https://raw.githubusercontent.com/watty62/Scot_covid19/master/data/processed/regional_deaths.csv'
    df_deaths = pd.read_csv(deaths_url)
    df_deaths.head()

    df_deaths.drop(df_deaths.loc[:, 'Ayrshire and Arran':'Western Isles'].columns, axis = 1,inplace=True) 
    df_deaths.columns=['Date','Deaths']
    #df_deaths = df_deaths.set_index(["Date"])

    #df_deaths.head(30)
    ## load file 
    url_test ='https://raw.githubusercontent.com/watty62/Scot_covid19/master/data/processed/scot_tests.csv'
    test_cases = pd.read_csv(url_test)

    #test_cases.tail(5)
    #test_cases = test_cases.set_index(["Date"])
    df_deaths = df_deaths.set_index('Date')

    test_cases = test_cases.set_index('Date')
    df_merged = pd.merge(test_cases, df_deaths, on='Date',how='left')

    #test_cases = test_cases.merge(df_deaths,on='Date',how="left")
    test_cases = df_merged.reset_index()
    test_cases['Deaths'] = test_cases['Deaths'].fillna(0)
    test_cases['Date'] = pd.to_datetime(test_cases['Date'], errors='raise')


    cases_grouped = tempM.groupby('Region')['Confirmed'].max().reset_index()
    cases_grouped = cases_grouped.sort_values(by='Confirmed', ascending=False)
    cases_grouped = cases_grouped.reset_index(drop=True)

    cases_grouped.style.background_gradient(cmap='Reds')
    return tempM, test_cases, cases_grouped,df_deaths,nat_cases_df

def plot_totals_today(byDate='01-04-2020',bar = True,line=False):
    # Cumulative numbers of confirmed cases in Scotland over time 
    byDate =  pd.to_datetime(byDate, errors='raise')
    tempu = tempM[tempM.Date<=byDate].copy()
    temp = tempu.groupby(['Date'])['Confirmed'].sum().reset_index().sort_values('Confirmed', ascending=True)
    if bar: 
        fig = px.bar(temp, x="Date", y="Confirmed", text='Confirmed',title='Confirmed Cases', height=600,
                    template='plotly_white')

        #fig.update_yaxes(type="log")
        t_text = 'In Total ' + str(temp['Confirmed'].max()) + ' Confirmed Cases in (Scotland) ('+str(byDate.strftime("%d/%m/%y"))+')'
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(title_text=t_text, title_x=0.5)
    else: 
        fig = px.line(temp, x="Date", y="Confirmed", text='Confirmed',title='Confirmed Cases', height=600,
                    template='plotly_white')

        #fig.update_yaxes(type="log")
        t_text = 'In Total ' + str(temp['Confirmed'].max()) + ' Confirmed Cases in (Scotland) on '+str(byDate.strftime("%d/%m/%y"))
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_layout(title_text=t_text, title_x=0.5,width=800,height=600)

    return (fig)

# plot daily spread of cases by one ore more regions in scotland 
# can be done as barplot or line plot with/out log scales i.e. 
# plot top four regions as line plots between two specific dates as follows: 
# plot_regions_u(top_ten[:4],2,False,False,'3-30-2020','4-11-2020')
def plot_regions_u(regions='Grampian',facet_cols=2,bar=False,logs=False,startDate='4-1-2020',endDate='4-11-2020'):
    
    temp = tempM.loc[tempM['Region'].isin(regions),:].copy()
    #temp = covid19[(covid19.Country.isin(countries))].copy()
    temp['Date'] = pd.to_datetime(temp['Date'])
    

    temp = temp.groupby(['Date', 'Region'])['Confirmed'].sum().reset_index().sort_values('Confirmed', ascending=True)
    #temp['Daily'] = temp[cases].diff()
    #temp['Daily']=0
    mask = (temp['Date'] >= pd.to_datetime(startDate))&(temp['Date'] <= pd.to_datetime(endDate))
    temp = temp.loc[mask]
    temp.sort_values(by=['Region', 'Date'])

    temp['Daily'] = temp.groupby('Region')['Confirmed'].diff()
    
    #temp.fillna(0,inplace=True)

    
    if (bar==False):
        fig = px.line(temp, x="Date", y='Daily', color='Region',  height=500,
           facet_col='Region', facet_col_wrap=facet_cols,template='plotly_white')
    else:
        fig = px.bar(temp, x="Date", y='Daily', color='Region',  height=400,
           facet_col='Region', facet_col_wrap=facet_cols,template='plotly_white',text=temp['Daily'])
        fig.update_traces(texttemplate='%{text:.2s}', textposition='auto')

    #fig.update_yaxes(type="log")
    if (logs==True):
        fig.update_yaxes(type="log")

        
    title = 'Daily spread across top ' + str(len(regions)) + ' regions ' + 'between '+ str(start_date.strftime("%d/%m/%y")) + ' and '+str(endDate.strftime("%d/%m/%y"))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_xaxes(tickangle=90)
    fig.update_layout(xaxis_title="Date",yaxis_title="Daily Count",width=900,height=700)
    fig.update_layout(title_text=title, title_x=0.5)
    return(fig)



#test_cases.tail(10)
tempM, test_cases,cases_grouped,df_deaths,nat_cases_df = load_prepare_data()
# get the date of the latest update 
byDate = nat_cases_df.iloc[nat_cases_df.shape[0]-1][0]
# regions sorted by total numer 
top_ten = cases_grouped['Region'].to_list()


def plot_confirmed_tests(date =byDate,bar=True):
    
    #date = pd.to_datetime(tempM['Date'],format='%d/%m/%y', errors='raise')
    # show number of tests per day against confirmed cases 
    test_ = test_cases[test_cases.Date<=date].copy()
    fig = go.Figure()

    if bar:

        fig.add_trace(go.Bar(
            x=test_['Date'],
            y=test_['Deaths'],
            name="Total deaths (cumulative)",
            #mode='lines+markers'
        ))

        fig.add_trace(go.Bar(
            x=test_['Date'],
            y=test_['Today Positive'],
            name="Daily Confirmed Cases",
            #mode='lines+markers'
        ))
        fig.add_trace(go.Bar(
            x=test_['Date'],
            y=test_['Conducted'],
            name="Daily Number of Tests",
            #mode='lines+markers'
        ))

    else:

        fig.add_trace(go.Scatter(
            x=test_['Date'],
            y=test_['Deaths'],
            name="Total deaths (cumulative)",
            #mode='lines+markers'
        ))

        fig.add_trace(go.Scatter(
            x=test_['Date'],
            y=test_['Today Positive'],
            name="Daily Confirmed Cases",
            #mode='lines+markers'
        ))
        fig.add_trace(go.Scatter(
            x=test_['Date'],
            y=test_['Conducted'],
            name="Daily Number of Tests",
            #mode='lines+markers'
        ))

    #fig.update_layout(barmode='group')
    fig.update_layout(template='plotly_white',width=900,height=700)
    fig.update_layout(title_text="Number of Tests VS Confirmed Cases on "+str(date.strftime("%d/%m/%y")), title_x=0.5)
    return fig

# load and prepare data 

### Initial Variables 
# some data checking must be done (i.e. start date < end date and so on)
start_date = st.sidebar.date_input('Date')


## write an intro paragraph in the main page 


st.markdown('Total number of confirmed Cases in Scotland is<strong> ' + 
    str(np.sum(cases_grouped['Confirmed'])) +'</strong>, on ' +' <strong>' + str(byDate)+
    '</strong> '+'. Data is collected from https://github.com/watty62/Scot_covid19, repo prepared by Ian Watt. Number of cases /region are as follows:',True)

# sidebar input to control number of regions in the table

### total numbers over time 

bar_chart = st.sidebar.checkbox('Confirmed Cases (change start to see results over time')


def plot_bar_totals(start_date ='1-1-2020',bar=True,line=False):
    if bar_chart:
        st.subheader('Confirmed Cases over time')

        fig = plot_totals_today(start_date, bar,line)
        #streamlit 
        st.plotly_chart(fig) 




regions = st.sidebar.checkbox('Regions (Tabluated results)')

def list_regions(n_region=5):
    cases_grouped = tempM.groupby('Region')['Confirmed'].max().reset_index()
    cases_grouped = cases_grouped.sort_values(by='Confirmed', ascending=False)
    cases_grouped = cases_grouped.reset_index(drop=True)

    top_ten = cases_grouped['Region'].to_list()
    if regions:
        st.subheader('Regions by Number of Confirmed Cases ')
        number_s = st.sidebar.number_input('Number of regions',1,len(top_ten),5)
        st.write(cases_grouped[:number_s].style.background_gradient(cmap='Reds'))
# show top 10 regions by


regions_daily = st.sidebar.checkbox('Regions Daily spread')
# line or bar plots 
plot_types = st.sidebar.radio("Plot type", 
    ['barplot','Lineplot'])

# call the above function 
bar = (plot_types=='barplot')
line = (plot_types=='Lineplot')
######################

# needs improvement to take the various parameters instead of hard-coding it
def plot_daily_regions_spread(start_date,bar=True,line=False):

    if regions_daily:
        st.subheader('By Regions (Daily spread)')
        end_date = st.sidebar.date_input('End Date')
        if start_date >= end_date:
            st.error('Make sure end date falls after start date.')

        number_s = st.sidebar.number_input('Number of regions to show',1,len(top_ten),5)
        fig = plot_regions_u(top_ten[:number_s],4,
            bar,line,start_date,end_date)
        st.plotly_chart(fig)

daily_tests = st.sidebar.checkbox('Daily Tests - Cases')

def plot_daily_tests(bydate = date.today(),barline=True):
    if daily_tests:
        barline=bar
        end_date = st.sidebar.date_input('By Date')
        fig = plot_confirmed_tests(end_date,barline)
        st.plotly_chart(fig)

plot_bar_totals(start_date,bar,line)

list_regions(10)
plot_daily_regions_spread(start_date,bar,line)
plot_daily_tests(byDate,bar)

#st.write(tempM)
#### plot commulative sums 

