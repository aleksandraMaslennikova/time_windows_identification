import numpy as np
import matplotlib.pyplot as plt

import constants

# -------------------------------------------------------------------------------
# --- FUNCTIONS THAT ARE USED TO DIVIDE DATASET IN SESSIONS OF DIFFERENT TYPE ---
# -------------------------------------------------------------------------------


# --- DIVIDE LOGS INTO SESSIONS OF CORRESPONDING SESSION TYPE ---
def get_session_logs(chosen_df,
                     specific_moodle_course,
                     type_of_session,
                     authentication_flag,
                     stt_flag,
                     del_attendance_session_flag,
                     outlier_detection_switch,
                     general_stt,
                     active_component_stt_dict):
    def estimate_inactivity_period_between_sessions(log_row):
        pause = None
        if outlier_detection_switch:
            # in case of time-off-task:
            # pause = duration (log_timestamp[i+1] - log_timestamp[i])
            #         - estimated_duration (estimation of actual time-on-task)
            pause = log_row["Duration"] - log_row["Estimated_Duration"]
        elif log_row["Component"] in active_component_stt_dict.keys():
            # in case of elapsed time, the STT represents the time we assume the student spent on-task, consequently:
            # pause = duration (log_timestamp[i+1] - log_timestamp[i]) - STT
            # when the specific STT is set for the Component, this specific STT is used for the estimation
            pause = log_row["Duration"] - active_component_stt_dict[log_row["Component"]]
        else:
            # when we do not have the specific component STT, the general one is used
            pause = log_row["Duration"] - general_stt
        return pause

    # interpretation of session settings
    is_course_session = type_of_session == "session_course"
    is_learning_session = type_of_session == "session_learning"
    is_study_session = is_course_session is False and is_learning_session is False
    general_stt = 0 if general_stt is None else general_stt

    user_list = chosen_df["Student ID"].unique()
    sessions = []
    reason_to_end = []
    for user in user_list:  # the logs are being divided into sessions one student at a time
        chosen_df_user_dict = chosen_df[chosen_df["Student ID"] == user].to_dict("records")
        # variable which accumulates all the logs of the current session
        # (afterwards, we save these logs as sessions list entry, and assign this variable the empty list value)
        session_logs = []
        for i in range(len(chosen_df_user_dict)):  # analysing the log of each student separately one log-line at a time
            # INTRODUCING VARIABLES USED IN THE CHECK LOOP
            previous_row_component = chosen_df_user_dict[i-1] if i != 0 else None
            current_row = chosen_df_user_dict[i]
            session_logs.append(current_row)

            # CHECK THE CONDITIONS FOR SESSION INTERRUPTION
            # 1) Authentication log checks (only if the authentication identification is used)
            # if we encounter log-in, it means the new session starts (with two exceptions:
            # - if this log-in is the first log of the session:
            # it means that we have already finished the previous session for some other reason,
            # consequently we do not have to do it the second time;
            # - if previous row is also a log-in: it represents the situation where a student failed to enter
            # the correct username and password the first time => should be considered as the same session
            # (can be still divided into different sessions by other checks (for instance, STT)))
            if authentication_flag \
                    and current_row["Component"] == "Login"\
                    and len(session_logs) != 1 \
                    and previous_row_component != "Login":
                # in this case the session should not include the current log, whilst login is a part of the new session
                sessions.append(session_logs[:-1])
                session_logs = [current_row]
                reason_to_end.append(("Authentication",
                                      current_row["Component"],
                                      estimate_inactivity_period_between_sessions(chosen_df_user_dict[i-1])))
            # if we encounter log-out, it means that a student voluntary ended the session
            elif authentication_flag and current_row["Component"] == "Logout":
                sessions.append(session_logs)
                session_logs = []
                reason_to_end.append(("Authentication",
                                      current_row["Component"],
                                      estimate_inactivity_period_between_sessions(current_row)))

            if len(session_logs) != 0 and i+1 != len(chosen_df_user_dict):
                next_row = chosen_df_user_dict[i+1]
                # 2) Change of Course (only for course and learning sessions)
                if (is_course_session or is_learning_session) \
                        and current_row["Course_Area"] not in constants.site_area \
                        and current_row["Course_Area"] != next_row["Course_Area"]:
                    # additional check: if the student was in a Course, afterwards switched to Site Area
                    # and immediately after came back to the same Course, we do not interrupt the course session.
                    # This case can represent that the student has received a message, checked the grades
                    # or calendar, etc., which in our opinion means that the student is still working on the course.
                    if not (next_row["Course_Area"] in constants.site_area and i + 2 != len(chosen_df_user_dict)
                            and chosen_df_user_dict[i+2]["Course_Area"] == current_row["Course_Area"]):
                        sessions.append(session_logs)
                        session_logs = []
                        if is_course_session:
                            reason_to_end.append(("Change of course",
                                                  current_row["Component"],
                                                  estimate_inactivity_period_between_sessions(current_row)))
                        if is_learning_session:
                            reason_to_end.append(("Quality learning stopped",
                                                  current_row["Component"],
                                                  estimate_inactivity_period_between_sessions(current_row)))

                # 3) Stop working on Quality Learning Modules (only for learning session)
                if is_learning_session \
                        and current_row["Component"] in constants.learning_components \
                        and next_row["Component"] not in constants.learning_components:
                    # additional check: to go from one learning module to another,
                    # the students can navigate through Course_home page,
                    # in this case we do not interrupt the learning session
                    if not (next_row["Component"] == "Course_home"
                            and i + 2 != len(chosen_df_user_dict)
                            and chosen_df_user_dict[i+2]["Component"] not in constants.learning_components):
                        sessions.append(session_logs)
                        session_logs = []
                        reason_to_end.append(("Quality learning stopped",
                                              current_row["Component"],
                                              estimate_inactivity_period_between_sessions(current_row)))

                # 4) Session timeout threshold log checks (only if the STT identification is used)
                if stt_flag:
                    # in case of time-off-task temporal metric, the timeout is the difference between
                    # duration (log_timestamp[i+1] - log_timestamp[i])
                    # and estimated_duration (estimation of actual time-on-task);
                    # in case of the elapsed-time temporal metric,
                    # just the duration (log_timestamp[i+1] - log_timestamp[i]) is used
                    if outlier_detection_switch:
                        inactivity_period = current_row["Duration"] - current_row["Estimated_Duration"]
                    else:
                        inactivity_period = current_row["Duration"]
                    # check if the current Component has the specific STT or the general one should be used
                    if current_row["Component"] in active_component_stt_dict.keys():
                        stt_current_component = active_component_stt_dict[current_row["Component"]]
                    else:
                        stt_current_component = general_stt
                    # check if inactivity_period is bigger than assigned STT
                    # (stt is stored in minutes, timeout in seconds)
                    if inactivity_period > stt_current_component*60.0:
                        sessions.append(session_logs)
                        session_logs = []

                        # analysing the current state of student activity that lead to the session interruption
                        # (for STT suggestion algorithm)
                        if is_study_session:
                            if current_row["Course_Area"] != next_row["Course_Area"]:
                                reason_to_end.append(("Different course/area after inactivity",
                                                      current_row["Component"],
                                                      estimate_inactivity_period_between_sessions(current_row)))
                            else:
                                if current_row["Course_Area"] not in constants.site_area:
                                    reason_to_end.append(("Same course after inactivity",
                                                          current_row["Component"],
                                                          estimate_inactivity_period_between_sessions(current_row)))
                                else:
                                    reason_to_end.append(("Same area after inactivity",
                                                          current_row["Component"],
                                                          estimate_inactivity_period_between_sessions(current_row)))
                        if is_course_session:
                            if current_row["Course_Area"] == next_row["Course_Area"] \
                                    or (next_row["Course_Area"] in constants.site_area
                                        and i + 2 < len(chosen_df_user_dict)
                                        and current_row["Course_Area"] == chosen_df_user_dict[i+2]["Course_Area"]):
                                reason_to_end.append(("Same course after inactivity",
                                                      current_row["Component"],
                                                      estimate_inactivity_period_between_sessions(current_row)))
                            else:
                                reason_to_end.append(("Site area after inactivity",
                                                      current_row["Component"],
                                                      estimate_inactivity_period_between_sessions(current_row)))
                        if is_learning_session:
                            if next_row["Component"] in constants.learning_components:
                                reason_to_end.append(("Quality learning after inactivity",
                                                      current_row["Component"],
                                                      estimate_inactivity_period_between_sessions(current_row)))
                            else:
                                reason_to_end.append(("Course home after inactivity",
                                                      current_row["Component"],
                                                      estimate_inactivity_period_between_sessions(current_row)))
        # adding the last session to the list
        # (after we have already seen scrolled through all the logs of a certain student)
        if len(session_logs) != 0:
            sessions.append(session_logs)
            reason_to_end.append(("Final log",
                                  chosen_df_user_dict[-1]["Component"],
                                  estimate_inactivity_period_between_sessions(chosen_df_user_dict[-1])))

    # FILTERING SESSIONS (to only return the sessions of interest)
    # at this point we divided all the logs into sessions.
    # However, we might only be interested in the session related to some specific course
    # (specific_moodle_course variable); also we have divided all the logs into sessions,
    # in case of course and learning sessions, we still need to check that the session has at least one log
    # that does not belong to the site_area, etc.
    # Consequently, first of all, we need to filter out all the sessions that we are not interested in.
    no_specific_moodle_course = len(specific_moodle_course) == 0
    session_ids_to_del = []
    for i in range(len(sessions)):
        session = sessions[i]
        # 1) Does it have logs that are part of the courses that are of interest to us?
        # If we are not interested in a specific course, always True;
        # otherwise, we check if the session contains the logs that we need
        has_needed_course = False if not no_specific_moodle_course else True
        if not no_specific_moodle_course:
            for log in session:
                if log["Course_Area"] in specific_moodle_course:
                   has_needed_course = True
        if not has_needed_course:
            session_ids_to_del.append(i)
        else:
            # 2) All the course sessions and learning sessions should contain at least one log that does not belong
            # to site area. If we are interested in study sessions, this variable is always True;
            # otherwise, we check this condition
            has_area_of_interest = False if not is_study_session else True
            if not is_study_session:
                for log in session:
                    if log["Course_Area"] not in constants.site_area:
                        has_area_of_interest = True
            if not has_area_of_interest:
                session_ids_to_del.append(i)
            else:
                # 3) The learning sessions should contain at least one log with the quality learning component.
                # If we are interested in any other session type, always True; otherwise check the condition
                has_learning_component = False if is_learning_session else True
                if is_learning_session:
                    for log in session:
                        if log["Component"] in constants.learning_components:
                            has_learning_component = True
                if not has_learning_component:
                    session_ids_to_del.append(i)
                else:
                    # 4) In case we are also not interested in the only attendance sessions,
                    # we should check whether or not the current session is the attendnce one
                    if del_attendance_session_flag:
                        # we defined the attendance sessions in the following way
                        is_attendance_session = session[-1]["Component"] == "Attendance" \
                                                and len(session) <= 5
                        if is_attendance_session:
                            session_ids_to_del.append(i)
    # delete all the sessions that we are not interested in
    sessions = [sessions[i] for i in range(len(sessions)) if i not in session_ids_to_del]
    reason_to_end = [reason_to_end[i] for i in range(len(reason_to_end)) if i not in session_ids_to_del]

    # CLEANING SESSIONS' LOGS (to only return the logs that are effectively part of the session)
    # the way in which we divide the dataset into sessions, sometimes still results in the course and
    # learning sessions that include in the beginning or the end the site area logs, which should not be the case.
    # Consequently, before returning the sessions to the user, we delete those unnecessary logs within the sessions.
    if is_course_session or is_learning_session:
        for i in range(len(sessions)):
            session = sessions[i]
            # delete site area logs from the beginning of the session (if there are any)
            if session[0]["Course_Area"] in constants.site_area:
                id_until_which_delete_logs = 0
                current_log = session[id_until_which_delete_logs]
                while current_log["Course_Area"] in constants.site_area:
                    id_until_which_delete_logs += 1
                    current_log = session[id_until_which_delete_logs]
                del session[:id_until_which_delete_logs]
            # delete site area logs from the end of the session (if there are any)
            if session[-1]["Course_Area"] in constants.site_area:
                id_until_which_delete_logs = -1
                current_log = session[id_until_which_delete_logs]
                while current_log["Course_Area"] in constants.site_area:
                    id_until_which_delete_logs -= 1
                    current_log = session[id_until_which_delete_logs]
                del session[id_until_which_delete_logs+1:]
            # in case of the learning session,
            # we should also delete the non-quality learning modules from the beginning snd the end
            if is_learning_session:
                # delete non-quality learning component logs from the beginning of the session (if there are any)
                if session[0]["Component"] not in constants.learning_components:
                    id_until_which_delete_logs = 0
                    current_log = session[id_until_which_delete_logs]
                    while current_log["Component"] not in constants.learning_components:
                        id_until_which_delete_logs += 1
                        current_log = session[id_until_which_delete_logs]
                    del session[:id_until_which_delete_logs]
                # delete non-quality learning component logs from the end of the session (if there are any)
                if session[-1]["Component"] not in constants.learning_components:
                    id_until_which_delete_logs = -1
                    current_log = session[id_until_which_delete_logs]
                    while current_log["Component"] not in constants.learning_components:
                        id_until_which_delete_logs -= 1
                        current_log = session[id_until_which_delete_logs]
                    del session[id_until_which_delete_logs+1:]

    return sessions, reason_to_end


