SELECT reports_experiment.subject_id,
       reports_experiment.experiment,
       reports_session.session_num,
       reports_freerecallevent.stim_list,
       reports_freerecallevent.recalled,
       count(reports_freerecallevent.recalled) AS count_recalled
FROM reports_freerecallevent
JOIN reports_event ON reports_event.id = reports_freerecallevent.event_ptr_id
JOIN reports_session ON reports_event.session_id = reports_session.id
JOIN reports_experiment ON reports_session.experiment_id = reports_experiment.id
WHERE reports_freerecallevent.list > 3
  AND reports_event.type = "WORD"
  AND reports_experiment.experiment NOT IN ("FR1")
GROUP BY subject_id,
         reports_experiment.experiment,
         reports_session.session_num,
         reports_freerecallevent.stim_list,
         reports_freerecallevent.recalled