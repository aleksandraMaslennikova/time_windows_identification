from datetime import datetime, timedelta
import pytz
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import constants
import ui_text
import functions_algorithm


# ---------------------------------------------------------------------------------------------
# --- FUNCTIONS THAT ARE USED TO EXTRACT AND ELABORATE DATA, TRANSFORM IT FOR DISPLAY, ETC. ---
# ---------------------------------------------------------------------------------------------

# --- INITIAL PRELOADING OF THE DATASETS FOR THE FUTURE USE IN THE APP ---  
def preload_data():
    dict_of_df = {}
    # preload all the dataset (with all the granularity options)
    for key in constants.file_names.keys():
        dict_of_df[key] = pd.read_csv(constants.data_dir_path + constants.file_names[key])
    return dict_of_df


# --- ACCORDING TO SETTINGS GET THE REQUIRED PORTION OF THE DATASET ---
def get_chosen_df(dict_of_df, observation_start_date, observation_end_date, activity_task_status):
    # which dataset to use (with activity or task granularity)
    chosen_df = dict_of_df[activity_task_status]
    # only consider rows that represent logs occurred in the defined time period (limit dates included)
    start_date = int(datetime.timestamp(datetime.fromisoformat(observation_start_date)))
    end_date = int(datetime.timestamp(datetime.fromisoformat(observation_end_date) + timedelta(days=1)))
    chosen_df = chosen_df.loc[(chosen_df["Unix_Time"] >= start_date) & (chosen_df["Unix_Time"] < end_date)]
    return chosen_df


# --- TRANSFORMATION OF THE LIST OF ASSIGNED THRESHOLDS FOR SPECIFIC COMPONENTS INTO DICTIONARY
# ({"component_name": assigned_threshold (float)}) ---
def transform_active_components_options_to_dict(options_list):
    # if the user didn't insert any component threshold, the dictionary should be empty
    if options_list is None:
        return {}
    # otherwise the thresholds are stored in the list of strings ("component_name (assigned_threshold min)"),
    # that should be parsed to transform them into dictionary
    res = {}
    for option in options_list:
        temp = option.split(" (")
        res[temp[0]] = float(temp[1].split(" min)")[0])
    return res


# --- TRANSFORMATION OF THE DICTIONARY OF ASSIGNED THRESHOLDS FOR SPECIFIC COMPONENTS INTO LIST
# ({"component_name": assigned_threshold (float)}) ---
def transform_active_components_dict_to_options(options_dict):
    res = []
    for option in options_dict.keys():
        res.append(option + " (" + str(options_dict[option]) + " min)")
    return res


# --- FUNCTION DESCRIPTION ---
def get_data_for_boxplot(learning_sessions):
    starts = []
    starts_unix = []
    ends = []
    ends_unix = []
    for session_times in learning_sessions:
        starts_unix.append(int(session_times[0]))
        start_session = datetime.fromtimestamp(session_times[0], tz=pytz.timezone("Europe/Rome"))
        ends_unix.append(int(session_times[1]))
        end_session = datetime.fromtimestamp(session_times[1], tz=pytz.timezone("Europe/Rome"))
        end_time = end_session.hour + end_session.minute / 60.0
        if start_session.day != end_session.day:
            end_time += 24
        start_session = start_session.hour
        starts.append(start_session)
        ends.append(end_time)
    return pd.DataFrame({"Time of session start": starts,
                         "Unix session start": starts_unix,
                         "Time of session end": ends,
                         "Unix session end": ends_unix})


# --- FUNCTION DESCRIPTION ---
def get_session_duration_info(data,
                              session_start_labels):
    # duration in minutes instead of seconds
    data["Session duration"] = (data["Unix session end"] - data["Unix session start"])/60.0
    # get statistical session's duration information
    hover_data = data.groupby("Time of session start", as_index=False).agg(
        base=("Time of session end", "min"),
        bar=("Time of session end", lambda s: s.max() - s.min()),
        session_start_label=("Time of session start", lambda s: session_start_labels[s.min()]),
        count=("Time of session end", lambda s: "{:,}".format(len(s)).replace(",", " ")),
        session_min=("Session duration", lambda s: round(s.min(), 2)),
        session_lower_fence=("Session duration", lambda s: round(s[s <= (np.percentile(s, 25)
                                                                         - 1.5 * (np.percentile(s, 75)
                                                                                  - np.percentile(s, 25)))].min(), 2)),
        session_q1=("Session duration", lambda s: round(np.percentile(s, 25), 2)),
        session_median=("Session duration", lambda s: round(np.median(s), 2)),
        session_q3=("Session duration", lambda s: round(np.percentile(s, 75), 2)),
        session_upper_fence=("Session duration", lambda s: round(s[s <= (np.percentile(s, 75)
                                                                         + 1.5 * (np.percentile(s, 75)
                                                                                  - np.percentile(s, 25)))].max(), 2)),
        session_max=("Session duration", lambda s: round(s.max(), 2))
    )
    # data in the format necessary for the plot
    custom_data = np.stack((
        hover_data["session_start_label"],
        hover_data["count"],
        hover_data["session_min"],
        hover_data["session_q1"],
        hover_data["session_median"],
        hover_data["session_q3"],
        hover_data["session_max"]
    ), axis=-1)
    return hover_data, custom_data