def get_classified_pause_length_list(pause_analysis, type_of_session, specific_component):
    result_dict = {}
    for pause_type in constants.stt_suggestion_final_pause_types[type_of_session]:
        result_dict[pause_type] = []
    for pause in pause_analysis:
        if pause[0] in constants.stt_suggestion_considered_pause_types[type_of_session] \
                and pause[2] != 0 \
                and (specific_component is None or pause[1] == specific_component):
            result_dict[constants.stt_suggestion_map[type_of_session][pause[0]]].append(pause[2] / 60.0)
    result_list = []
    for pause_type in constants.stt_suggestion_final_pause_types[type_of_session]:
        result_dict[pause_type] = np.array(result_dict[pause_type])
        result_dict[pause_type] = result_dict[pause_type].astype(float)
        result_list.append(result_dict[pause_type])
    return np.array(result_list, dtype=object)


def get_recommended_threshold(data, labels, max_stt):
    start_point = constants.min_stt_allowed
    end_point = max_stt  # constants.max_stt_allowed
    bins = list(range(start_point, end_point, 1))
    bins.append(end_point)
    n, bins, patches = plt.hist(data, bins, histtype='bar', stacked=False, fill=True, density=True)
    plt.close()
    index_real_pause = 0 if labels[0] in constants.stt_suggestion_real_pause else 1
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


def get_session_timeout_threshold_suggestion(chosen_df,
                                             specific_moodle_course,
                                             type_of_session,
                                             specific_component):
    _, pause_analysis = get_session_logs(chosen_df,
                                         specific_moodle_course,
                                         type_of_session,
                                         authentication_flag=False,
                                         stt_flag=True,
                                         del_attendance_session_flag=False,
                                         outlier_detection_switch=True,
                                         general_stt=0,
                                         active_component_stt_dict={})
    preprocessed_analysis = get_classified_pause_length_list(pause_analysis,
                                                             type_of_session,
                                                             specific_component)
    error_message = "There is not enough examples of this behaviour to make an STT recommendation"
    if len(preprocessed_analysis[0]) != 0 or len(preprocessed_analysis[1]) != 0:
        stt_suggestion = get_recommended_threshold(preprocessed_analysis,
                                                   constants.stt_suggestion_final_pause_types[type_of_session],
                                                   constants.max_stt_allowed)
        if stt_suggestion is not None and not np.isnan(stt_suggestion):
            return stt_suggestion
        else:
            return error_message
    else:
        return error_message
