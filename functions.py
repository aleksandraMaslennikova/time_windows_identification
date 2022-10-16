import pandas as pd
from datetime import datetime, timedelta
from tzlocal import get_localzone
import pytz
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import ui_text as constant

def preload_data(dir_path):
  dict_of_df = {}
  # fix the outhlier detection method, because rn we only use this one
  outlier_detection_method = "outliers_global"
  #for outlier_detection_method in constant.outlier_detection_methods_values:
  dict_of_df[outlier_detection_method] = {}
  for grouping in constant.components_grouped:
    dict_of_df[outlier_detection_method][grouping] = {}
    dict_of_df[outlier_detection_method][grouping] = pd.read_csv(dir_path + outlier_detection_method + "_" + grouping + "_All.csv")
  return dict_of_df

def get_chosen_df(dict_of_df, observation_start_date, observation_end_date, outlier_detection_method, group_logs_status):
  chosen_df = dict_of_df[outlier_detection_method][group_logs_status]
  start_date = int(datetime.timestamp(datetime.fromisoformat(observation_start_date)))
  end_date = int(datetime.timestamp(datetime.fromisoformat(observation_end_date) + timedelta(days=1)))
  chosen_df = chosen_df.loc[(chosen_df["Unix_Time"] >= start_date) & (chosen_df["Unix_Time"] < end_date)]
  return chosen_df

def transform_active_components_options_to_dict(options_list):
  if options_list is None:
    return {}
  res = {}
  for option in options_list:
    temp = option.split(" (")
    res[temp[0]] = float(temp[1].split(" min)")[0])
  return res

def transform_active_components_dict_to_options(options_dict):
  res = []
  for option in options_dict.keys():
    res.append(option + " (" + str(options_dict[option]) + " min)")
  return res

def get_study_session_logs(chosen_df, is_study_session, is_course_session, is_learning_session, study_session_identification, outlier_detection_switch, time_off_task_threshold, active_component_threshold_dict):
  # --- INTERPRETATION OF STUDY SESSION SETTINGS ---
  authentication_flag = "authentication" in study_session_identification
  time_off_task_flag = "stt" in study_session_identification

  # --- GETTING STUDY SESSIONS ---
  user_list = chosen_df["Student ID"].unique()
  sessions = []
  reason_to_end = []
  for user in user_list:
    chosen_df_user_dict = chosen_df[chosen_df["Student ID"] == user].to_dict("records")
    session_logs = []
    for i in range(len(chosen_df_user_dict)):
      previous_row = chosen_df_user_dict[i-1] or None
      current_row = chosen_df_user_dict[i]
      pause = (current_row["duration"] - current_row["Event_duration"]) if outlier_detection_switch else current_row["duration"] - time_off_task_threshold
      session_logs.append(current_row)
      # stop the previous study session because of the new log in
      if authentication_flag and current_row["Component"] == "Login" and len(session_logs) != 1 and previous_row["Component"] != "Login":
        sessions.append(session_logs[:-1])
        reason_to_end.append(("Authentication", current_row["Component"], chosen_df_user_dict[i-1]["duration"] - chosen_df_user_dict[i-1]["Event_duration"]))
        session_logs = [current_row]
      elif authentication_flag and current_row["Component"] == "Logout":
        sessions.append(session_logs)
        reason_to_end.append(("Authentication", current_row["Component"], pause))
        session_logs = []
      stopped_by_change_of_area = False
      if (is_course_session or is_learning_session) and len(session_logs) != 0 and i+1 != len(chosen_df_user_dict) and current_row["Area"] != chosen_df_user_dict[i+1]["Area"]:
        if current_row["Area"] not in constant.site_area and chosen_df_user_dict[i+1]["Area"] in constant.site_area and i+2 != len(chosen_df_user_dict):
          if chosen_df_user_dict[i+2]["Area"] != current_row["Area"]:
            stopped_by_change_of_area = True
        else:
          stopped_by_change_of_area = True
      if stopped_by_change_of_area:
        sessions.append(session_logs)
        if is_course_session:
          reason_to_end.append(("Change of course", current_row["Component"], pause))
        if is_learning_session:
          reason_to_end.append(("Quality learning stopped", current_row["Component"], pause))
        session_logs = []
      if is_learning_session and len(session_logs) != 0 and current_row["Component"] in constant.learning_components and \
         i+1 != len(chosen_df_user_dict) and chosen_df_user_dict[i+1]["Component"] not in constant.learning_components:
        if chosen_df_user_dict[i+1]["Component"] == "Course_home" and i+2 != len(chosen_df_user_dict):
          if chosen_df_user_dict[i+2]["Component"] not in constant.learning_components:
            sessions.append(session_logs)
            reason_to_end.append(("Quality learning stopped", current_row["Component"], pause))
            session_logs = []
        else:
          sessions.append(session_logs)
          reason_to_end.append(("Quality learning stopped", current_row["Component"], pause))
          session_logs = []
      if time_off_task_flag and len(session_logs) != 0:
        difference = current_row["duration"] - current_row["Event_duration"] if outlier_detection_switch else current_row["duration"]
        if (current_row["Component"] in active_component_threshold_dict.keys() and difference > active_component_threshold_dict[current_row["Component"]]) or \
           (current_row["Component"] not in active_component_threshold_dict.keys() and difference > time_off_task_threshold*60.0):
          sessions.append(session_logs)
          if i+1 < len(chosen_df_user_dict):
            next_row = chosen_df_user_dict[i+1]
            if is_study_session:
              if current_row["Area"] != next_row["Area"]:
                reason_to_end.append(("Different course/area after inactivity", current_row["Component"], pause))
              else:
                if current_row["Area"] not in constant.site_area:
                  reason_to_end.append(("Same course after inactivity", current_row["Component"], pause))
                else:
                  reason_to_end.append(("Same area after inactivity", current_row["Component"], pause))
            if is_course_session:
              if current_row["Area"] != next_row["Area"] and i+2 < len(chosen_df_user_dict) and current_row["Area"] == chosen_df_user_dict[i+2]["Area"]:
                reason_to_end.append(("Site area after inactivity", current_row["Component"], pause))
              else:
                reason_to_end.append(("Same course after inactivity", current_row["Component"], pause))
            if is_learning_session:
              if next_row["Component"] == "Course_home":
                reason_to_end.append(("Course home after inactivity", current_row["Component"], pause))
              else:
                reason_to_end.append(("Quality learning after inactivity", current_row["Component"], pause))
          else:
            reason_to_end.append(("Final log", current_row["Component"], pause))
          session_logs = []
    if len(session_logs) != 0:
      sessions.append(session_logs)
      reason_to_end.append(("Final log", chosen_df_user_dict[-1]["Component"], pause))
  return sessions, reason_to_end

