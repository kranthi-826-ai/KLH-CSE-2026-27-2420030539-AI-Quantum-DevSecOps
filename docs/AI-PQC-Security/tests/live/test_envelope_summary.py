import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('envelope_summary',Path(__file__).resolve().parents[2]/'scripts/summarize_envelope_benchmark.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    data=[];modes=[]
    for mode in sorted(module.MODES):
        data.append({'benchmark':'com.pqc.security.crypto.benchmark.EnvelopeBenchmark.freshKeyRoundTrip',
            'mode':'avgt','params':{'mode':mode},'forks':5,'threads':1,'warmupIterations':5,
            'measurementIterations':10,'warmupTime':'1 s','measurementTime':'1 s',
            'primaryMetric':{'score':2.,'scoreError':.1,'scoreUnit':'ms/op','scoreConfidence':[1.9,2.1],
                             'rawData':[[2.]*10 for _ in range(5)]},
            'secondaryMetrics':{'gc.alloc.rate.norm':{'scoreUnit':'B/op','score':10000.}}})
        modes.append({'mode':mode,'encapsulationBytes':100,'nonceBytes':12,'ciphertextBytes':4112,
            'signatureMinBytes':50,'signatureMaxBytes':52,'rawComponentsMinBytes':4274,'rawComponentsMaxBytes':4276})
    return data,{'schema':'matched-envelope-sizes-v1','payloadBytes':4096,'samplesPerMode':16,'modes':modes}


class EnvelopeSummaryTests(unittest.TestCase):
    def test_keeps_fork_means_and_does_not_invent_request_percentiles(self):
        result=module.summarize(*fixture())
        self.assertEqual(len(result['profiles']),3)
        self.assertEqual(result['profiles'][0]['forkMeanMs'],[2.]*5)
        self.assertTrue(result['notRequestPercentiles'])
        self.assertFalse(result['adaptiveSystemSpeedupMeasured'])

    def test_rejects_wrong_protocol_nan_and_incomplete_raw_samples(self):
        for change in ('forks','threads','measurementIterations','units','nan','missing','mean'):
            data,sizes=fixture();row=data[0]
            if change in ('forks','threads','measurementIterations'):row[change]=2
            elif change=='units':row['primaryMetric']['scoreUnit']='us/op'
            elif change=='nan':row['primaryMetric']['rawData'][0][0]=float('nan')
            elif change=='missing':row['primaryMetric']['rawData'].pop()
            else:row['primaryMetric']['score']=3.
            with self.subTest(change=change),self.assertRaises(ValueError):module.summarize(data,sizes)

    def test_rejects_duplicate_profiles_and_inconsistent_sizes(self):
        data,sizes=fixture()
        data[1]=copy.deepcopy(data[0])
        with self.assertRaises(ValueError):module.summarize(data,sizes)
        data,sizes=fixture();sizes['modes'][0]['rawComponentsMinBytes']+=1
        with self.assertRaises(ValueError):module.summarize(data,sizes)

if __name__=='__main__':unittest.main()
