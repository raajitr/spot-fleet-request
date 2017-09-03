import boto3
from botocore.exceptions import ClientError

class SpotInstantiate:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.create_session()

    def create_session(self):
        self.session = boto3.Session(
                        region_name='us-east-2',
                        aws_access_key_id=self.access_key,
                        aws_secret_access_key=self.secret_key,
                    )

    def authenticate(self):
        try:
            self.session.client('sts').get_caller_identity()['Account']
            return True
        except ClientError as e:
            return False

    def _request_spot_fleet(self, fleet_request):
        try:
            spot_fleet_request = self.session.client('ec2').request_spot_fleet(
                DryRun=False,
                SpotFleetRequestConfig={
                    'IamFleetRole': fleet_request['arn'],
                    'LaunchSpecifications': [
                        {
                            'ImageId': 'ami-007a5d65',
                            'InstanceType': fleet_request['instance_type'],
                        },
                    ],
                    'SpotPrice': fleet_request['price'],
                    'TargetCapacity': fleet_request['fleet_size'],
                    # 'ValidFrom': datetime(2015, 1, 1),
                    # 'ValidUntil': datetime(2015, 1, 1),
                    }
                )

        except Exception as e:
            return {'error': e}
        return spot_fleet_request

    def describe_request(self):
        try:
            result = []
            response = self.session.client('ec2').describe_spot_fleet_requests()
            for r in response['SpotFleetRequestConfigs']:
                result.append({
                    'create_time': r['CreateTime'],
                    'fleet_request_id': r['SpotFleetRequestId'],
                    'fleet_request_state': r['SpotFleetRequestState'],
                    'target_capacity': r['SpotFleetRequestConfig']['TargetCapacity'],
                    'spot_price': r['SpotFleetRequestConfig']['SpotPrice'],
                    'active_instances': self.describe_fleet_instance(r['SpotFleetRequestId'])
                })
            result = sorted(result, key=lambda x: x['create_time'], reverse=True)
            return result
        except Exception as e:
            return {'error': e}

    def describe_fleet_instance(self, request_id):
        try:
            response = self.session.client('ec2').describe_spot_fleet_instances(
                                                    SpotFleetRequestId=request_id,
                                                    )
            return response['ActiveInstances']

        except Exception as e:
            return {'error': e}

    def cancel_request(self, request_id):
        try:
            response = self.session.client('ec2').cancel_spot_fleet_requests(
                            SpotFleetRequestIds=[
                            request_id
                            ],
                            TerminateInstances=True
                        )
            return response
        except Exception as e:
            return {'error': e}