def get_study_session_time_periods(chosen_df, moodle_course, type_of_session, study_session_identification, del_attendance_session_flag, outlier_detection_switch, time_off_task_threshold, active_component_threshold_dict):
  # --- INTERPRETATION OF STUDY SESSION SETTINGS ---
  is_course_session = type_of_session == "session_course"
  is_learning_session = type_of_session == "session_learning"
  is_study_session = is_course_session == False and is_learning_session == False
  is_general_research = len(moodle_course) == 0
  time_off_task_threshold = 0 if time_off_task_threshold is None else time_off_task_threshold

  session_logs, reason_to_end = get_study_session_logs(chosen_df, is_study_session, is_course_session, is_learning_session, study_session_identification, outlier_detection_switch, time_off_task_threshold, active_component_threshold_dict)

  num = 0
  study_session_time_periods = []
  final_pause_analysis = []
  for j in range(len(session_logs)):
    session = session_logs[j]
    # retrieve information about this current session
    has_needed_course = False
    if not is_general_research:
      for log in session:
        if log["Area"] in moodle_course:
          has_needed_course = True
    has_course_area = False
    if is_course_session:
      for log in session:
        if log["Area"] not in constant.site_area:
          has_course_area = True
    has_learning_component = False
    if is_learning_session:
      for log in session:
        if log["Component"] in constant.learning_components:
          has_learning_component = True
    is_attendance_session = session[-1]["Component"]=="Attendance" and len(session) <= 5

    # process if need to add to the list, and choose start and end of the session
    if ((not is_general_research and has_needed_course) or is_general_research) and \
       ((is_course_session and has_course_area) or not is_course_session) and \
       ((is_learning_session and has_learning_component) or not is_learning_session) and \
       ((del_attendance_session_flag and not is_attendance_session) or not del_attendance_session_flag):
      not_add = False
      num += 1
      # select start point 
      i = 0
      if is_course_session:
        while (is_general_research and session[i]["Area"] in constant.site_area) or (not is_general_research and session[i]["Area"] not in moodle_course):
          i += 1
      if is_learning_session:
        while (is_general_research and session[i]["Component"] not in constant.learning_components) or (not is_general_research and not (session[i]["Area"] in moodle_course and session[i]["Component"] in constant.learning_components)):
          i += 1
          if i == len(session):
            i = 0
            not_add = True
            break;
      if not not_add:
        session_start = session[i]["Unix_Time"]
        # select end point
        i = len(session) - 1
        if is_course_session:
          i = len(session) - 1
          while (is_general_research and session[i]["Area"] in constant.site_area) or (not is_general_research and session[i]["Area"] not in moodle_course):
            i -= 1
        if is_learning_session:
          i = len(session) - 1
          while (is_general_research and session[i]["Component"] not in constant.learning_components) or (not is_general_research and not (session[i]["Area"] in moodle_course and session[i]["Component"] in constant.learning_components)):
            i -= 1
        session_end = session[i]["Unix_Time"] + session[i]["Event_duration"] if outlier_detection_switch else session[i]["Unix_Time"] + time_off_task_threshold
        if session[-1]["Component"] == "Logout":
          session_end = session[-1]["Unix_Time"]
        study_session_time_periods.append((session_start, int(session_end)))
        final_pause_analysis.append(reason_to_end[j])
  return study_session_time_periods, final_pause_analysis

