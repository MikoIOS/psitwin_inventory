import importlib.util
import json
from pathlib import Path
import subprocess
import pytest


def module():
    path = Path(__file__).resolve().parents[2] / 'scripts/ampliar_ec2_ia.py'
    spec = importlib.util.spec_from_file_location('resize_psitwin', path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.mark.parametrize('deny', [False, True])
def test_resize_targets_only_psitwin_and_restarts_on_denial(monkeypatch, deny):
    task = module()
    calls = []
    def aws(*args):
        calls.append(args)
        if args[0] == 'describe-instances':
            return {'Reservations': [{'Instances': [{
                'Tags': [{'Key': 'Name', 'Value': 'psitwin'}],
                'State': {'Name': 'running'}, 'PublicIpAddress': '35.171.142.151',
                'InstanceType': 't3.large' if len(calls) == 1 else 't3.xlarge'}]}]}
        if args[0] == 'modify-instance-attribute' and deny:
            raise subprocess.CalledProcessError(255, args, stderr='UnauthorizedOperation')
        return {}
    monkeypatch.setattr(task, 'aws', aws)
    if deny:
        with pytest.raises(SystemExit): task.main()
    else:
        task.main()
    mutate = next(call for call in calls if call[0] == 'modify-instance-attribute')
    assert mutate[2] == task.INSTANCE
    assert json.loads(mutate[-1]) == {'Value': 't3.xlarge'}
    start = [call for call in calls if call[0] == 'start-instances']
    assert len(start) == 1 and start[0][-1] == task.INSTANCE
    assert calls.index(start[0]) > calls.index(mutate)
