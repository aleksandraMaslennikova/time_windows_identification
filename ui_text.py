# --- UI VARIABLES: TEXT AND LABEL-VALUE INFORMATION ---
# in case of the dictionary variables, for the translation or change of the ui-text,
# ONLY change the "label" value ("value" is used inside the code; if changed, the algorithm will not work correctly)

select_specific_moodle_course_filter_label = "Select no, one, or more courses"
select_specific_moodle_course_filter_placeholder = "All dataset logs"

select_specific_period_label = "Select the time interval"

activity_or_task_label = "Select activity or task"
activity_or_task_options = [{"label": "Activity", "value": "activity_granularity"},
                            {"label": "Task", "value": "task_granularity"}]

temporal_metric_label = "Select the temporal metric"
temporal_metric_options = [{"label": "Elapsed time", "value": "elapsed-time"},
                           {"label": "Time-off-task", "value": "time-off-task"}]

type_of_session_label = "Type of session"
type_of_session_options = [{"label": "Study session", "value": "session_study"},
					       {"label": "Course session", "value": "session_course"},
                           {"label": "Learning session", "value": "session_learning"}]

study_session_identification_label = "Select the session identification method"
study_session_identification_options = [{"label": "Authentication logs", "value": "authentication"},
                                        {"label": "Session Timeout Threshold (STT)", "value": "stt"}]

check_list_options = [{"label": "Exclude only-attendance sessions", "value": "del_only_attendance"}]

max_session_timeout_threshold_label = "Max considered STT"
max_session_timeout_threshold_placeholder = "STT (minutes)"

general_session_timeout_threshold_label = "Set the (desired) STT"
general_session_timeout_threshold_placeholder = "STT (minutes)"

select_component_label = "Select the module of interest"
component_session_timeout_threshold_label = "Module's STT"
component_session_timeout_threshold_placeholder = "STT (minutes)"
component_session_timeout_threshold_button_text = "Add STT"
component_active_session_timeout_thresholds_placeholder = "No active module specific thresholds"

suggestion_session_timeout_threshold = "Recommended threshold: {} minutes"
suggestion_session_timeout_threshold_activity_task = "Recommended threshold: {} minutes for activity, {} minutes for task"
no_suggestion_session_timeout_threshold = "There is not enough examples of this behaviour to make an STT recommendation"

plot_title = "Spread of session durations"
hovertemplate = ("<b>Session start period %{customdata[0]}</b><br>" +
				"Most popular %{customdata[7]}: %{customdata[8]} (%{customdata[9]} times)<br>" +
                "Session count: %{customdata[1]}<br>" +
                "Session min: %{customdata[2]} min<br>" +
                "Session q1: %{customdata[3]} min<br>" +
                "Session median: %{customdata[4]} min<br>" +
                "Session q3: %{customdata[5]} min<br>" +
                "Session max: %{customdata[6]} min<extra></extra>")
