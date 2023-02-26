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
    def most_frequent(lst):
        max_val = max(set(lst), key=lst.count)
        return max_val, lst.count(max_val)

    starts = []
    starts_unix = []
    ends = []
    ends_unix = []
    most_freq_activity_task = []
    most_freq_activity_task_count = []
    most_freq_type = []
    possible_start_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    granularity = "activity_granularity" if "Event_Name" in learning_sessions[0][0].keys() else "task_granularity"
    dict_activity_task_by_start = {}
    for start_value in possible_start_values:
        dict_activity_task_by_start[start_value] = []
    for session in learning_sessions:
        start_unix = session[0]["Unix_Time"]
        end_unix = session[-1]["Unix_Time"]
        starts_unix.append(int(start_unix))
        start_session = datetime.fromtimestamp(start_unix, tz=pytz.timezone("Europe/Rome"))
        ends_unix.append(int(end_unix))
        end_session = datetime.fromtimestamp(end_unix, tz=pytz.timezone("Europe/Rome"))
        end_time = end_session.hour + end_session.minute / 60.0
        if start_session.day != end_session.day:
            end_time += 24
        start_session = start_session.hour
        starts.append(start_session)
        ends.append(end_time)
        for log in session:
            info = log["Component"] if granularity == "task_granularity" else (log["Component"], log["Event_Name"])
            dict_activity_task_by_start[start_session].append(info)
    for start_value in possible_start_values:
        dict_activity_task_by_start[start_value] = (most_frequent(dict_activity_task_by_start[start_value]))
    for start in starts:
        most_freq_activity_task.append(dict_activity_task_by_start[start][0])
        most_freq_activity_task_count.append(dict_activity_task_by_start[start][1])
        most_freq_type.append(granularity[:-12])
    return pd.DataFrame({"Time of session start": starts,
                         "Unix session start": starts_unix,
                         "Time of session end": ends,
                         "Unix session end": ends_unix,
                         "Most freq": most_freq_activity_task,
                         "Most freq - Count": most_freq_activity_task_count})


# --- FUNCTION DESCRIPTION ---
def get_session_hover_info(data,
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
        session_max=("Session duration", lambda s: round(s.max(), 2)),
        granularity=("Granularity", lambda s: s.iloc[0].lower()),
        most_freq=("Most freq", lambda s: s.iloc[0]),
        most_freq_count=("Most freq - Count", lambda s: s.iloc[0])
    )

    # data in the format necessary for the plot
    custom_data = np.stack((
        hover_data["session_start_label"],
        hover_data["count"],
        hover_data["session_min"],
        hover_data["session_q1"],
        hover_data["session_median"],
        hover_data["session_q3"],
        hover_data["session_max"],
        hover_data["granularity"],
        hover_data["most_freq"],
        hover_data["most_freq_count"]
    ), axis=-1)
    return hover_data, custom_data


# --- FUNCTION DESCRIPTION ---
def plot_boxplot(data, activity_task_visibility):
    def plot_hovering_info(granularity, x_movement, width):
        portion = data[data["Granularity"] == granularity].copy()
        hover_data, custom_data = get_session_hover_info(portion, session_start_labels)
        fig2 = go.Figure(go.Bar(
            x=hover_data["Time of session start"] + x_movement,
            y=hover_data["bar"],
            base=hover_data["base"],
            customdata=custom_data,
            hovertemplate=ui_text.hovertemplate,
            width=width,
            opacity=0,
            hoverlabel=dict(bgcolor="#aecdc2"),
            showlegend=False
        ))
        fig.add_traces(fig2.data)
        del portion

    # plot boxplot data
    fig = px.box(data, x="Time of session start", y="Time of session end", color="Granularity", height=550)
    fig.update_traces(visible=activity_task_visibility["Task"],
                      selector=dict(name="Task"))
    fig.update_traces(visible=activity_task_visibility["Activity"],
                      selector=dict(name="Activity"))

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
    granularity_to_add_hover_info = []
    for granularity in activity_task_visibility.keys():
        if activity_task_visibility[granularity] is True:
            granularity_to_add_hover_info.append(granularity)
    if len(granularity_to_add_hover_info) == 1:
        plot_hovering_info(granularity_to_add_hover_info[0], 0, 0.5)
    elif len(granularity_to_add_hover_info) == 2:
        plot_hovering_info("Activity", -0.175, 0.25)
        plot_hovering_info("Task", 0.175, 0.25)

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


