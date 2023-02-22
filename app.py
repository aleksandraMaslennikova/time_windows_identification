from dash import Dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
from datetime import datetime
import json
import pytz

import ui_text
import constants
import functions_ui
import functions_algorithm


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# ---------------------------
# --- PRELOADING DATASETS ---
# ---------------------------

dict_of_df = functions_ui.preload_data()
# global variables used in the algorithm and ui extracted from the datasets
df = dict_of_df["task_granularity"]
site_area_components = df.loc[df["Course_Area"].isin(constants.site_area)]["Component"].unique()
course_components = {}
courses = []
for course_dict in constants.specific_moodle_course_filter:
    course = course_dict["value"]
    courses.append(course)
    course_components[course] = list(df.loc[df["Course_Area"] == course]["Component"].unique())

# -----------------------------------------
# --- ESTABLISH INITIAL SETTING OPTIONS ---
# -----------------------------------------

initial_df = dict_of_df["task_granularity"]
min_date = datetime.fromtimestamp(initial_df.min()["Unix_Time"], tz=pytz.timezone("Europe/Rome"))\
                   .replace(hour=0, minute=0, second=0, microsecond=0)
max_date = datetime.fromtimestamp(initial_df.max()["Unix_Time"], tz=pytz.timezone("Europe/Rome"))\
                    .replace(hour=0, minute=0, second=0, microsecond=0)

# ----------------------------------------------
# --- LAYOUT (VISUALLY COMPONENT OF THE APP) ---
# ----------------------------------------------

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.P(children=ui_text.select_specific_moodle_course_filter_label),
                dcc.Dropdown(options=constants.specific_moodle_course_filter,
                             value=[],
                             multi=True,
                             placeholder=ui_text.select_specific_moodle_course_filter_placeholder,
                             id="specific-moodle-course-filter-toggle")
            ]),

            html.Div([
                html.P(children=ui_text.select_specific_period_label),
                dcc.DatePickerRange(id="observation-range",
                                    min_date_allowed=constants.min_date_allowed,
                                    max_date_allowed=constants.max_date_allowed,
                                    start_date=min_date,
                                    end_date=max_date,
                                    display_format="MMM Do YYYY")
            ], style={"margin-top": "5pt"})
        ], style={"width": "23%", "padding": "5pt", "outline": "double #8285af"}),

        html.Div([
            html.Div([
                html.P(children=ui_text.activity_or_task_label),
                dcc.RadioItems(options=ui_text.activity_or_task_options,
                               value="task_granularity",
                               id="activity-task-toggle")
            ]),

            html.Div([
                html.P(children=ui_text.temporal_metric_label),
                dcc.RadioItems(options=ui_text.temporal_metric_options,
                               value="time-off-task",
                               id="temporal-metric-toggle")
            ], style={"margin-top": "5pt"}),
        ], style={"width": "20%", "padding": "5pt", "outline": "double #8285af", "margin-left": "10pt"}),

        html.Div([
            html.Div([
                html.P(children=ui_text.type_of_session_label),
                dcc.RadioItems(options=ui_text.type_of_session_options,
                               value="session_study",
                               id="type-of-session-toggle")
            ])
        ], style={"width": "10%", "margin-left": "10pt", "padding": "5pt"}),

        html.Div([
            html.Div([
                html.P(children=ui_text.study_session_identification_label),
                dcc.Dropdown(options=ui_text.study_session_identification_options,
                             value=["authentication", "stt"],
                             multi=True,
                             id="study-session-identification-toggle")
            ]),

            html.Div([
                dcc.Checklist(options=ui_text.check_list_options,
                              value=[],
                              id="check-list-toggle")
            ], style={"margin-top": "5pt"})
        ], style={"width": "30%", "margin-left": "10pt", "padding": "5pt"})
    ], style={"display": "flex", "margin-left": "10pt", "margin-top": "5pt"}),

    html.Div([
        html.Div([
            html.P(children=ui_text.general_session_timeout_threshold_label),
            dcc.Input(id="general-session-timeout-threshold",
                      type="number",
                      placeholder=ui_text.general_session_timeout_threshold_placeholder),
            html.Div(children="",
                     style={"color": "#8b8b8b", "font-size": "smaller"},
                     id="general-session-timeout-threshold-suggestion")
        ], id="general-session-timeout-threshold-div",
           style={"width": "20%", "visibility": "hidden"}),

        html.Div([
            html.Div([
                html.P(children=ui_text.select_component_label),
                dcc.Dropdown(options=[],
                             value=[],
                             id="components-toggle"),
                html.Div(children="",
                         style={"color": "#8b8b8b", "font-size": "smaller"},
                         id="component-session-timeout-threshold-suggestion")
            ], style={"width": "27%"}),

            html.Div([
                html.Div([
                    html.P(children=ui_text.component_session_timeout_threshold_label),
                    dcc.Input(id="component-session-timeout-threshold",
                              type="number",
                              placeholder=ui_text.component_session_timeout_threshold_placeholder)
                ]),

                html.Div([
                    html.Button(ui_text.component_session_timeout_threshold_button_text,
                                id="component-add-session-timeout-threshold")
                ], style={"margin-top": "5pt"})
            ], style={"margin-left": "10pt"}),

            html.Div([
                dcc.Dropdown(options=[],
                             value=[],
                             multi=True,
                             placeholder=ui_text.component_active_session_timeout_thresholds_placeholder,
                             id="component-active-session-timeout-thresholds")
            ], style={"margin-left": "10pt", "width": "40%"})
        ], id="component-session-timeout-threshold-div",
           style={"width": "70%", "display": "inline-flex", "border-left": "2px solid #9fa1a8", "padding-left": "5pt",
                  "visibility": "hidden"})
    ], style={"display": "flex", "margin-left": "10pt", "margin-top": "5pt"}),

    html.Div([
        html.Div([dcc.Graph(id="session-spread-box-plot")])
    ], style={"width": "85%"}),

    # dcc.Store stores the intermediate value
    dcc.Store(id="pause-info")
])

