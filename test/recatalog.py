import os


def find_runs(instrument, ipts, run_min, run_max, legacy=False):
    base_path = "/SNS/%s/IPTS-%s/nexus/" % (instrument.upper(), ipts)
    for r in range(run_min, run_max):
        filepath = "%s/%s_%s.nxs.h5" % (base_path, instrument.upper(), r)
        legacypath = "/SNS/%s/IPTS-%s/0/%s/NeXus/%s_%r_event.nxs" % (
            instrument.upper(),
            ipts,
            r,
            instrument.upper(),
            r,
        )
        if not legacy:
            os.system(
                "python simple_producer.py -b %s -i %s -r %s -d %s --catalog"
                % (instrument.upper(), ipts, r, filepath)
            )
            os.system(
                "python simple_producer.py -b %s -i %s -r %s -d %s --reduction_catalog"
                % (instrument.upper(), ipts, r, filepath)
            )
        else:
            os.system(
                "python simple_producer.py -b %s -i %s -r %s -d %s --catalog"
                % (instrument.upper(), ipts, r, legacypath)
            )
            # os.system
            # ("python simple_producer.py -b %s -i %s -r %s -d %s --reduction_catalog" % (instrument.upper(),
            #  ipts,
            #  r,
            #  legacypath))


# find_runs('HYS', 10717, 42578, 42579)
# find_runs('ARCS', 10094, 48147, 48156, legacy=True)
# find_runs('BSS', 10679, 35275, 35290, legacy=True)
# find_runs('CNCS', 9358, 77294, 77345, legacy=True)
# find_runs('EQSANS', 11094, 31807, 31822, legacy=True)
# find_runs('NOM', 10724, 25452, 25481, legacy=True)
# find_runs('PG3', 2767, 18104, 18107, legacy=True)
# find_runs('REF_L', 10328, 110610, 110638, legacy=True)
# find_runs('REF_M', 10719, 16034, 16038, legacy=True)
# find_runs('SEQ', 7561, 48860, 48873)
# find_runs('SNAP', 10254, 15229, 15234, legacy=True)
# find_runs('TOPAZ', 9949, 9408, 9409, legacy=True)
# find_runs('VIS', 11944, 3572, 3576)
find_runs("VULCAN", 10076, 45783, 45784, legacy=True)
