##############################################
# US School Districts and Gifted and Talented (GAT) programs
# developed by Matt Delventhal for AoPS, 12 Sep 2022
#
# Streamlit app which generates interactive map and downloadable data
#   for all US school districts as of 2017-18.
# 
# Source data from US Dept of Education Civil Rights Data Collection.
#
# Already-processed data is loaded from a google sheet.
#
#
#
##############################################

### dependencies
import streamlit as st


import psycopg2
import pandas as pd
import numpy as np

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pydeck as pdk

import altair as alt

import time as time
import datetime as dt



from lib.dbfuncs import convert_df

from pagefuncs.gat_schools_funcs import *

### initialize persistent variables
if "init_zoom" not in st.session_state:
    st.session_state["init_zoom"] = 3
    
if "focus_priority" not in st.session_state:
    st.session_state["focus_priority"] = 0

if "jump_now" not in st.session_state:
    st.session_state["jump_now"] = False

if "focus_lon" not in st.session_state:
    st.session_state["focus_lon"] = -96.75

if "focus_lat" not in st.session_state:
    st.session_state["focus_lat"] = 39

### functions

# prepare dataframe for export to csv


# helper function which tells map view where to jump based on drop-down menu input
def set_focus(inp):
    if st.session_state['jump_now']:
        st.session_state['focus_priority'] = inp

# helper function to prevent view from resetting based on a non-user-initiated change to dropdown menu selection
def stop_jump():
    st.session_state['jump_now'] = False

### load data
main_df,state_latlon_dict,district_latlon_dict,statenames,districtnames = data_load()

### output header and overview text
st.markdown("# U.S. School Districts: Size by Enrollment and Gifted and Talented (GAT) programs")

st.write(
"""Below you can find an interactive map of U.S. school districts.
 - The size of each circle is proportional to the total number of students enrolled in the district.
 - Circles are colored according to what percentage of students participate in Gifted and Talented programs.
You may mouse over each school district for more detailed information. You can also use the controls to filter 
school districts based on size or GAT enrollment, or to jump the map view to focus on a particular state.
"""
    )

### lay our the remainder of the page structure
slidercols = st.columns([10,1,10])
selectbox_cols = st.columns([10,1,10])
st.button("Reset map",on_click=set_focus,args=(0,))
map_container = st.container()
footer_container = st.container()



### Deploy the map figure

### filtering slider bars

# slider to filter by total enrollment
enr_filter_vals = ['{:,d}'.format((x*1000)) for x in range(101)]
enr_filter_vals[-1] = "100,000+"
[min_enr,max_enr] = slidercols[0].select_slider("Filter: total enrollment.",enr_filter_vals,("0","100,000+"),
                                        on_change=stop_jump)

# turn input back into numeric from float
try:
    min_enr = float(min_enr.replace(",",""))
except:
    min_enr = 5000000
try:
    max_enr = float(max_enr.replace(",",""))
except:
    max_enr = 5000000 

# slider to filter by GAT enrollment share
gat_filter_vals = ['{:.0%}'.format(x/100) for x in range(26)]
gat_filter_vals[0] = "0"
gat_filter_vals[-1] = "25% or more"
[min_gat,max_gat] = slidercols[2].select_slider("Filter: share of GAT students.",gat_filter_vals,("0","25% or more"),
                                        on_change=stop_jump)

# turn input back into numeric from float
try:
    min_gat = float(min_gat.replace("%",""))/100.0
except:
    min_gat = 1.0
try:
    max_gat = float(max_gat.replace("%",""))/100.0
except:
    max_gat = 1.0 

# filter data based on user input
filtered_df = main_df.copy()
filtered_df = filtered_df[(filtered_df["total_enr"] >= min_enr) & (filtered_df["total_enr"] <= max_enr)]
filtered_df = filtered_df[(filtered_df["gatpct"] >= min_gat) & (filtered_df["gatpct"] <= max_gat)]

# style a subset of the filtered dataframe for display and download
subds = filtered_df[["district_name","total_enr","gatpct_todisplay","state_2dig","LAT","LON","ZIP"]]


# allow user to select a state to snap the map to
focus_state = selectbox_cols[0].selectbox("Zoom to state:",[""] + statenames,
                            on_change=set_focus,args=(1,))
                            