def get_classified_pause_length_list(pause_analysis, type_of_session, component_toggle):
  result_dict = {}
  for pause_type in constant.stt_suggestion_final_pause_types[type_of_session]:
    result_dict[pause_type] = []
  for pause in pause_analysis:
    if pause[0] in constant.stt_suggestion_considered_pause_types[type_of_session] and pause[2] != 0 and (component_toggle is None or pause[1] == component_toggle):
      result_dict[constant.stt_suggestion_map[type_of_session][pause[0]]].append(pause[2]/60.0)
  result_list = []
  for pause_type in constant.stt_suggestion_final_pause_types[type_of_session]:
    result_dict[pause_type] = np.array(result_dict[pause_type])
    result_dict[pause_type] = result_dict[pause_type].astype(np.float)
    result_list.append(result_dict[pause_type])
  return np.array(result_list, dtype=object) 

def get_recommended_threshold(data, labels):
  start_point = constant.min_stt_allowed
  end_point = constant.max_stt_allowed
  bins = list(range(start_point, end_point, 1))
  bins.append(end_point)
  n, bins, patches = plt.hist(data, bins, histtype='bar', stacked=False, fill=True, density=True)
  plt.close()
  index_real_pause = 0 if labels[0] in constant.stt_suggestion_real_pause else 1
  index_continue = 1 - index_real_pause
  difference_list = []
  difference_x = []
  for i in range(len(n[0])):
    density_real_pause = n[index_real_pause][i]
    density_continue = n[index_continue][i]
    if density_real_pause != 0 and density_continue != 0:
      difference_x.append(i+1)
      density_sum = density_real_pause + density_continue
      probability_real_pause = density_real_pause / density_sum
      probability_continue = density_continue / density_sum
      difference_list.append(probability_continue - probability_real_pause)
  try:
    res = np.polyfit(np.log(difference_x), difference_list, 1)
    a = res[0]
    b = res[1]
    change_place = np.exp(-b/a)
    return round(change_place, 2)
  except:
    return None

def get_general_time_off_task_update(final_pause_analysis, type_of_session, moodle_course, study_session_identification, outlier_detection_switch):
  general_time_off_task = {"width": "20%", "visibility": "hidden"}
  general_time_off_task_suggestion = ""
  if "stt" in study_session_identification:
    general_time_off_task["visibility"] = "visible"
    if outlier_detection_switch:
      preprocessed_analysis = get_classified_pause_length_list(final_pause_analysis, type_of_session, None)
      time_off_task_suggestion = get_recommended_threshold(preprocessed_analysis, constant.stt_suggestion_final_pause_types[type_of_session])
      if time_off_task_suggestion is None or np.isnan(time_off_task_suggestion):
        general_time_off_task_suggestion = constant.no_suggestion_threshold
      else:
        general_time_off_task_suggestion = constant.suggestion_threshold.format(time_off_task_suggestion)
  return general_time_off_task, general_time_off_task_suggestion

def get_component_time_off_task_update(study_session_identification, moodle_course, type_of_session):
  component_time_off_task = {"width": "70%", "display": "inline-flex", "border-left": "2px solid #9fa1a8", "padding-left": "5pt", "visibility": "hidden"}
  component_options = []
  if "stt" in study_session_identification and len(moodle_course) != 0:
      component_time_off_task["visibility"] = "visible"
      if type_of_session == "session_study":
        options = set()
        for course in moodle_course:
          for module in constant.course_components[course]:
            options.add(module)
        for module in constant.site_area_components:
          options.add(module)
        component_options = sorted(list(options))
      elif type_of_session == "session_course":
        options = set()
        for course in moodle_course:
          for module in constant.course_components[course]:
            options.add(module)
        component_options = sorted(list(options))
      elif type_of_session == "session_learning":
        component_options = sorted(list(constant.learning_components))
  return component_time_off_task, component_options

