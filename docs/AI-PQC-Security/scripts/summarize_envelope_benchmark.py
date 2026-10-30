"""Validate frozen JMH evidence and summarize fork means, never request-tail percentiles."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
MODES={'CLASSICAL','HYBRID','PQC'}


def positive(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>0


def summarize(data, sizes):
    if not isinstance(data,list) or len(data)!=3 or {row.get('params',{}).get('mode') for row in data}!=MODES:
        raise ValueError('Require exactly three distinct matched benchmark modes')
    if sizes.get('schema')!='matched-envelope-sizes-v1' or sizes.get('samplesPerMode')!=16 or sizes.get('payloadBytes')!=4096:
        raise ValueError('Unexpected size-sampling protocol')
    size_rows=sizes.get('modes',[])
    if len(size_rows)!=3 or {row.get('mode') for row in size_rows}!=MODES:
        raise ValueError('Missing or duplicate profile size samples')
    result=[]
    for row in sorted(data,key=lambda entry:entry['params']['mode']):
        if (not row.get('benchmark','').endswith('EnvelopeBenchmark.freshKeyRoundTrip') or row.get('mode')!='avgt'
            or row.get('forks')!=5 or row.get('threads')!=1 or row.get('warmupIterations')!=5
            or row.get('measurementIterations')!=10 or row.get('warmupTime')!='1 s' or row.get('measurementTime')!='1 s'):
            raise ValueError('JMH protocol does not match frozen workload')
        metric=row['primaryMetric']
        raw=metric.get('rawData',[])
        if metric.get('scoreUnit')!='ms/op' or len(raw)!=5 or any(len(fork)!=10 or not all(positive(n) for n in fork) for fork in raw):
            raise ValueError('Missing finite measurements or wrong units/fork counts')
        interval=metric.get('scoreConfidence',[])
        if not positive(metric.get('score')) or not positive(metric.get('scoreError')) or len(interval)!=2 or not all(positive(n) for n in interval):
            raise ValueError('JMH summary contains invalid estimates')
        fork_means=[statistics.mean(fork) for fork in raw]
        if not math.isclose(statistics.mean(fork_means),metric['score'],rel_tol=1e-9):
            raise ValueError('Recorded mean does not match raw iterations')
        mode=row['params']['mode']
        size=next(entry for entry in size_rows if entry['mode']==mode)
        for field in ('rawComponentsMinBytes','rawComponentsMaxBytes','encapsulationBytes','nonceBytes',
                      'ciphertextBytes','signatureMinBytes','signatureMaxBytes'):
            if not isinstance(size.get(field),int) or isinstance(size[field],bool) or size[field]<=0:
                raise ValueError('Invalid sampled size')
        fixed=size['encapsulationBytes']+size['nonceBytes']+size['ciphertextBytes']
        if (size['nonceBytes']!=12 or size['ciphertextBytes']!=4112 or size['signatureMinBytes']>size['signatureMaxBytes']
            or size['rawComponentsMinBytes']!=fixed+size['signatureMinBytes']
            or size['rawComponentsMaxBytes']!=fixed+size['signatureMaxBytes']):
            raise ValueError('Size components do not match the common payload boundary')
        allocation=row.get('secondaryMetrics',{}).get('gc.alloc.rate.norm',{})
        if allocation.get('scoreUnit')!='B/op' or not positive(allocation.get('score')):
            raise ValueError('Missing matched allocation profile')
        result.append({'mode':mode,'meanMsPerOperation':metric['score'],'jmhErrorMs':metric['scoreError'],
            'jmhConfidenceIntervalMs':interval,'forkMeanMs':fork_means,'medianForkMeanMs':statistics.median(fork_means),
            'minForkMeanMs':min(fork_means),'maxForkMeanMs':max(fork_means),
            'allocatedBytesPerOperation':allocation['score'],'sampledSizes':size})
    return {'schema':'matched-envelope-summary-v1','payloadBytes':4096,'profiles':result,
        'latencyScope':'Provider construction, both key generations, seal/open, equality and wipe; no AI/policy/HTTP/database',
        'notRequestPercentiles':True,'wireSizesMeasured':False,'adaptiveSystemSpeedupMeasured':False,
        'confidenceIntervalMeaning':'JMH default 99.9% statistical interval, not a hardware/generalization guarantee'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    folder=args.directory.resolve()
    if folder.parent!=(ROOT/'ml/artifacts').resolve():raise ValueError('Use an immediate artifact child')
    output=folder/'summary.json'
    if output.exists():raise ValueError('Refusing to overwrite a prior analysis')
    receipt=json.loads((folder/'verification.json').read_text(encoding='utf-8-sig'))
    if not receipt.get('passed') or not receipt.get('ownedProcessStopped'):
        raise ValueError('Benchmark receipt is incomplete or not passing')
    for name,key in [('jmh.json','resultSha256'),('sizes.json','sizesSha256')]:
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=receipt.get(key):
            raise ValueError('Input checksum does not match completed-run receipt')
    result=summarize(json.loads((folder/'jmh.json').read_text(encoding='utf-8-sig')),
                     json.loads((folder/'sizes.json').read_text(encoding='utf-8-sig')))
    result['sourceRevision']=receipt['revision']
    result['jarSha256']=receipt['jarSha256']
    with output.open('x',encoding='utf-8') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