# -----------------------------------------
# --- CALLBACKS (THE APP FUNCTIONALITY) ---
# -----------------------------------------

@app.callback(
    Output(component_id="session-spread-box-plot", component_property="figure"),
    Input(component_id="observation-range", component_property="start_date"),
    Input(component_id="observation-range", component_property="end_date"),
    Input(component_id="specific-moodle-course-filter-toggle", component_property="value"),
    Input(component_id="type-of-session-toggle", component_property="value"),
    Input(component_id="temporal-metric-toggle", component_property="value"),
    Input(component_id="activity-task-toggle", component_property="value"),
    Input(component_id="study-session-identification-toggle", component_property="value"),
    Input(component_id="check-list-toggle", component_property="value"),
    Input(component_id="general-session-timeout-threshold", component_property="value"),
    Input(component_id="component-add-session-timeout-threshold", component_property="n_clicks"),
    Input(component_id="component-active-session-timeout-thresholds", component_property="value"),
    State(component_id="components-toggle", component_property="value"),
    State(component_id="component-session-timeout-threshold", component_property="value"), prevent_initial_call=True)
def update_plot(observation_start_date,
                observation_end_date,
                specific_moodle_course,
                type_of_session,
                temporal_metric_toggle,
                activity_task_toggle,
                study_session_identification,
                check_list,
                general_stt,
                component_add_stt_button,
                component_active_stt,
                current_component_selection,
                component_stt):
    # --- PROCESS SETTINGS ---
    outlier_detection_switch = True if temporal_metric_toggle == "time-off-task" else False
    del_attendance_session_flag = "del_only_attendance" in check_list
    authentication_flag = "authentication" in study_session_identification
    stt_flag = "stt" in study_session_identification
    # load existing information about previously assigned component thresholds
    active_component_stt_dict = functions_ui.transform_active_components_options_to_dict(component_active_stt)
    # if the callback was initiated by adding new component threshold, add it the component thresholds dictionary
    if component_add_stt_button is not None:
        if current_component_selection is not None and component_stt is not None:
            active_component_stt_dict[current_component_selection] = component_stt

    # --- GET DATA ACCORDING TO SETTINGS ---
    chosen_df = functions_ui.get_chosen_df(dict_of_df,
                                           observation_start_date,
                                           observation_end_date,
                                           activity_task_toggle)
    learning_sessions, final_pause_analysis = functions_algorithm.get_session_time_periods(chosen_df,
                                                                                           specific_moodle_course,
                                                                                           type_of_session,
                                                                                           authentication_flag,
                                                                                           stt_flag,
                                                                                           del_attendance_session_flag,
                                                                                           outlier_detection_switch,
                                                                                           general_stt,
                                                                                           active_component_stt_dict)

    # --- PLOT THE DATA ---
    data = functions_ui.get_data_for_boxplot(learning_sessions)
    fig = functions_ui.plot_boxplot(data)

    return fig


@app.callback(
    Output(component_id="pause-info", component_property="data"),
    Input(component_id="observation-range", component_property="start_date"),
    Input(component_id="observation-range", component_property="end_date"),
    Input(component_id="activity-task-toggle", component_property="value"),
    Input(component_id="specific-moodle-course-filter-toggle", component_property="value"),
    Input(component_id="type-of-session-toggle", component_property="value"))
