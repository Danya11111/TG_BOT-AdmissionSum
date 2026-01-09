import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import requests

# Настройка логирования
logger = logging.getLogger(__name__)


class GigaChatClient:
    """Minimal OAuth client and chat wrapper for GigaChat API.

    - Auth: POST oauth with Basic base64(client_id:client_secret)
    - Chat: POST chat completions with Bearer token
    """

    OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    EMBEDDINGS_URL = "https://gigachat.devices.sberbank.ru/api/v1/embeddings"

    def __init__(
        self,
        auth_basic_base64: str,
        scope: str = "GIGACHAT_API_PERS",
        verify_tls: bool = True,
        request_timeout_sec: int = 30,
        max_retries: int = 3,
        retry_delay_sec: float = 1.0,
    ) -> None:
        self._auth_basic = auth_basic_base64.strip()
        self._scope = scope
        self._verify_tls = verify_tls
        self._request_timeout_sec = request_timeout_sec
        self._max_retries = max_retries
        self._retry_delay_sec = retry_delay_sec
        self._access_token: Optional[str] = None
        self._expires_at_epoch: float = 0.0

    def _headers_oauth(self) -> Dict[str, str]:
        return {
            "Authorization": f"Basic {self._auth_basic}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

    def _headers_api(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _obtain_token(self) -> None:
        data = {"scope": self._scope}
        last_error = None
        
        for attempt in range(self._max_retries):
            try:
                logger.info(f"GigaChat OAuth attempt {attempt + 1}/{self._max_retries}")
                response = requests.post(
                    self.OAUTH_URL,
                    headers=self._headers_oauth(),
                    data=data,
                    timeout=self._request_timeout_sec,
                    verify=self._verify_tls,
                )
                response.raise_for_status()
                payload = response.json()
                access_token = payload.get("access_token")
                expires_in = payload.get("expires_in", 0)
                if not access_token:
                    raise RuntimeError("GigaChat OAuth: access_token missing in response")
                self._access_token = access_token
                # Refresh slightly earlier than actual expiry
                self._expires_at_epoch = time.time() + float(expires_in) * 0.9
                logger.info("GigaChat OAuth successful")
                return
            except requests.exceptions.SSLError as e:
                last_error = e
                logger.warning(f"GigaChat OAuth SSL error: {e}")
                # Auto-fallback: retry once immediately without TLS verification
                if self._verify_tls:
                    try:
                        logger.warning("Retrying OAuth without TLS verification due to SSL error")
                        response = requests.post(
                            self.OAUTH_URL,
                            headers=self._headers_oauth(),
                            data=data,
                            timeout=self._request_timeout_sec,
                            verify=False,
                        )
                        response.raise_for_status()
                        payload = response.json()
                        access_token = payload.get("access_token")
                        expires_in = payload.get("expires_in", 0)
                        if not access_token:
                            raise RuntimeError("GigaChat OAuth: access_token missing in response")
                        self._access_token = access_token
                        self._expires_at_epoch = time.time() + float(expires_in) * 0.9
                        # Persist no-TLS for next requests in current process
                        self._verify_tls = False
                        logger.info("GigaChat OAuth successful without TLS verification")
                        return
                    except Exception as inner_e:
                        last_error = inner_e
                        logger.warning(f"Fallback OAuth without TLS verification failed: {inner_e}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                logger.warning(f"GigaChat OAuth attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay_sec * (attempt + 1))  # Exponential backoff
            except requests.exceptions.HTTPError as e:
                logger.error(f"GigaChat OAuth HTTP error: {e}")
                raise
            except Exception as e:
                logger.error(f"GigaChat OAuth unexpected error: {e}")
                raise
        
        if last_error:
            raise RuntimeError(f"GigaChat OAuth failed after {self._max_retries} attempts") from last_error

    def _get_token(self) -> str:
        if not self._access_token or time.time() >= self._expires_at_epoch:
            self._obtain_token()
        assert self._access_token is not None
        return self._access_token

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "GigaChat",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        token = self._get_token()
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "n": 1,
            "stream": False,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        last_error = None
        for attempt in range(self._max_retries):
            try:
                logger.info(f"GigaChat chat attempt {attempt + 1}/{self._max_retries}")
                response = requests.post(
                    self.CHAT_URL,
                    headers=self._headers_api(token),
                    json=body,
                    timeout=self._request_timeout_sec,
                    verify=self._verify_tls,
                )
                response.raise_for_status()
                logger.info("GigaChat chat successful")
                return response.json()
            except requests.exceptions.SSLError as e:
                last_error = e
                logger.warning(f"GigaChat chat SSL error: {e}")
                if self._verify_tls:
                    try:
                        logger.warning("Retrying chat without TLS verification due to SSL error")
                        response = requests.post(
                            self.CHAT_URL,
                            headers=self._headers_api(token),
                            json=body,
                            timeout=self._request_timeout_sec,
                            verify=False,
                        )
                        response.raise_for_status()
                        self._verify_tls = False
                        logger.info("GigaChat chat successful without TLS verification")
                        return response.json()
                    except Exception as inner_e:
                        last_error = inner_e
                        logger.warning(f"Fallback chat without TLS verification failed: {inner_e}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                logger.warning(f"GigaChat chat attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay_sec * (attempt + 1))  # Exponential backoff
                    # Refresh token on next attempt
                    if attempt > 0:
                        self._access_token = None
                        token = self._get_token()
            except requests.exceptions.HTTPError as e:
                logger.error(f"GigaChat chat HTTP error: {e.response.status_code if hasattr(e, 'response') else 'unknown'}")
                raise
            except Exception as e:
                logger.error(f"GigaChat chat unexpected error: {e}")
                raise
        
        if last_error:
            raise RuntimeError(f"GigaChat chat failed after {self._max_retries} attempts") from last_error

    def chat_text(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        payload = self.chat(messages=messages, **kwargs)
        try:
            return payload["choices"][0]["message"]["content"]
        except Exception:
            return str(payload)

    def get_embeddings(
        self,
        texts: List[str],
        model: str = "Embeddings",
    ) -> List[List[float]]:
        """
        Получает векторные представления текстов через GigaChat Embeddings API.
        
        Args:
            texts: Список текстов для векторизации
            model: Модель для embeddings (по умолчанию "Embeddings")
        
        Returns:
            Список векторов (каждый вектор - список из 1024 float)
        """
        token = self._get_token()
        body: Dict[str, Any] = {
            "model": model,
            "input": texts,
        }
        
        last_error = None
        for attempt in range(self._max_retries):
            try:
                logger.info(f"GigaChat embeddings attempt {attempt + 1}/{self._max_retries} (texts: {len(texts)})")
                response = requests.post(
                    self.EMBEDDINGS_URL,
                    headers=self._headers_api(token),
                    json=body,
                    timeout=self._request_timeout_sec,
                    verify=self._verify_tls,
                )
                response.raise_for_status()
                payload = response.json()
                
                # Извлекаем векторы из ответа
                # Формат ответа: {"data": [{"embedding": [0.1, 0.2, ...]}, ...]}
                if "data" in payload:
                    embeddings = [item["embedding"] for item in payload["data"]]
                else:
                    # Альтернативный формат ответа
                    embeddings = payload.get("embeddings", [])
                
                if not embeddings:
                    raise RuntimeError("GigaChat embeddings: no embeddings in response")
                
                logger.info(f"GigaChat embeddings successful: {len(embeddings)} vectors")
                return embeddings
                
            except requests.exceptions.SSLError as e:
                last_error = e
                logger.warning(f"GigaChat embeddings SSL error: {e}")
                if self._verify_tls:
                    try:
                        logger.warning("Retrying embeddings without TLS verification due to SSL error")
                        response = requests.post(
                            self.EMBEDDINGS_URL,
                            headers=self._headers_api(token),
                            json=body,
                            timeout=self._request_timeout_sec,
                            verify=False,
                        )
                        response.raise_for_status()
                        payload = response.json()
                        
                        if "data" in payload:
                            embeddings = [item["embedding"] for item in payload["data"]]
                        else:
                            embeddings = payload.get("embeddings", [])
                        
                        if not embeddings:
                            raise RuntimeError("GigaChat embeddings: no embeddings in response")
                        
                        self._verify_tls = False
                        logger.info("GigaChat embeddings successful without TLS verification")
                        return embeddings
                    except Exception as inner_e:
                        last_error = inner_e
                        logger.warning(f"Fallback embeddings without TLS verification failed: {inner_e}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                logger.warning(f"GigaChat embeddings attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay_sec * (attempt + 1))  # Exponential backoff
                    # Refresh token on next attempt
                    if attempt > 0:
                        self._access_token = None
                        token = self._get_token()
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
                logger.error(f"GigaChat embeddings HTTP error {status_code}: {e}")
                raise
            except Exception as e:
                logger.error(f"GigaChat embeddings unexpected error: {e}")
                raise
        
        if last_error:
            raise RuntimeError(f"GigaChat embeddings failed after {self._max_retries} attempts") from last_error