# --- FUNCTION DESCRIPTION ---
def plot_boxplot(data):
    # plot boxplot data
    fig = px.box(data, x="Time of session start", y="Time of session end", height=550)

    # set plot's title
    title_text = ui_text.plot_title
    fig.update_layout(title={"text": title_text, "y": 0.95, "x": 0.5, "xanchor": "center", "yanchor": "top"})

    # set x and y axis labels
    session_start_labels = {}
    for i in range(10):
        session_start_labels[i] = "0" + str(i) + ":00-0" + str(i) + ":59"
    for i in range(10, 24):
        session_start_labels[i] = str(i) + ":00-" + str(i) + ":59"
    fig.update_layout(xaxis_tickvals=list(np.arange(24)))
    fig.update_layout(xaxis_ticktext=list(session_start_labels.values()))
    fig.update_layout(yaxis_range=[0, 30])
    fig.update_layout(yaxis_tickvals=list(np.arange(30)))
    fig.update_layout(yaxis_ticktext=list(np.arange(24)) + ["24+00", "24+01", "24+02", "24+03", "24+04", "24+05"])

    # add session's duration information
    hover_data, custom_data = get_session_duration_info(data, session_start_labels)
    fig2 = go.Figure(go.Bar(
        x=hover_data["Time of session start"],
        y=hover_data["bar"],
        base=hover_data["base"],
        customdata=custom_data,
        hovertemplate=ui_text.hovertemplate,
        width=0.5,
        opacity=0,
        hoverlabel=dict(bgcolor="#aecdc2")
    ))
    fig.add_traces(fig2.data)
    fig.update_layout(showlegend=False)

    # add green stripes that represent lesson time
    fig.update_layout(shapes=[dict(type="rect", xref="x", yref="y", x0="8.5", y0="0", x1="12.5", y1="31",
                                   fillcolor="green", opacity=0.25, line_width=0, layer="below"),
                              dict(type="rect", xref="x", yref="y", x0="13.5", y0="0", x1="17.5", y1="31",
                                   fillcolor="green", opacity=0.25, line_width=0, layer="below"),
                              dict(type="rect", xref="x", yref="y", x0="-0.6", y0="9", x1="24", y1="13",
                                   fillcolor="green", opacity=0.25, line_width=0, layer="below"),
                              dict(type="rect", xref="x", yref="y", x0="-0.6", y0="14", x1="24", y1="18",
                                   fillcolor="green", opacity=0.25, line_width=0, layer="below")])
    return fig


# --- FUNCTION DESCRIPTION ---
def get_general_time_off_task_update(final_pause_analysis, type_of_session, study_session_identification, outlier_detection_switch):
    general_time_off_task = {"width": "20%", "visibility": "hidden"}
    general_time_off_task_suggestion = ""
    if "stt" in study_session_identification:
        general_time_off_task["visibility"] = "visible"
        if outlier_detection_switch:
            preprocessed_analysis = functions_algorithm.get_classified_pause_length_list(final_pause_analysis,
                                                                                         type_of_session,
                                                                                         None)
            time_off_task_suggestion = functions_algorithm.get_recommended_threshold(preprocessed_analysis,
                                                                                     constants.stt_suggestion_final_pause_types[type_of_session])
            if time_off_task_suggestion is None or np.isnan(time_off_task_suggestion):
                general_time_off_task_suggestion = ui_text.no_suggestion_session_timeout_threshold
            else:
                general_time_off_task_suggestion = ui_text.suggestion_session_timeout_threshold.format(time_off_task_suggestion)
    return general_time_off_task, general_time_off_task_suggestion


# --- FUNCTION DESCRIPTION ---
def get_component_time_off_task_suggestion(final_pause_analysis,
                                           type_of_session,
                                           outlier_detection_switch,
                                           component_toggle):
    component_time_off_task_suggestion = ""
    if outlier_detection_switch and component_toggle is not None:
        preprocessed_analysis = functions_algorithm.get_classified_pause_length_list(final_pause_analysis,
                                                                                     type_of_session,
                                                                                     component_toggle)
        if len(preprocessed_analysis[0]) != 0 or len(preprocessed_analysis[1]) != 0:
            time_off_task_suggestion = functions_algorithm.get_recommended_threshold(preprocessed_analysis,
                                                                                     constants.stt_suggestion_final_pause_types[type_of_session])
            if time_off_task_suggestion is not None and not np.isnan(time_off_task_suggestion):
                component_time_off_task_suggestion = ui_text.suggestion_session_timeout_threshold.format(time_off_task_suggestion)
            else:
                component_time_off_task_suggestion = ui_text.no_suggestion_session_timeout_threshold
        else:
            component_time_off_task_suggestion = ui_text.no_suggestion_session_timeout_threshold
    return component_time_off_task_suggestion


# --- FUNCTION DESCRIPTION ---
def get_component_time_off_task_update(study_session_identification,
                                       moodle_course,
                                       site_area_components,
                                       course_components,
                                       type_of_session):
    component_time_off_task = {"width": "70%",
                               "display": "inline-flex",
                               "border-left": "2px solid #9fa1a8",
                               "padding-left": "5pt",
                               "visibility": "hidden"}
    component_options = []
    if "stt" in study_session_identification and len(moodle_course) != 0:
        component_time_off_task["visibility"] = "visible"
        if type_of_session == "session_study":
            options = set()
            for course in moodle_course:
                for module in course_components[course]:
                    options.add(module)
            for module in site_area_components:
                options.add(module)
            component_options = sorted(list(options))
        elif type_of_session == "session_course":
            options = set()
            for course in moodle_course:
                for module in course_components[course]:
                    options.add(module)
            component_options = sorted(list(options))
        elif type_of_session == "session_learning":
            component_options = sorted(list(constants.learning_components))
    return component_time_off_task, component_options
