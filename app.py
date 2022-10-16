from dash import Dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_daq as daq
from datetime import datetime
import pandas as pd
import json
import pytz

import ui_text as constant
import functions as f


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# --- PRELOADING DATA ---
# rule for the file names: outlier_detection_method + "_" + grouped/not_grouped + "_" + moodle_course
data_dir_path = "data/"
dict_of_df = f.preload_data(data_dir_path)

# --- ESTABLISH SETTING OPTIONS ---
initial_df = dict_of_df["outliers_global"]["grouped"]
min_date = datetime.fromtimestamp(initial_df.min()["Unix_Time"], tz=pytz.timezone("Europe/Rome")).replace(hour=0, minute=0, second=0, microsecond=0)
max_date = datetime.fromtimestamp(initial_df.max()["Unix_Time"], tz=pytz.timezone("Europe/Rome")).replace(hour=0, minute=0, second=0, microsecond=0)

# ------ ARRANGE COMPONENTS ------
app.layout = html.Div([
  html.Div([
    html.Div([
      html.Div([
        html.P(children = constant.moodle_course_text),
        dcc.Dropdown(options = constant.moodle_courses, 
                     value = [],
                     multi = True,
                     placeholder = constant.moodle_course_placeholder,
                     id = "moodle-course-toggle")
      ]),

      html.Div([
        html.P(children = constant.select_period_text),
        dcc.DatePickerRange(id = "observation-range",
                            min_date_allowed = constant.min_date_allowed,
                            max_date_allowed = constant.max_date_allowed,
                            start_date = min_date,
                            end_date = max_date,
                            display_format = "MMM Do YYYY")        
      ], style = {"margin-top": "5pt"})      
    ], style = {"width": "23%", "padding": "5pt", "outline": "double #8285af"}),

    html.Div([
      html.Div([
        html.P(children = constant.activity_or_task_text),
        dcc.RadioItems(options = constant.activity_or_task, 
                       value = "task", 
                       id = "activity-task-toggle")
      ]),

      html.Div([
        html.P(children = constant.temporal_text),
        dcc.RadioItems(options = constant.temporal, 
                       value = "time-off-task", 
                       id = "outlier-detection-toggle")
      ], style = {"margin-top": "5pt"}),     
    ], style = {"width": "20%", "padding": "5pt", "outline": "double #8285af", "margin-left": "10pt"}),

    html.Div([
      html.Div([
        html.P(children = constant.type_of_session_text),
        dcc.RadioItems(options = constant.types_of_session, 
                     value = "session_study", 
                     id = "type-of-session-toggle")
      ])        
    ], style = {"width": "10%", "margin-left": "10pt", "padding": "5pt"}),

    html.Div([
      html.Div([
        html.P(children = constant.study_session_identification_text),
        dcc.Dropdown(options = constant.study_session_identification_options,
                     value = ["authentication", "stt"],
                     multi = True,
                     id = "study-session-identification-toggle")
      ]),

      html.Div([
        dcc.Checklist(options = constant.check_list_options,
                      value = [],
                      id = "check-list-toggle")
      ], style = {"margin-top": "5pt"})
    ], style = {"width": "30%", "margin-left": "10pt", "padding": "5pt"})     
  ], style = {"display": "flex", "margin-left": "10pt", "margin-top": "5pt"}),

  html.Div([
    html.Div([
      html.P(children = constant.general_threshold_text),
      dcc.Input(id = "time-off-task-threshold",
                type = "number",
                placeholder = constant.general_threshold_placeholder),
      html.Div(children = "", style = {"color": "#8b8b8b", "font-size": "smaller"}, id = "general-threshold-suggestion")
    ], id = "general-time-off-task-div", style = {"width": "20%", "visibility": "hidden"}),

    html.Div([
      html.Div([
        html.P(children = constant.select_component),
        dcc.Dropdown(options = [], 
                     value = [], 
                     id = "components-toggle"),
        html.Div(children = "", style = {"color": "#8b8b8b", "font-size": "smaller"}, id = "component-threshold-suggestion")
      ], style = {"width": "27%"}),

      html.Div([
        html.Div([
          html.P(children = constant.component_threshold_text),
          dcc.Input(id = "component-time-off-task-threshold",
                    type = "number",
                    placeholder = constant.component_threshold_placeholder)
        ]),

        html.Div([
          html.Button(constant.button_text, id = "add-component-threshold")
        ], style = {"margin-top": "5pt"})
      ], style = {"margin-left": "10pt"}),

      html.Div([
        dcc.Dropdown(options = [], 
                     value = [],
                     multi = True,
                     placeholder = constant.active_component_thresholds_text,
                     id = "active-component-thresholds")
      ], style = {"margin-left": "10pt", "width": "40%"})        
    ], id = "component-time-off-task-div", style = {"width": "70%", "display": "inline-flex", "border-left": "2px solid #9fa1a8", "padding-left": "5pt", "visibility": "hidden"})            
  ], style = {"display": "flex", "margin-left": "10pt", "margin-top": "5pt"}),

  html.Div([
    html.Div([dcc.Graph(id = "session-box-plot")])         
  ], style = {"width": "85%"}),

  # dcc.Store stores the intermediate value
  dcc.Store(id="pause-info")
])

