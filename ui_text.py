from datetime import date

# UI: text and label-value information
activity_or_task_text = "Select activity or task"
activity_or_task = [{"label": "Activity", "value": "activity"},
                    {"label": "Task", "value": "task"}]
temporal_text = "Select the temporal metric"
temporal = [{"label": "Elapsed time", "value": "elapsed-time"},
            {"label": "Time-off-task", "value": "time-off-task"}]


moodle_course_text = "Select no, one, or more courses"
moodle_course_placeholder = "All dataset logs"
moodle_courses = [{"label": "Course A", "value": "ALL_DA"},
				  {"label": "Course B", "value": "ALL_DB"},
				  {"label": "Course C", "value": "DM&ML"}]

select_period_text = "Select the time interval"

type_of_session_text = "Type of session"
types_of_session = [{"label": "Study session", "value": "session_study"},
					{"label": "Course session", "value": "session_course"},
                    {"label": "Learning session", "value": "session_learning"}]

outlier_detection_text = {True: "Outlier detection: On",
						  False: "Outlier detection: Off"}
outlier_detection_methods = [{"label": "Global based", "value": "outliers_global"}, 
							 {"label": "User based", "value": "outliers_user"}]


study_session_identification_text = "Select the session identification method"
study_session_identification_options = [{"label": "Authentication logs", "value": "authentication"},
                                        {"label": "Session Timeout Threshold (STT)", "value": "stt"}]

check_list_options = [{"label": "Exclude only-attendance sessions", "value": "del_only_attendance"}]

general_threshold_text = "Set the (desired) STT"
general_threshold_placeholder = "STT (minutes)"

select_component = "Select the module of interest"
component_threshold_text = "Module's STT"
component_threshold_placeholder = "STT (minutes)"
button_text = "Add STT"
active_component_thresholds_text = "No active module specific thresholds"

suggestion_threshold = "Recommended threshold: {} minutes"
no_suggestion_threshold = "There is not enough examples of this behaviour to make an STT recommendation"

plot_title = "Spread of session durations"
hovertemplate= ("<b>Session start period %{customdata[0]}</b><br>"+
                "Session count: %{customdata[1]}<br>" +
                "Session min: %{customdata[2]} min<br>" +
                "Session q1: %{customdata[3]} min<br>" +
                "Session median: %{customdata[4]} min<br>" +
                "Session q3: %{customdata[5]} min<br>" +
                "Session max: %{customdata[6]} min<extra></extra>")

# necessary constants
outlier_detection_methods_values = ["outliers_global", "outliers_user"]
moodle_courses_values = ["ALL_DA", "ALL_DB", "DM&ML"]
components_grouped = ["grouped", "not_grouped"]
site_area = ["Authentication", "Overall Site", "Profile", "Social Interaction"]
site_area_components = ['Badge', 'Blog', 'Courses list', 'Dashboard', 'Forum', 'Grades', 'Login', 'Logout', 'Messaging', 'Notification', 'Participant_profile', 'Site home', 'Tag', 'User_profile']
learning_components = ["Assignment", "File", "Glossary", "H5P", "Lesson", "Quiz", "URL"]
course_components = {"ALL_DA": ["Assignment", "Attendance", "Badge", "Book", "Chat", "Choice", "Course_home", "Database", "Feedback",
                                "File", "Folder", "Forum", "Glossary", "Grades", "H5P", "Jitsi", "Lesson", "Page",
                                "Participant_profile", "Quiz", "Reservation", "Survey", "URL", "User_profile", "Wiki"],
                     "ALL_DB": ["Assignment", "Attendance", "Badge", "Book", "Chat", "Choice", "Course_home", "Database", "Feedback",
                                "File", "Forum", "Glossary", "Grades", "H5P", "Jitsi", "Lesson", "Page", "Participant_profile",
                                "Quiz", "Reservation", "Survey", "URL", "User_profile", "Wiki"],
                     "DM&ML": ["Assignment", "Attendance", "Badge", "Book", "Choice", "Course_home", "Database", "Feedback", "File",
                               "Folder", "Forum", "Glossary", "Grades", "H5P", "Jitsi", "Lesson", "Page", "Participant_profile",
                               "Quiz", "Reservation", "Tag", "URL", "User_profile", "Wiki"]}
min_date_allowed = date(2021, 1, 1)
max_date_allowed = date(2021, 8, 1)
min_stt_allowed = 0
max_stt_allowed = 60
stt_suggestion_considered_pause_types = {"session_study": ["Different course/area after inactivity", "Same course after inactivity"],
                                         "session_course": ["Change of course", "Site area after inactivity", "Same course after inactivity"],
                                         "session_learning": ["Quality learning stopped", "Course home after inactivity", "Quality learning after inactivity"]}
stt_suggestion_map = {"session_study": {"Different course/area after inactivity": "Different course/area after inactivity",
                                        "Same course after inactivity": "Same course after inactivity"},
                      "session_course": {"Change of course": "Change of course + Site area after inactivity",
                                         "Site area after inactivity": "Change of course + Site area after inactivity",
                                         "Same course after inactivity": "Same course after inactivity"},
                      "session_learning": {"Quality learning stopped": "Quality learning stopped",
                                           "Course home after inactivity": "Inactivity",
                                           "Quality learning after inactivity": "Inactivity"}}
stt_suggestion_final_pause_types = {"session_study": ["Different course/area after inactivity", "Same course after inactivity"],
                                    "session_course": ["Change of course + Site area after inactivity", "Same course after inactivity"],
                                    "session_learning": ["Quality learning stopped", "Inactivity"]}
stt_suggestion_real_pause = ["Different course/area after inactivity", "Change of course + Site area after inactivity", "Quality learning stopped"]
