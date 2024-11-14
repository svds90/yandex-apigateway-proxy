import requests
from requests.adapters import HTTPAdapter, Retry, PoolManager
from fake_useragent import UserAgent
from pprint import pprint
from typing import Union, Optional


TIMEOUT_CONNECT = 5
TIMEOUT_READ = 10
TOTAL_RETRIES = 5
CONNECT_RETRIES = 3
READ_RETRIES = 2
BACKOFF_FACTOR = 0.5
STATUS_FORCELIST = [500, 502, 503, 504]
PROXIES = None


class CustomHTTPAdapter(HTTPAdapter):
    def __init__(
            self,
            total_retries: Union[int, None, bool] = TOTAL_RETRIES,
            connect_retries: int = CONNECT_RETRIES,
            read_retries: int = READ_RETRIES,
            backoff_factor: float = BACKOFF_FACTOR,
            status_forcelist: Optional[list[int]] = STATUS_FORCELIST,
            proxies: Optional[dict[str, str]] = PROXIES
    ):

        self.retry = Retry(
            total=total_retries,
            connect=connect_retries,
            read=read_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist
        )
        self.proxies = proxies
        self.poolmanager = PoolManager()
        self.max_retries = self.retry


adapter = CustomHTTPAdapter()
session = requests.Session()
session.mount('https://', adapter)
session.mount('http://', adapter)

r = session.get('https://httpbin.org/headers')
print(r.text)


class YandexApiGatewayManager:
    def __init__(self) -> None:
        pass


class YandexApiGateway:
    def __init__(self, base_url, authorization=None, authorization_type=None) -> None:
        pass
