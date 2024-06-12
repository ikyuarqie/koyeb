# from flask import Flask
# app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello from Koyeb'


# if __name__ == "__main__":
#     app.run()

from flask import Flask, request, jsonify
import xmltodict
import requests
from requests.auth import HTTPBasicAuth
import base64

app = Flask(__name__)

# Function to convert JSON to XML (SOAP 1.2)
def json_to_soap(json_data):
    envelope = {
        "soap12:Envelope": {
            "@xmlns:soap12": "http://www.w3.org/2003/05/soap-envelope",
            "@xmlns:urn": "urn:sap-com:document:sap:rfc:functions",
            "soap12:Header": {},
            "soap12:Body": json_data
        }
    }
    xml_data = xmltodict.unparse(envelope, pretty=True)
    # Remove the XML declaration if present
    if xml_data.startswith('<?xml'):
        xml_data = xml_data.split('?>', 1)[1].strip()
    return xml_data

# Function to convert XML (SOAP) to JSON
def soap_to_json(xml_data):
    return xmltodict.parse(xml_data)

# Function to decode the basic auth credentials from the request header
def decode_auth(auth_header):
    auth_type, auth_string = auth_header.split(' ')
    if auth_type.lower() == 'basic':
        username, password = base64.b64decode(auth_string).decode('utf-8').split(':')
        return username, password
    else:
        return None, None

@app.route('/convert', methods=['POST'])
def convert():
    try:
        json_data = request.json

        # Extract WSDL URL from custom header
        soap_endpoint = request.headers.get('wsdl')
        if not soap_endpoint:
            return jsonify({'error': 'SOAP-Endpoint header is required'}), 400

        # Extract basic auth credentials from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is required'}), 400

        username, password = decode_auth(auth_header)
        if not username or not password:
            return jsonify({'error': 'Invalid Authorization header'}), 400

        soap_request = json_to_soap(json_data)

        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': ''  # Optional, depends on your SOAP service
        }

        response = requests.post(
            soap_endpoint,
            data=soap_request,
            headers=headers,
            auth=HTTPBasicAuth(username, password)
        )

        if response.status_code == 200:
            json_response = soap_to_json(response.text)
            return jsonify(json_response)
        else:
            return jsonify({'error': f'SOAP request failed with status code {response.status_code}'}), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
