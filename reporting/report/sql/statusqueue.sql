--
-- Known message queues
--
INSERT INTO report_statusqueue(id, name) VALUES (1, 'POSTPROCESS.DATA_READY');
INSERT INTO report_statusqueue(id, name) VALUES (2, 'POSTPROCESS.INFO');
INSERT INTO report_statusqueue(id, name) VALUES (3, 'POSTPROCESS.ERROR');

INSERT INTO report_statusqueue(id, name) VALUES (4, 'CATALOG.DATA_READY');
INSERT INTO report_statusqueue(id, name) VALUES (5, 'CATALOG.STARTED');
INSERT INTO report_statusqueue(id, name) VALUES (6, 'CATALOG.COMPLETE');

INSERT INTO report_statusqueue(id, name) VALUES (7, 'REDUCTION.DATA_READY');
INSERT INTO report_statusqueue(id, name) VALUES (8, 'REDUCTION.STARTED');
INSERT INTO report_statusqueue(id, name) VALUES (9, 'REDUCTION.DISABLED');
INSERT INTO report_statusqueue(id, name) VALUES (10,'REDUCTION.NOT_NEEDED');
INSERT INTO report_statusqueue(id, name) VALUES (11,'REDUCTION.COMPLETE');

INSERT INTO report_statusqueue(id, name) VALUES (12,'REDUCTION_CATALOG.DATA_READY');
INSERT INTO report_statusqueue(id, name) VALUES (13,'REDUCTION_CATALOG.STARTED');
INSERT INTO report_statusqueue(id, name) VALUES (14,'REDUCTION_CATALOG.COMPLETE');

INSERT INTO report_statusqueue(id, name) VALUES (15,'TRANSLATION.STARTED');
INSERT INTO report_statusqueue(id, name) VALUES (16,'TRANSLATION.COMPLETE');
INSERT INTO report_statusqueue(id, name) VALUES (17,'POSTPROCESS.CHECK');
SELECT pg_catalog.setval('report_statusqueue_id_seq', 17, true);

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