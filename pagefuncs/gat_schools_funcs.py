import streamlit as st

import pygsheets as pygs
from google.oauth2 import service_account

import numpy as np
### credentials
from creds.credpointers import pysheet_creds,SCOPES,pysheet_customcreds

# input data and apply color scheme for geographical scatter plot
@st.cache(allow_output_mutation=True,hash_funcs={service_account.Credentials: lambda _: None})
def data_load(creds=pysheet_customcreds):
    gc = pygs.authorize(custom_credentials=pysheet_customcreds)
    sh = gc.open('schooldistricts_enrollment_and_gat')
    df_in = sh[0].get_as_df().copy()
    df_in = df_in[~df_in["LON"].isna()]
    df_in = df_in[df_in["total_enr"] > 0]
    df_in["coordinates"] = list(zip(df_in["LON"],df_in["LAT"]))
    df_in["enr_radius"] = df_in["total_enr"].apply(lambda x: np.sqrt(max(x,1000)))
    df_in = df_in.drop(columns=["CBSA"])
    df_in["enr_todisplay"] = df_in["total_enr"].apply(lambda x: '{:,d}'.format(x))
    df_in["gatpct"] = df_in["total_gat"]/df_in["total_enr"]
    df_in["gatpct_todisplay"] = df_in["gatpct"].apply(lambda x: '{:.2%}'.format(x))
    
    YlOrRd = [[1.0*(100-x)/100 + 245/255.0*x/100,
               1.0*(100-x)/100 + 141/255.0*x/100, 
               204/255.0*(100-x)/100 + 60/255.0*x/100] for x in range(101)]
    YlOrRd += [[245/255.0*(100-x)/100 + 128/255.0*x/100,
               141/255.0*(100-x)/100 + 0.0*x/100, 
               60/255.0*(100-x)/100 + 38/255.0*x/100] for x in range(101)][1:]

    YlOrRd = [[1.0*(100-x)/100 + 245/255.0*x/100,
               1.0*(100-x)/100 + 141/255.0*x/100, 
               204/255.0*(100-x)/100 + 60/255.0*x/100] for x in range(101)]
    YlOrRd += [[245/255.0*(100-x)/100 + 245/255.0*x/100,
               141/255.0*(100-x)/100 + 0/255.0*x/100, 
               60/255.0*(100-x)/100 + 60/255.0*x/100] for x in range(101)][1:]
    
    cmap = [[y*255 for y in x] for x in YlOrRd]
    
    df_in["gatpct_r"] = df_in["gatpct"].apply(lambda x: cmap[min(4*int(x*(len(cmap)-1)),len(cmap)-1)][0])
    df_in["gatpct_g"] = df_in["gatpct"].apply(lambda x: cmap[min(4*int(x*(len(cmap)-1)),len(cmap)-1)][1])
    df_in["gatpct_b"] = df_in["gatpct"].apply(lambda x: cmap[min(4*int(x*(len(cmap)-1)),len(cmap)-1)][2])
    
    
    state_df = df_in.groupby(by="state_2dig").agg({"state_name":"max","LAT":"mean","LON":"mean"})
    state_df_se = df_in.groupby(by="state_2dig").agg({"state_name":"max","LAT":"std","LON":"std"})
    state_latlon_dict = {}
    for ind in state_df.index:
        state_latlon_dict[state_df["state_name"][ind]] = {}
        state_latlon_dict[state_df["state_name"][ind]]["lat"] = state_df["LAT"][ind]
        state_latlon_dict[state_df["state_name"][ind]]["lon"] = state_df["LON"][ind]
        state_latlon_dict[state_df["state_name"][ind]]["lat_std"] = state_df_se["LAT"][ind]
        state_latlon_dict[state_df["state_name"][ind]]["lon_std"] = state_df_se["LON"][ind]
    
    sorted_districts = list(df_in["district_name"].unique())
    sorted_districts.sort()
    district_latlon_dict = {}
    for ind in df_in.index:
        district_latlon_dict[df_in["district_name"][ind]] = {}
        district_latlon_dict[df_in["district_name"][ind]]["lat"] = df_in["LAT"][ind]
        district_latlon_dict[df_in["district_name"][ind]]["lon"] = df_in["LON"][ind]

    return df_in,state_latlon_dict,district_latlon_dict,list(state_latlon_dict.keys()),list(district_latlon_dict.keys())

