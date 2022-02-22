--
-- Known message queues
--
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (17, 'POSTPROCESS.CHECK', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (16, 'TRANSLATION.COMPLETE', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (15, 'TRANSLATION.STARTED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (20, 'REDUCTION_CATALOG.ERROR', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (14, 'REDUCTION_CATALOG.COMPLETE', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (13, 'REDUCTION_CATALOG.STARTED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (12, 'REDUCTION_CATALOG.DATA_READY', false);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (11, 'REDUCTION.COMPLETE', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (10, 'REDUCTION.NOT_NEEDED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (18, 'REDUCTION.ERROR', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (9,  'REDUCTION.DISABLED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (8,  'REDUCTION.STARTED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (7,  'REDUCTION.DATA_READY', false);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (21, 'REDUCTION.REQUEST', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (19, 'CATALOG.ERROR', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (6,  'CATALOG.COMPLETE', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (5,  'CATALOG.STARTED', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (4,  'CATALOG.DATA_READY', false);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (22, 'CATALOG.REQUEST', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (3,  'POSTPROCESS.ERROR', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (2,  'POSTPROCESS.INFO', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (1,  'POSTPROCESS.DATA_READY', true);
INSERT INTO report_statusqueue (id, name, is_workflow_input) VALUES (23, 'FERMI_REDUCTION.DATA_READY', true);
SELECT pg_catalog.setval('report_statusqueue_id_seq', 23, true);

--
-- Instruments - must be lowercase
--
INSERT INTO report_instrument(id, name) VALUES (2, 'hysa');
SELECT pg_catalog.setval('report_instrument_id_seq', 2, true);

--
-- Task definitions
--
INSERT INTO report_task(id, instrument_id_id, input_queue_id_id, task_class) VALUES (1, 2, 17, 'workflow_process.WorkflowProcess');

INSERT INTO report_task(id, instrument_id_id, input_queue_id_id, task_class) VALUES (2, 2, 1, ' ');
INSERT INTO report_task_task_queue_ids(task_id, statusqueue_id) VALUES (2, 4);
INSERT INTO report_task_task_queue_ids(task_id, statusqueue_id) VALUES (2, 7);
INSERT INTO report_task_success_queue_ids(task_id, statusqueue_id) VALUES (2, 6);
INSERT INTO report_task_success_queue_ids(task_id, statusqueue_id) VALUES (2, 11);
SELECT pg_catalog.setval('report_task_id_seq', 2, true);
