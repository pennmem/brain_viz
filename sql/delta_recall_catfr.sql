SELECT reports_experiment.subject_id,
       reports_experiment.experiment,
       reports_session.session_num,
       reports_categoricalfreerecallevent.stim_list,
       reports_categoricalfreerecallevent.recalled,
       count(reports_categoricalfreerecallevent.recalled) as count_recalled
FROM reports_categoricalfreerecallevent
JOIN reports_event ON reports_event.id = reports_categoricalfreerecallevent.event_ptr_id
JOIN reports_session ON reports_event.session_id = reports_session.id
JOIN reports_experiment ON reports_session.experiment_id = reports_experiment.id
WHERE reports_categoricalfreerecallevent.list > 3
  AND reports_event.type in ("WORD", "STUDY_PAIR")
  AND reports_experiment.experiment NOT IN ("catFR1")
GROUP BY subject_id, reports_experiment.experiment, reports_session.session_num, reports_categoricalfreerecallevent.stim_list, reports_categoricalfreerecallevent.recalled