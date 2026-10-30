"""Run on Nobara with AWS CLI credentials. Resize only the approved psitwin EC2."""
import json
import subprocess

INSTANCE = 'i-07aad4ab7a1e6b43b'
REGION = 'us-east-1'
TARGET_TYPE = 't3.xlarge'


def aws(*args):
    response = subprocess.run(['aws', 'ec2', *args, '--region', REGION,
        '--output', 'json', '--no-cli-pager'], capture_output=True, text=True, check=True)
    return json.loads(response.stdout) if response.stdout.strip() else {}


def main():
    stopped = False
    try:
        data = aws('describe-instances', '--instance-ids', INSTANCE)
        instance = data['Reservations'][0]['Instances'][0]
        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
        if tags.get('Name') != 'psitwin' or instance.get('PublicIpAddress') != '35.171.142.151':
            raise SystemExit('La instancia/IP no coincide. No se modificó nada.')
        state = instance['State']['Name']
        if state not in {'running', 'stopped'}:
            raise SystemExit(f'Estado {state}; esperar a que termine la transición antes de repetir.')
        if instance['InstanceType'] != TARGET_TYPE:
            if state == 'running':
                print('Deteniendo únicamente psitwin para ampliar memoria...', flush=True)
                aws('stop-instances', '--instance-ids', INSTANCE)
                aws('wait', 'instance-stopped', '--instance-ids', INSTANCE)
            stopped = True
            print('Solicitando t3.xlarge: 16 GiB y 4 vCPU...', flush=True)
            aws('modify-instance-attribute', '--instance-id', INSTANCE,
                '--instance-type', json.dumps({'Value': TARGET_TYPE}))
        print('Encendiendo psitwin y esperando las comprobaciones de salud...', flush=True)
        aws('start-instances', '--instance-ids', INSTANCE)
        stopped = False
        aws('wait', 'instance-status-ok', '--instance-ids', INSTANCE)
        result = aws('describe-instances', '--instance-ids', INSTANCE)['Reservations'][0]['Instances'][0]
        print(json.dumps({'Estado': result['State']['Name'], 'Tipo': result['InstanceType'],
                          'IP': result.get('PublicIpAddress')}, indent=2))
    except subprocess.CalledProcessError as exc:
        print('AWS rechazó o no completó la operación:', exc.stderr.strip(), flush=True)
        if stopped:
            print('Intentando volver a encender psitwin con su configuración actual...', flush=True)
            try:
                aws('start-instances', '--instance-ids', INSTANCE)
                print('Arranque solicitado. Confirmar el estado en EC2.', flush=True)
            except subprocess.CalledProcessError as recovery:
                print('No se pudo solicitar el arranque:', recovery.stderr.strip(), flush=True)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