@app.callback(
    Output(component_id = "session-box-plot", component_property = "figure"),
    Input(component_id = "observation-range", component_property = "start_date"),
    Input(component_id = "observation-range", component_property = "end_date"),
    Input(component_id = "moodle-course-toggle", component_property = "value"),
    Input(component_id = "type-of-session-toggle", component_property = "value"),
    Input(component_id = "outlier-detection-toggle", component_property = "value"),
    Input(component_id = "activity-task-toggle", component_property = "value"),
    Input(component_id = "study-session-identification-toggle", component_property = "value"),
    Input(component_id = "check-list-toggle", component_property = "value"),
    Input(component_id = "time-off-task-threshold", component_property = "value"),
    Input(component_id = "add-component-threshold", component_property = "n_clicks"),
    Input(component_id = "active-component-thresholds", component_property = "value"),
    State(component_id = "components-toggle", component_property = "value"),
    State(component_id = "component-time-off-task-threshold", component_property = "value"), prevent_initial_call=True)
def update_plot(observation_start_date,
                observation_end_date,
                moodle_course,
                type_of_session,
                outlier_detection_toggle,
                activity_task_toggle,
                study_session_identification,
                check_list,
                time_off_task_threshold,
                add_button,
                active_component_thresholds,
                component_toggle,
                component_time_off_task_threshold):
  # --- PROCESS SETTINGS ---
  # now outlier method selection is hidden => we need to fix it manually here
  outlier_detection_method = "outliers_global"
  outlier_detection_switch = True if outlier_detection_toggle == "time-off-task" else False
  group_logs_status = "grouped" if activity_task_toggle == "task" else "not_grouped"
  is_general_research = len(moodle_course) == 0
  # moodle_course = ["All"] if is_general_research else moodle_course
  del_attendance_session_flag = "del_only_attendance" in check_list
  # load existing information about component's threshold
  active_component_threshold_dict = f.transform_active_components_options_to_dict(active_component_thresholds) if not is_general_research else {}
  # add new component's threshold
  if add_button is not None:
    if component_toggle is not None and component_time_off_task_threshold is not None:
      active_component_threshold_dict[component_toggle] =  component_time_off_task_threshold

  # --- GET DATA ACCORDING TO SETTINGS ---
  chosen_df = f.get_chosen_df(dict_of_df, observation_start_date, observation_end_date, outlier_detection_method, group_logs_status) 
  learning_sessions, final_pause_analysis = f.get_study_session_time_periods(chosen_df, moodle_course, type_of_session, study_session_identification, del_attendance_session_flag, outlier_detection_switch, time_off_task_threshold, active_component_threshold_dict)
  
  # --- PLOT THE DATA ---
  data = f.get_data_for_boxplot(learning_sessions)
  fig = f.plot_boxplot(data)
  
  return fig

@app.callback(
    Output(component_id = "pause-info", component_property = "data"),
    Input(component_id = "observation-range", component_property = "start_date"),
    Input(component_id = "observation-range", component_property = "end_date"),
    Input(component_id = "activity-task-toggle", component_property = "value"),
    Input(component_id = "moodle-course-toggle", component_property = "value"),
    Input(component_id = "type-of-session-toggle", component_property = "value"))
