import json
import boto3
import os

# Initialize AWS IoT Data Plane client
# Note: In production, specify your AWS IoT endpoint or let boto3 resolve it.
iot_client = boto3.client('iot-data', region_name='eu-central-1')

def lambda_handler(event, context):
    """
    AWS Lambda handler designed to receive command requests from API Gateway, 
    validates the action, and publishes it via MQTT to the physical cart.
    """
    print(f"📥 Received Command Event: {json.dumps(event)}")
    
    # 1. Parse body (handles standard HTTP POST calls)
    body = event.get('body', {})
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass
            
    cart_id = body.get('cart_id', 'cart_001')
    command = body.get('command')
    
    if not command:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing required parameter: command'})
        }
        
    allowed_commands = ["unlock_doors", "emergency_stop"]
    if command not in allowed_commands:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f"Invalid command: '{command}'. Allowed values: {allowed_commands}"})
        }
        
    # Define topic and payload
    topic = f"carta/commands/{cart_id}"
    payload = {
        "command": command,
        "timestamp": int(os.environ.get('TIME_FACTOR', 1))
    }
    
    try:
        # Publish to AWS IoT Core MQTT
        response = iot_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(payload)
        )
        print(f"✅ Published command '{command}' successfully to AWS IoT Topic: {topic}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*', # CORS Enabled
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'message': f"Command '{command}' sent successfully to cart {cart_id}!"})
        }
        
    except Exception as e:
        print(f"❌ Failed to publish command to IoT Core: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f"Failed to send command to IoT: {str(e)}"})
        }