def get_suggestion_ui_text(time_off_task_suggestion_dict):
    activity_task_toggle = list(time_off_task_suggestion_dict.keys())
    activity_granularity_is_none = "activity_granularity" in activity_task_toggle \
                                   and (time_off_task_suggestion_dict["activity_granularity"] is None
                                        or np.isnan(time_off_task_suggestion_dict["activity_granularity"]))
    task_granularity_is_none = "task_granularity" in activity_task_toggle \
                               and (time_off_task_suggestion_dict["task_granularity"] is None
                                    or np.isnan(time_off_task_suggestion_dict["task_granularity"]))
    if activity_granularity_is_none or task_granularity_is_none:
        suggestion = ui_text.no_suggestion_session_timeout_threshold
    elif len(activity_task_toggle) == 1:
        stt_suggestion = time_off_task_suggestion_dict[activity_task_toggle[0]]
        suggestion = ui_text.suggestion_session_timeout_threshold.format(stt_suggestion)
    elif len(activity_task_toggle) == 2:
        activity_stt_suggestion = time_off_task_suggestion_dict["activity_granularity"]
        task_stt_suggestion = time_off_task_suggestion_dict["task_granularity"]
        suggestion = ui_text.suggestion_session_timeout_threshold_activity_task.format(
            activity_stt_suggestion,
            task_stt_suggestion
        )
    return suggestion


# --- FUNCTION DESCRIPTION ---
def get_general_time_off_task_update(final_pause_analysis_dict,
                                     type_of_session,
                                     study_session_identification,
                                     outlier_detection_switch,
                                     activity_task_toggle,
                                     max_stt):
    general_time_off_task = {"width": "20%", "visibility": "hidden"}
    max_time_off_task = {"width": "15%", "visibility": "hidden"}
    general_time_off_task_suggestion = ""
    if "stt" in study_session_identification and len(activity_task_toggle) != 0:
        max_time_off_task["visibility"] = "visible"
        if max_stt is not None:
            general_time_off_task["visibility"] = "visible"
            if outlier_detection_switch:
                time_off_task_suggestion_dict = {}
                for granularity in activity_task_toggle:
                    final_pause_analysis = final_pause_analysis_dict[granularity]
                    preprocessed_analysis = functions_algorithm.get_classified_pause_length_list(final_pause_analysis,
                                                                                                 type_of_session,
                                                                                                 None)
                    time_off_task_suggestion_dict[granularity] = functions_algorithm.get_recommended_threshold(
                        preprocessed_analysis,
                        constants.stt_suggestion_final_pause_types[type_of_session],
                        max_stt
                    )
                general_time_off_task_suggestion = get_suggestion_ui_text(time_off_task_suggestion_dict)
    return max_time_off_task, general_time_off_task, general_time_off_task_suggestion


# --- FUNCTION DESCRIPTION ---
def get_component_time_off_task_suggestion(final_pause_analysis_dict,
                                           type_of_session,
                                           outlier_detection_switch,
                                           component_toggle,
                                           activity_task_toggle,
                                           max_stt):
    component_time_off_task_suggestion = ""
    if outlier_detection_switch and component_toggle is not None and len(activity_task_toggle) != 0:
        preprocessed_analysis_dict = {}
        for granularity in activity_task_toggle:
            final_pause_analysis = final_pause_analysis_dict[granularity]
            preprocessed_analysis_dict[granularity] = functions_algorithm.get_classified_pause_length_list(
                final_pause_analysis,
                type_of_session,
                component_toggle)
        activity_granularity_check = "activity_granularity" in activity_task_toggle \
                                     and (len(preprocessed_analysis_dict["activity_granularity"][0]) != 0
                                          or len(preprocessed_analysis_dict["activity_granularity"][1]) != 0)
        task_granularity_check = "task_granularity" in activity_task_toggle \
                                 and (len(preprocessed_analysis_dict["task_granularity"][0]) != 0
                                      or len(preprocessed_analysis_dict["task_granularity"][1]) != 0)
        if activity_granularity_check or task_granularity_check:
            time_off_task_suggestion_dict = {}
            for granularity in activity_task_toggle:
                time_off_task_suggestion_dict[granularity] = functions_algorithm.get_recommended_threshold(
                    preprocessed_analysis_dict[granularity],
                    constants.stt_suggestion_final_pause_types[type_of_session],
                    max_stt
                )
            component_time_off_task_suggestion = get_suggestion_ui_text(time_off_task_suggestion_dict)
    return component_time_off_task_suggestion


# --- FUNCTION DESCRIPTION ---
def get_component_time_off_task_update(study_session_identification,
                                       moodle_course,
                                       site_area_components,
                                       course_components,
                                       type_of_session,
                                       activity_task_toggle,
                                       max_stt):
    component_time_off_task = {"width": "70%",
                               "display": "inline-flex",
                               "border-left": "2px solid #9fa1a8",
                               "padding-left": "5pt",
                               "visibility": "hidden"}
    component_options = []
    if "stt" in study_session_identification \
            and len(moodle_course) != 0\
            and len(activity_task_toggle) != 0\
            and max_stt is not None:
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