def update_pase_analysis_info(observation_start_date,
                              observation_end_date,
                              activity_task_toggle,
                              moodle_course,
                              type_of_session):
  # --- PROCESS SETTINGS ---
  # now outlier method selection is hidden => we need to fix it manually here
  outlier_detection_method = "outliers_global"
  group_logs_status = "grouped" if activity_task_toggle == "task" else "not_grouped"

  # --- GET DATA ACCORDING TO SETTINGS ---
  chosen_df = f.get_chosen_df(dict_of_df, observation_start_date, observation_end_date, outlier_detection_method, group_logs_status)
  learning_sessions, final_pause_analysis = f.get_study_session_time_periods(chosen_df, moodle_course, type_of_session, ["stt"], False, True, 0, {})
  return json.dumps(final_pause_analysis)

@app.callback(
    Output(component_id = "general-time-off-task-div", component_property = "style"),
    Output(component_id = "general-threshold-suggestion", component_property = "children"),
    Output(component_id = "component-time-off-task-div", component_property = "style"),
    Output(component_id = "components-toggle", component_property = "options"),
    Output(component_id = "add-component-threshold", component_property = "n_clicks"),
    Output(component_id = "active-component-thresholds", component_property = "options"),
    Output(component_id = "active-component-thresholds", component_property = "value"),
    Input(component_id = "pause-info", component_property = "data"),
    Input(component_id = "outlier-detection-toggle", component_property = "value"),
    Input(component_id = "study-session-identification-toggle", component_property = "value"),
    Input(component_id = "add-component-threshold", component_property = "n_clicks"),
    Input(component_id = "active-component-thresholds", component_property = "value"),
    State(component_id = "moodle-course-toggle", component_property = "value"),
    State(component_id = "type-of-session-toggle", component_property = "value"),
    State(component_id = "components-toggle", component_property = "value"),
    State(component_id = "component-time-off-task-threshold", component_property = "value"), prevent_initial_call=True)
def update_options(pause_info,
                   outlier_detection_toggle,
                   study_session_identification,
                   add_button,
                   active_component_thresholds,
                   moodle_course,
                   type_of_session,
                   component_toggle,
                   component_time_off_task_threshold):
  # --- PROCESS SETTINGS ---
  # load existing information about component's threshold
  active_component_threshold_dict = f.transform_active_components_options_to_dict(active_component_thresholds) # if not len(moodle_course) == 0 else {}
  # add new component's threshold
  if add_button is not None:
    if component_toggle is not None and component_time_off_task_threshold is not None:
      active_component_threshold_dict[component_toggle] = component_time_off_task_threshold
  outlier_detection_switch = True if outlier_detection_toggle == "time-off-task" else False

  # --- UPDATE VISUALIZATION PART ---
  active_component_thresholds = f.transform_active_components_dict_to_options(active_component_threshold_dict)

  final_pause_analysis = json.loads(pause_info)
  moodle_course = constant.moodle_courses_values if len(moodle_course) == 0 else moodle_course
  general_time_off_task, general_time_off_task_suggestion = f.get_general_time_off_task_update(final_pause_analysis, type_of_session, moodle_course, study_session_identification, outlier_detection_switch)
  component_time_off_task, component_options = f.get_component_time_off_task_update(study_session_identification, moodle_course, type_of_session)
  return general_time_off_task, general_time_off_task_suggestion, component_time_off_task, component_options, None, active_component_thresholds, active_component_thresholds

@app.callback(
    Output(component_id = "component-threshold-suggestion", component_property = "children"),
    Input(component_id = "components-toggle", component_property = "value"),
    Input(component_id = "pause-info", component_property = "data"),
    State(component_id = "type-of-session-toggle", component_property = "value"),
    State(component_id = "outlier-detection-toggle", component_property = "value"), prevent_initial_call=True)
def update_components_threshold(component_toggle,
                                pause_info,
                                type_of_session,
                                outlier_detection_toggle):
  final_pause_analysis = json.loads(pause_info)
  outlier_detection_switch = True if outlier_detection_toggle == "time-off-task" else False
  component_time_off_task_suggestion = f.get_component_time_off_task_suggestion(final_pause_analysis, type_of_session, outlier_detection_switch, component_toggle)
  return component_time_off_task_suggestion

if __name__ == "__main__":
  app.run_server(debug=True)