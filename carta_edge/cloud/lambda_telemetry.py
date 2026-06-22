import json
import boto3
import os
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TELEMETRY_TABLE', 'CartaTelemetry')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    AWS Lambda handler triggered by AWS IoT Core rule on 'carta/telemetry/+'
    """
    print(f"📥 Received IoT Telemetry Event: {json.dumps(event)}")
    
    # Extract data from the incoming payload
    cart_id = event.get('cart_id', 'unknown_cart')
    battery = event.get('battery_percentage', 0)
    latitude = event.get('latitude', 0.0)
    longitude = event.get('longitude', 0.0)
    timestamp = event.get('timestamp', datetime.utcnow().isoformat())
    
    # Validate payload
    try:
        # 1. Save data into AWS DynamoDB for historical tracking
        response = table.put_item(
            Item={
                'cart_id': cart_id,
                'timestamp': timestamp,
                'battery_percentage': int(battery),
                'latitude': str(latitude),
                'longitude': str(longitude),
                'received_at': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Telemetry successfully archived in DynamoDB table '{table_name}'.")
        
        # 2. Check battery health status (Low battery trigger)
        if battery < 20:
            print(f"⚠️ ALERT: Low battery on {cart_id}! Current charge: {battery}%.")
            # In a production cloud app, you can trigger Amazon SNS here:
            # sns = boto3.client('sns')
            # sns.publish(TopicArn='arn:aws:sns:eu-central-1:123456789012:CartaAlerts', Message=...)
            
    except Exception as e:
        print(f"❌ Error archiving telemetry: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to process telemetry: {str(e)}")
        }
        
    return {
        'statusCode': 200,
        'body': json.dumps("Telemetry processed successfully.")
    }