def update_pause_analysis_info(observation_start_date,
                               observation_end_date,
                               activity_task_toggle,
                               moodle_course,
                               type_of_session):
    # --- GET DATA ACCORDING TO SETTINGS ---
    chosen_df = functions_ui.get_chosen_df(dict_of_df,
                                           observation_start_date,
                                           observation_end_date,
                                           activity_task_toggle)
    learning_sessions, final_pause_analysis = functions_algorithm.get_session_time_periods(chosen_df,
                                                                                           moodle_course,
                                                                                           type_of_session,
                                                                                           authentication_flag=False,
                                                                                           stt_flag=True,
                                                                                           del_attendance_session_flag=False,
                                                                                           outlier_detection_switch=True,
                                                                                           general_stt=0,
                                                                                           active_component_stt_dict={})
    return json.dumps(final_pause_analysis)


@app.callback(
    Output(component_id="general-session-timeout-threshold-div", component_property="style"),
    Output(component_id="general-session-timeout-threshold-suggestion", component_property="children"),
    Output(component_id="component-session-timeout-threshold-div", component_property="style"),
    Output(component_id="components-toggle", component_property="options"),
    Output(component_id="component-add-session-timeout-threshold", component_property="n_clicks"),
    Output(component_id="component-active-session-timeout-thresholds", component_property="options"),
    Output(component_id="component-active-session-timeout-thresholds", component_property="value"),
    Input(component_id="pause-info", component_property="data"),
    Input(component_id="temporal-metric-toggle", component_property="value"),
    Input(component_id="study-session-identification-toggle", component_property="value"),
    Input(component_id="component-add-session-timeout-threshold", component_property="n_clicks"),
    Input(component_id="component-active-session-timeout-thresholds", component_property="value"),
    State(component_id="specific-moodle-course-filter-toggle", component_property="value"),
    State(component_id="type-of-session-toggle", component_property="value"),
    State(component_id="components-toggle", component_property="value"),
    State(component_id="component-session-timeout-threshold", component_property="value"), prevent_initial_call=True)
def update_options(pause_info,
                   outlier_detection_toggle,
                   study_session_identification,
                   add_button,
                   active_component_stt,
                   moodle_course,
                   type_of_session,
                   component_toggle,
                   component_session_timeout_threshold):
    # --- PROCESS SETTINGS ---
    # load existing information about component's threshold
    active_component_threshold_dict = functions_ui.transform_active_components_options_to_dict(active_component_stt)
    # add new component's threshold
    if add_button is not None:
        if component_toggle is not None and component_session_timeout_threshold is not None:
            active_component_threshold_dict[component_toggle] = component_session_timeout_threshold
    outlier_detection_switch = True if outlier_detection_toggle == "time-off-task" else False
    moodle_course = courses if len(moodle_course) == 0 else moodle_course

    # --- UPDATE VISUALIZATION PART ---
    active_component_stt = functions_ui.transform_active_components_dict_to_options(active_component_threshold_dict)

    final_pause_analysis = json.loads(pause_info)
    general_stt, general_stt_suggestion = functions_ui.get_general_time_off_task_update(final_pause_analysis,
                                                                                        type_of_session,
                                                                                        study_session_identification,
                                                                                        outlier_detection_switch)
    component_stt, component_options = functions_ui.get_component_time_off_task_update(study_session_identification,
                                                                                       moodle_course,
                                                                                       site_area_components,
                                                                                       course_components,
                                                                                       type_of_session)
    return general_stt, general_stt_suggestion, component_stt, component_options, None, active_component_stt, active_component_stt


@app.callback(
    Output(component_id="component-session-timeout-threshold-suggestion", component_property="children"),
    Input(component_id="components-toggle", component_property="value"),
    Input(component_id="pause-info", component_property="data"),
    State(component_id="type-of-session-toggle", component_property="value"),
    State(component_id="temporal-metric-toggle", component_property="value"), prevent_initial_call=True)
def update_components_threshold(component_toggle,
                                pause_info,
                                type_of_session,
                                outlier_detection_toggle):
    final_pause_analysis = json.loads(pause_info)
    outlier_detection_switch = True if outlier_detection_toggle == "time-off-task" else False
    component_stt_suggestion = functions_ui.get_component_time_off_task_suggestion(final_pause_analysis,
                                                                                   type_of_session,
                                                                                   outlier_detection_switch,
                                                                                   component_toggle)
    return component_stt_suggestion


if __name__ == "__main__":
  app.run_server(debug=True)
