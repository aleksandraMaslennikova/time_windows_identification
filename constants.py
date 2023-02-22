from datetime import date

# --- VARIABLES THAT ALLOW TO CUSTOMISE THE VISUAL TOOL, SESSION IDENTIFICATION, ETC. ---
# the datasets location
data_dir_path = "data/"
file_names = {"activity_granularity": "data_activity_granularity.csv",
              "task_granularity": "data_task_granularity.csv"}

# courses available as a filter option
specific_moodle_course_filter = [{"label": "Course A", "value": "Course_A"},
                                 {"label": "Course B", "value": "Course_B"},
                                 {"label": "Course C", "value": "Course_C"}]

# limits of time interval in the calendar
min_date_allowed = date(2021, 1, 1)
max_date_allowed = date(2021, 8, 1)

# areas at the site level (related to logs performed not at the course level)
site_area = ["Overall Site"]
# modules considered as the quality learning ones
learning_components = ["Assignment", "File", "Lesson", "URL"]

# the interval of the considered STT values
min_stt_allowed = 0
max_stt_allowed = 60

# --- VARIABLES REQUIRED FOR THE STT SUGGESTION ALGORITHM ---
stt_suggestion_considered_pause_types = {"session_study": ["Different course/area after inactivity",
                                                           "Same course after inactivity"],
                                         "session_course": ["Change of course", "Site area after inactivity",
                                                            "Same course after inactivity"],
                                         "session_learning": ["Quality learning stopped",
                                                              "Course home after inactivity",
                                                              "Quality learning after inactivity"]}
stt_suggestion_map = {"session_study": {"Different course/area after inactivity": "Different course/area after inactivity",
                                        "Same course after inactivity": "Same course after inactivity"},
                      "session_course": {"Change of course": "Change of course + Site area after inactivity",
                                         "Site area after inactivity": "Change of course + Site area after inactivity",
                                         "Same course after inactivity": "Same course after inactivity"},
                      "session_learning": {"Quality learning stopped": "Quality learning stopped",
                                           "Course home after inactivity": "Inactivity",
                                           "Quality learning after inactivity": "Inactivity"}}
stt_suggestion_final_pause_types = {"session_study": ["Different course/area after inactivity",
                                                      "Same course after inactivity"],
                                    "session_course": ["Change of course + Site area after inactivity",
                                                       "Same course after inactivity"],
                                    "session_learning": ["Quality learning stopped", "Inactivity"]}
stt_suggestion_real_pause = ["Different course/area after inactivity",
                             "Change of course + Site area after inactivity",
                             "Quality learning stopped"]