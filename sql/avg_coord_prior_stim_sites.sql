SELECT DISTINCT reports_localization.subject_id,
                reports_bipolar.contact_name,
                reports_experiment.experiment,
                reports_session.session_num,
                reports_montage.montage_num,
                reports_bipolaratlas.x,
                reports_bipolaratlas.y,
                reports_bipolaratlas.z
FROM reports_stim
JOIN reports_event ON reports_event.id = reports_stim.event_id
JOIN reports_session ON reports_event.session_id = reports_session.id
JOIN reports_experiment ON reports_experiment.id = reports_session.experiment_id
JOIN reports_bipolar ON ((contact_1_id = anode_id
                          AND contact_2_id = cathode_id)
                         OR (contact_1_id = cathode_id
                             AND contact_2_id = anode_id))
JOIN reports_bipolaratlas ON (reports_bipolar.id = reports_bipolaratlas.contact_id)
JOIN reports_montage ON (reports_montage.id = reports_bipolar.montage_id)
JOIN reports_localization ON (reports_localization.id = reports_montage.localization_id)
WHERE reports_bipolaratlas.atlas_name = "avg"