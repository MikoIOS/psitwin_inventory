"""Run on the workstation with AWS CLI credentials, not inside EC2.

Creates a dedicated web security group for psitwin; preserves its existing groups
and leaves other instances untouched. Does not launch or resize instances.
"""
import json
import subprocess

REGION = 'us-east-1'
INSTANCE = 'i-07aad4ab7a1e6b43b'
NAME = 'psitwin-ai-web-7a1e6b43b'
DESCRIPTION = 'HTTPS inference and ACME for psitwin only'


def aws(*args):
    result = subprocess.run(['aws', 'ec2', *args, '--region', REGION,
                             '--output', 'json', '--no-cli-pager'],
                            check=True, text=True, capture_output=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main():
    try:
        data = aws('describe-instances', '--instance-ids', INSTANCE)
        instance = data['Reservations'][0]['Instances'][0]
        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
        if tags.get('Name') != 'psitwin' or instance.get('PublicIpAddress') != '35.171.142.151':
            raise SystemExit('La instancia/IP no coincide con psitwin. No se modificó nada.')
        vpc = instance['VpcId']
        groups = aws('describe-security-groups', '--filters',
                     f'Name=vpc-id,Values={vpc}', f'Name=group-name,Values={NAME}')['SecurityGroups']
        if groups:
            group = groups[0]
            if group['Description'] != DESCRIPTION:
                raise SystemExit('Ya existe un grupo con configuración inesperada. Detener y revisar.')
            group_id = group['GroupId']
            attachments = aws('describe-network-interfaces', '--filters',
                              f'Name=group-id,Values={group_id}')['NetworkInterfaces']
            if any(eni.get('Attachment', {}).get('InstanceId') != INSTANCE for eni in attachments):
                raise SystemExit('El grupo está siendo usado por otro recurso. No se modificó nada.')
        else:
            group_id = aws('create-security-group', '--group-name', NAME,
                           '--description', DESCRIPTION, '--vpc-id', vpc)['GroupId']
            group = {'IpPermissions': []}
            print('Grupo dedicado creado:', group_id)
        for port, description in [(80, 'ACME HTTP validation'), (443, 'Authenticated AI HTTPS')]:
            exists = any(rule.get('IpProtocol') == 'tcp' and rule.get('FromPort') == port
                         and rule.get('ToPort') == port and
                         any(r.get('CidrIp') == '0.0.0.0/0' for r in rule.get('IpRanges', []))
                         for rule in group.get('IpPermissions', []))
            if not exists:
                aws('authorize-security-group-ingress', '--group-id', group_id,
                    '--ip-permissions', json.dumps([{
                        'IpProtocol': 'tcp', 'FromPort': port, 'ToPort': port,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': description}]}]))
                print('Puerto permitido:', port)
        existing = [item['GroupId'] for item in instance['SecurityGroups']]
        if group_id not in existing:
            aws('modify-instance-attribute', '--instance-id', INSTANCE,
                '--groups', *existing, group_id)
        print('Grupo asociado solo a psitwin. Grupos anteriores conservados.')
        print('No se abrieron 8100 ni 11434 en el grupo nuevo.')
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.stderr.strip()) from exc


if __name__ == '__main__':
    main()
