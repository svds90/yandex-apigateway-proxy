import requests

from time import sleep
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse

OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /{path+}:
    get:
      x-yc-apigateway-integration:
        type: http
        url: %s/{path}
        headers:
          Accept: '*/*'
          Accept-Encoding: "gzip, deflate"
          Host: %s
          Connection: 'keep-alive'
      parameters:
      - name: path
        in: path
        required: false
        schema:
          type: string
"""


class YandexApiGateway(HTTPAdapter):
    def __init__(self, iam_token: str, folder_id: str, base_url: str, **kwargs) -> None:
        super().__init__(**kwargs)

        self.service_url = (
            "https://serverless-apigateway.api.cloud.yandex.net/apigateways/v1/apigateways"
        )
        self.iam_token = iam_token
        self.folder_id = folder_id
        self.base_url = self.set_base_url(base_url)
        self.host = urlparse(self.base_url).netloc
        self.gateway_name = self.host.replace(".", "-") + "-proxy"
        self.gateway_id = None
        self.gateway_url = None
        self.gateway_is_active = False

    def __enter__(self):
        self.init_gateway()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del exc_type, exc_value, traceback
        self.shutdown_gateway()

    @staticmethod
    def set_base_url(base_url: str) -> str:
        return base_url.rstrip("/") if "://" in base_url else f"https://{base_url.rstrip('/')}"

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        parsed_url = urlparse(request.url)
        new_url = str(self.gateway_url) + str(parsed_url.path)

        new_request = requests.Request(
            method=request.method, url=new_url, headers=request.headers, data=request.body
        ).prepare()

        return super().send(new_request, stream, timeout, verify, cert, proxies)

    def request(self, method: str, url: str, **kwargs) -> dict:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.iam_token}"
        response = requests.request(method=method, url=url, headers=headers, **kwargs)

        if response.status_code >= 400:
            return {}

        return response.json()

    def get_api_gateways(self, api_gateway_id=None) -> dict:
        if api_gateway_id:
            url = f"{self.service_url}/{api_gateway_id}"
            return self.request(method="GET", url=url)

        url = f"{self.service_url}?folderId={self.folder_id}"
        return self.request(method="GET", url=url).get("apiGateways", {})

    def init_gateway(self) -> dict:
        gateway_list = self.get_api_gateways()

        for gateway in gateway_list:
            if gateway["name"] == self.gateway_name:
                self.gateway_id = gateway["id"]
                self.gateway_url = f"https://{gateway["domain"]}"
                return gateway

        payload = {
            "folderId": self.folder_id,
            "name": self.gateway_name,
            "openapiSpec": OPENAPI_SPEC % (self.base_url, self.host),
        }

        response = self.request(method="POST", url=self.service_url, json=payload)
        self.gateway_id = response.get("metadata", {}).get("apiGatewayId")

        while True:
            sleep(0.5)
            response = self.get_api_gateways(self.gateway_id)
            if response.get("status") == "ACTIVE":
                self.gateway_is_active = True
                self.gateway_url = f"https://{response['domain']}"
                break

        return response

    def shutdown_gateway(self) -> dict:
        if not self.gateway_id:
            return {}

        url = f"{self.service_url}/{self.gateway_id}"
        return self.request(method="DELETE", url=url)