# allow user to select a district to snap the map to
focus_district = selectbox_cols[2].selectbox("Find district:",[""] + districtnames,
                                on_change=set_focus,args=(2,))


# set initial map center and zoom based on user selections
# when the user selects a new state or district from the drop-down menu, zoom and map focus should correspond to that new selection
# if user has clicked "reset map", should go back to original whole-country view
# otherwise, should be unchanged
if st.session_state['jump_now']:
    if st.session_state["focus_priority"] == 0:
        st.session_state["init_zoom"] = 3
        st.session_state["focus_lat"] = 39
        st.session_state["focus_lon"] = -96.75
    elif st.session_state["focus_priority"] == 1:
        if not focus_state == "":
            st.session_state["init_zoom"] = 5
            st.session_state["focus_lat"] = state_latlon_dict[focus_state]["lat"]
            st.session_state["focus_lon"] = state_latlon_dict[focus_state]["lon"]
            zoomadjust = (np.sqrt(state_latlon_dict[focus_state]["lon_std"]**2 + state_latlon_dict[focus_state]["lat_std"]**2)/3.149513798318698)**.2
            if (not np.isnan(zoomadjust)) and (not np.isinf(zoomadjust)) and (not zoomadjust == 0):
                st.session_state["init_zoom"] /= zoomadjust
    elif st.session_state["focus_priority"] == 2:
        if not focus_district == "":
            st.session_state["init_zoom"] = 9.5
            st.session_state["focus_lat"] = district_latlon_dict[focus_district]["lat"]
            st.session_state["focus_lon"] = district_latlon_dict[focus_district]["lon"]

# viewstate for pydeck map
view_state = pdk.ViewState(
    **{"latitude": st.session_state["focus_lat"], 
    "longitude": st.session_state["focus_lon"], 
    "zoom": st.session_state["init_zoom"], 
    "maxZoom": 12, "pitch": 20, "bearing": 0}
)

# layer for pydeck map
layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_df,
    pickable=True,
    opacity=0.5,
    stroked=True,
    filled=True,
    radius_scale=30,
    radius_min_pixels=.25,
    radius_max_pixels=15,
    line_width_min_pixels=.1,
    get_position="coordinates",
    get_radius="enr_radius",
    get_fill_color=["gatpct_r", "gatpct_g", "gatpct_b"],
    get_line_color=[255, 255, 255],
    auto_highlight=True
)



# tooltip on mouse-over for the geo-scatterplot
tooltip = {"html": '<table border = "1" style="width: 100%;font-size:10px">' +\
                   '<colgoup>' +\
                   '<col span="1" style="width: 50%;">' +\
                   '<col span="1" style="width: 50%;">' +\
                   '</colgroup>' +\
                   '<tbody>' +\
                   '<tr>' +\
                   '<td><b>District name:</b></td>' +\
                   '<td>{district_name}</td>' +\
                   '</tr>' +\
                   '<tr>' +\
                   '<td><b>Total enrollment:</b></td>' +\
                   '<td>{enr_todisplay}</td>' +\
                   '</tr>' +\
                   '<tr>' +\
                   '<td><b>Gifted and Talented Enrollment:</b></td>' +\
                   '<td>{gatpct_todisplay}</td>' +\
                   '</tr>' +\
                   '</tbody></table>',
          "style": {"width":"360px","font-family":"arial"}}

# put elements together into pydeck map
r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style=pdk.map_styles.DARK,
        tooltip=tooltip
    )



# Deploy the Deck.
map_container.pydeck_chart(r)

# reset the "jump now" helper variable, in case it was set to "False" to prevent an unintentional map jump on the current script execution
st.session_state['jump_now'] = True


### footer

footer_container.write("#### Selected data")

# columns for selected data summary + download button
selected_data_summary_cols = footer_container.columns(2)

# display filtered data
footer_container.write(subds)

# summary table for selected data
selected_data_summary_cols[0].markdown(f"""
| Number of districts | Total students |
| --- | --- |
| {len(filtered_df):.0f} | {filtered_df["total_enr"].sum():,d} |
""")

# download button
selected_data_summary_cols[1].download_button(
        label = "Download selected data",
        data=convert_df(subds),
        file_name='schooldistricts_enrollment_and_gat.csv',
        mime='text/csv',
        )