def get_component_time_off_task_suggestion(final_pause_analysis, type_of_session, outlier_detection_switch, component_toggle):
  component_time_off_task_suggestion = ""
  if outlier_detection_switch and component_toggle is not None: 
    preprocessed_analysis = get_classified_pause_length_list(final_pause_analysis, type_of_session, component_toggle)
    if len(preprocessed_analysis[0]) != 0 or len(preprocessed_analysis[1]) != 0:
      time_off_task_suggestion = get_recommended_threshold(preprocessed_analysis, constant.stt_suggestion_final_pause_types[type_of_session])
      if time_off_task_suggestion is not None and not np.isnan(time_off_task_suggestion):
        component_time_off_task_suggestion = constant.suggestion_threshold.format(time_off_task_suggestion)
      else:
        component_time_off_task_suggestion = constant.no_suggestion_threshold
    else:
      component_time_off_task_suggestion = constant.no_suggestion_threshold
  return component_time_off_task_suggestion

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
    end_time = end_session.hour + end_session.minute/60.0
    if start_session.day != end_session.day:
      end_time += 24
    start_session = start_session.hour
    starts.append(start_session)
    ends.append(end_time)
  return pd.DataFrame({"Time of session start": starts, "Unix session start": starts_unix, "Time of session end": ends, "Unix session end": ends_unix})

def get_session_duration_info(data, session_start_labels):
  # duration in minutes instead of seconds
  data["Session duration"] = (data["Unix session end"] - data["Unix session start"])/60.0
  # get statistical session's duration information
  hover_data= data.groupby("Time of session start", as_index=False).agg(
    base=("Time of session end", "min"),
    bar=("Time of session end", lambda s: s.max() - s.min()),
    session_start_label=("Time of session start", lambda s: session_start_labels[s.min()]),
    count=("Time of session end", lambda s: "{:,}".format(len(s)).replace(",", " ")),
    session_min=("Session duration", lambda s: round(s.min(), 2)),
    session_lower_fence=("Session duration", lambda s: round(s[s <= (np.percentile(s, 25) - 1.5 * (np.percentile(s, 75) - np.percentile(s, 25)))].min(), 2)),
    session_q1=("Session duration", lambda s: round(np.percentile(s, 25), 2)),
    session_median=("Session duration", lambda s: round(np.median(s), 2)),
    session_q3=("Session duration", lambda s: round(np.percentile(s, 75), 2)),
    session_upper_fence=("Session duration", lambda s: round(s[s <= (np.percentile(s, 75) + 1.5 * (np.percentile(s, 75) - np.percentile(s, 25)))].max(), 2)),
    session_max=("Session duration", lambda s: round(s.max(), 2))
    )
  # data in the format necessary for the plot
  customdata = np.stack((
    hover_data["session_start_label"],
    hover_data["count"],
    hover_data["session_min"],
    hover_data["session_q1"], 
    hover_data["session_median"], 
    hover_data["session_q3"],
    hover_data["session_max"]
    ), axis=-1)
  return hover_data, customdata 

def plot_boxplot(data):
  # plot boxplot data
  fig = px.box(data, x="Time of session start", y="Time of session end", height=550)

  #set plot's title
  title_text = constant.plot_title
  fig.update_layout(title={"text": title_text, "y":0.95, "x":0.5, "xanchor": "center", "yanchor": "top"})
  
  # set x and y axis labels
  session_start_labels = {}
  for i in range(10):
    session_start_labels[i] = "0" + str(i) + ":00-0" + str(i) +":59"
  for i in range(10, 24):
    session_start_labels[i] = str(i) + ":00-" + str(i) +":59"
  fig.update_layout(xaxis_tickvals = list(np.arange(24)))
  fig.update_layout(xaxis_ticktext = list(session_start_labels.values()))
  fig.update_layout(yaxis_range = [0, 30])
  fig.update_layout(yaxis_tickvals = list(np.arange(30)))
  fig.update_layout(yaxis_ticktext = list(np.arange(24)) + ["24+00", "24+01", "24+02", "24+03", "24+04", "24+05"])

  # add session's duration information
  hover_data, customdata  = get_session_duration_info(data, session_start_labels)
  fig2 = go.Figure(go.Bar(
    x = hover_data["Time of session start"],
    y = hover_data["bar"],
    base = hover_data["base"],
    customdata = customdata,
    hovertemplate = constant.hovertemplate,
    width = 0.5,
    opacity = 0,
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