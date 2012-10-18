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
SELECT pg_catalog.setval('report_statusqueue_id_seq', 16, true);
