SELECT reports_experiment.subject_id,
       reports_experiment.experiment,
       reports_session.session_num,
       reports_pairedassociatelearningevent.stim_list,
       reports_pairedassociatelearningevent.correct as recalled,
       count(reports_pairedassociatelearningevent.correct) AS count_recalled
FROM reports_pairedassociatelearningevent
JOIN reports_event ON reports_event.id = reports_pairedassociatelearningevent.event_ptr_id
JOIN reports_session ON reports_event.session_id = reports_session.id
JOIN reports_experiment ON reports_session.experiment_id = reports_experiment.id
WHERE reports_pairedassociatelearningevent.list > 3
  AND reports_event.type = "STUDY_PAIR"
  AND reports_experiment.experiment NOT IN ("PAL1")
GROUP BY subject_id,
         reports_experiment.experiment,
         reports_session.session_num,
         reports_pairedassociatelearningevent.stim_list,
         reports_pairedassociatelearningevent.correct