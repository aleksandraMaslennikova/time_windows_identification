
# Session-based Time-windows Identification in Virtual Learning Environment

This repository contains the code that divides the log data into sessions, calculates the suggestion for Session Timeout Threshold (STT), and provides a Visual Tool that assists in determining time-windows for future analysis.

For further details on all the definitions and the algorithm's functionality, consult [Visual Analytics for Session-based Time-Windows Identification in Virtual Learning Environments](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=10017679&casa_token=6AioK6bO2-oAAAAA:V3P14EYkl_lfoNEk3jmtMlvi-947j6TD1em0KS3Zr0ws83aYojucpYZR1QOx5sZuHCWQnUN5rQ&tag=1).																		
## Table of contents
* [Quick start. Data structure](#data-structure)
* [Quick start. Divide your log-data into sessions](#divide-your-log-data-into-sessions)
* [Quick start. Get Session Timeout Threshold suggestion](#get-session-timeout-threshold-suggestion)
* [Quick start. Run Visual Tool to determine time-windows](#run-visual-tool-to-determine-time-windows)
* [License](#license)
* [Acknowledgements](#acknowledgements)
* [Contacts](#contact--s-)

## Quick start

This section contains a description of the data structure expected by the algorithms as well as an instructions on the three main applications of this code.

### Data structure

The **data/** folder contains examples of expected csv-files. The Visual Tool requires two files to function properly: one with activity granularity and another one with task granularity.

To learn more about the data structure used in the algorithm, read [Time-on-Task Estimation by data-driven Outlier Detection based on Learning Activities](https://dl.acm.org/doi/pdf/10.1145/3506860.3506913?casa_token=MSB7wHOmFRUAAAAA:OXQm3n6X4H9-MUtdjC9OEnRBu9FLQA3M3ziWjvE1Q3Wtl8oV-TsQoKO0sJ1LY3ogwyJ2rufHdxLk). Below you will find a brief summary description.

The csv-files contain the following columns:
* _Student ID_ - the unique ID assigned to each student.
* _Course_Area_ - for course-level log, this value represents the Course in which a student performed the action, and for site-level log, it represents the category of the action performed in the Site Area.
* _Component_ - the module type (for example, File, Url, Quiz).
* _Event_Name_ (ONLY for activity granularity) - the type of action performed on the module (for example, deleted, updated, created, submitted).
* _Unix_Time_ - the unix timestamp that represents when the action was performed.
* _Estimated_Duration_ - the estimation of how much time a student has actually spent performing the action.
* _Duration_ - the value calculated by subtracting the timestamps of two consecutive actions.

**NB! Trasformation of the activity granularity file into the task granularity file**

If you only have the activity granularity logs at hand, this code will transform your activity granularity file into a file with task granularity.
You just need to indicate `file_path_activity_granularity`, i.e. path to the file where data with activity granularity is stored, and `file_path_task_granularity`, i.e. path to the file where data with task granularity will be stored.
```
df = pd.read_csv(file_path_activity_granularity)
user_list = df["Student ID"].unique()

# list for every column of the final dataframe
student_id_column = []
course_area_column = []
component_column = []
unix_time_column = []
duration_column = []
estimated_duration_column = []

for user in user_list:
  user_df = df[df["Student ID"] == user]
  
  for key1, course_area_df in user_df.groupby((user_df["Course_Area"].shift() != user_df["Course_Area"]).cumsum()):
    for key2, component_df in course_area_df.groupby((course_area_df["Component"].shift() != course_area_df["Component"]).cumsum()):
      component_df_dict = component_df.to_dict('records')
      sum_duration = 0
      sum_estimated_duration = 0
      for row in component_df_dict:
        sum_duration += row["Duration"]
        sum_estimated_duration += row["Estimated_duration"]
      student_id_column.append(user)
      course_area_column.append(component_df_dict[0]["Course_Area"])
      component_column.append(component_df_dict[0]["Component"])
      unix_time_column.append(component_df_dict[0]["Unix_Time"])
      duration_column.append(sum_duration)
      estimated_duration_column.append(sum_estimated_duration)

data_task_granularity = {'Student ID': student_id_column,
						 'Course_Area': course_area_column,
						 'Component': component_column,
						 'Unix_Time': unix_time_column,
						 'Estimated_duration': estimated_duration_column,
						 'Duration': duration_column}
df_task = pd.DataFrame(data_task_granularity)
df_task.to_csv(file_path_task_granularity) 
```

### Divide your log-data into sessions

If you are only interested in this functionality, you just need two files from the repository: **constants.py** and **functions_algorithm.py**.

1. Adjust the algorithm session identification settings in **constants.py** file to suit your data:

* include in the `site_area` list all the _Course_Area_ values that are associated with site-level logs in your dataset. This list is essential for identifying course and learning sessions. For example, `site_area = ["Overall Site", "Authentication"]`. If, on the other hand, you are only interested in study sessions you can leave this list empty For example, `site_area = []`.
* include all _Component_ values associated with quality learning in the `learning_components` list. This list is only used for identifying learning sessions. For example, `learning_components = ["Assignment", "File", "Lesson", "URL"]`.

2. Run `get_session_logs()` function from **functions_algorithm.py**
```
get_session_logs(chosen_df,
                 specific_moodle_course,
                 type_of_session,
                 authentication_flag,
                 stt_flag,
                 del_attendance_session_flag,
                 outlier_detection_switch,
                 general_stt,
                 active_component_stt_dict)
```

Parameters:
* **_chosen_df_ : pandas.DataFrame** - dataframe of logs that will be separated into sessions.
* **_specific_moodle_course_: list** - you may specify the list of courses here if you only want to see sessions that include logs from those courses. For example, ``["Course_A", "Course_B"]``. Otherwise, pass an empty list ``[]``. 
* **_type_of_session_ : {"session_study", "session_course", "session_learning"}** - type of sessions you would like to separate the logs into. Chose one of the listed options and pass it as a string value.
* **_authentication_flag_ : bool** - ``True`` if you want an algorithm to use the Login and Logout _Component_ values as a signal for a session start or end. ``False`` otherwise.
* **_stt_flag_ : bool** - ``True`` if you want to use Session Timeout Threshold (STT) as a signal for a session end. ``False`` otherwise.
* **_del_attendance_session_flag_ : bool** - ``True`` if you want to delete the sessions where students used the platform just to take attendance. ``False`` otherwise.
* **_outlier_detection_switch_ : bool** - ``True`` if you want to use _Time-off-task_ to identify sessions. ``False`` if you want to use _Elapsed time_.
* **_general_stt_: float** - value of Session Timeout Threshold (STT) in minutes.
* **_active_component_stt_dict_: dict** - all the component-specific Session Timeout Thresholds (STTs) in minutes. For all sessions where the last component that happened before inactivity has a component-specific STT, this STT will be used instead of the general one. Each component-specific STT should be specified in this form ``{"component_name" (string): assigned_threshold (float)}``. For example, ``{"Attendance": 15, "Quiz": 10.5}``. If you don't want to assign any component-specific STTs, pass an empty dictionary ``{}``.

Returns:
* **_sessions_ : list** - list of all the resulting sessions. Each session is represented as a list of logs belonging to it.
* **_reason_to_end_ : list** - list of the same length as ``sessions``. Each entry in this list explains the reason why the session with the same index in ``sessions`` was interrupted. The explanation has a form of tuple: ``("description_of_behavior_after_inactivity", "last_component_before_inactivity", inactivity_duration)``. For example, ``('Different course/area after inactivity', 'Attendance', 7312.0)``

### Get Session Timeout Threshold suggestion

If you are only interested in this functionality, you just need two files from the repository: **constants.py** and **functions_algorithm.py**.

1. Adjust the algorithm settings in **constants.py** file to suit your data:
* include in the `site_area` list all the _Course_Area_ values that are associated with site-level logs in your dataset. This list is essential for identifying course and learning sessions. For example, `site_area = ["Overall Site", "Authentication"]`. If, on the other hand, you are only interested in study sessions you can leave this list empty For example, `site_area = []`.
* include all _Component_ values associated with quality learning in the `learning_components` list. This list is only used for identifying learning sessions. For example, `learning_components = ["Assignment", "File", "Lesson", "URL"]`.
* if you want, you can adjust `min_stt` and `max_stt` values. These values represent the smallest and the greatest STT values considered by the STT suggestion algorithm.

2. Run `get_session_timeout_threshold_suggestion()` function from **functions_algorithm.py**
```
get_session_timeout_threshold_suggestion(chosen_df,
                                         specific_moodle_course,
                                         type_of_session,
                                         specific_component)
```

Parameters:
* **_chosen_df_ : pandas.DataFrame** - dataframe of logs for which you would like to get the STT suggestion.
* **_specific_moodle_course_: list** - if you want to get an STT suggestion that can be used specifically for sessions that include logs from certain courses, you may specify the list of these courses here. For example, ``["Course_A", "Course_B"]``. Otherwise, pass an empty list ``[]``. 
* **_type_of_session_ : {"session_study", "session_course", "session_learning"}** - type of sessions for which the suggestion is computed. Chose one of the listed options and pass it as a string value.
* **_specific_component_ : string or None** - ``None`` if you want to get general STT suggestion. If, on the other hand, you want to get an STT suggestion for a specific _Component_ value, you should pass this value in string format. For example, ``"File"``.

Returns:
* **_stt_suggestion_ : int or string** - STT suggestion in minutes. However, if an algorithm doesn't get enough examples to make a suggestion, an error message is returned.

### Run Visual Tool to determine time-windows

If you are interested in running the Visual Tool, you need all the files from the repository.

1. Adjust the settings in **constants.py** file to suit your data:

* change the first two variables to tell the Visual Tool where to find the files that contain the dataset. `data_dir_path` contains the path to the folder where the data is stored. For example, `data_dir_path = "data/"`. `file_names` dictionary contains the names of the files (in the `data_dir_path` folder) where logs at activity and task granularity are stored. For example, `file_names = {"activity_granularity": "data_activity_granularity.csv", "task_granularity": "data_task_granularity.csv"}`. 
* adjust `specific_moodle_course_filter` dictionary to represent the courses that are present in your dataset. For each course, you can specify its value in the dataset, and the label that will be visualized in the Tool. For example, `specific_moodle_course_filter = [{"label": "Course A", "value": "Course_A"}]`.
* `min_date_allowed` and `max_date_allowed` control the range of dates that the user can choose in the "Select the time interval" filter. For example, `min_date_allowed = date(2021, 1, 1)`.
* include in the `site_area` list all the _Course_Area_ values that are associated with site-level logs in your dataset. This list is essential for identifying course and learning sessions. For example, `site_area = ["Overall Site", "Authentication"]`. If, on the other hand, you are only interested in study sessions you can leave this list empty For example, `site_area = []`.
* include all _Component_ values associated with quality learning in the `learning_components` list. This list is only used for identifying learning sessions. For example, `learning_components = ["Assignment", "File", "Lesson", "URL"]`.
* if you want, you can adjust `min_stt` and `max_stt` values. These values represent the smallest and the greatest STT values considered by the Session Timeout Threshold suggestion algorithm. For example, `max_stt_allowed = 60`

2. Run the Visual Tool

Make sure that you have all the necessary libraries, modules, and packages installed on your machine.
```
pip install -r requirements.txt
```

Run the app.py file.

```
python app.py
```

## License

This project is licensed under the terms of the GNU General Public License v3.0.

If you use the library in an academic setting, please cite the following papers:

> A. Maslennikova, D. Rotelli and A. Monreale, "Visual Analytics for Session-based Time-Windows Identification in Virtual Learning Environments," 2022 26th International Conference Information Visualisation (IV), Vienna, Austria, 2022, pp. 251-258, https://ieeexplore.ieee.org/abstract/document/10017679

```
@inproceedings{maslennikova2022visual,
  title={Visual Analytics for Session-based Time-Windows Identification in Virtual Learning Environments},
  author={Maslennikova, Aleksandra and Rotelli, Daniela and Monreale, Anna},
  booktitle={2022 26th International Conference Information Visualisation (IV)},
  pages={251--258},
  year={2022},
  organization={IEEE}
}
```

## Acknowledgements
This work has been partially supported by EU – Horizon 2020 Program under the scheme “INFRAIA-01-2018-2019 – Integrating Activities for Advanced Communities”, Grant Agreement n.871042, “SoBigData++: European Integrated Infrastructure for Social Mining and Big Data Analytics” (http://www.sobigdata.eu), the scheme "HORIZON-INFRA-2021-DEV-02 - Developing and consolidating the European research infrastructures landscape, maintaining global leadership (2021)", Grant Agreement n.101079043, “SoBigData RI PPP: SoBigData RI Preparatory Phase Project”, by NextGenerationEU - National Recovery and Resilience Plan (Piano Nazionale di Ripresa e Resilienza, PNRR) - Project: “SoBigData.it - Strengthening the Italian RI for Social Mining and Big Data Analytics” - Prot. IR0000013 - Avviso n. 3264 del 28/12/2021, and by PNRR - M4C2 - Investimento 1.3, Partenariato Esteso PE00000013 - ``FAIR - Future Artificial Intelligence Research" - Spoke 1 "Human-centered AI", funded by the European Commission under the NextGeneration EU programme.

## Contact(s)
[Aleksandra Maslennikova](mailto:aleksandra.maslennikova@phd.unipi.it) - Department of Computer Science - University of Pisa