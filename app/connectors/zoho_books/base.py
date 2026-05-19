"""
Zoho Books connector base and dynamic operation executor.
"""

from __future__ import annotations

import base64
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlparse

from app.database import CredentialManager
from app.errors import CredentialMissingError, NetworkError, ValidationError
from app.http_client import http_client
from app.logging_config import get_logger
from app.posthog_client import track_token_refreshed

logger = get_logger(__name__)


class ZohoBooksConnector:
    """Dynamic Zoho Books connector backed by OpenAPI operation metadata."""

    DEFAULT_ACCOUNTS_SERVER = "https://accounts.zoho.com"
    DEFAULT_API_DOMAIN = "https://www.zohoapis.com"

    def __init__(self) -> None:
        self.client_id = os.getenv("ZOHO_BOOKS_CLIENT_ID", "")
        self.client_secret = os.getenv("ZOHO_BOOKS_CLIENT_SECRET", "")
        self.accounts_server = os.getenv(
            "ZOHO_BOOKS_ACCOUNTS_SERVER", self.DEFAULT_ACCOUNTS_SERVER
        ).rstrip("/")
        self.api_version = os.getenv("ZOHO_BOOKS_API_VERSION", "v3").strip() or "v3"

    def _token_url(self, accounts_server: str | None = None) -> str:
        return f"{(accounts_server or self.accounts_server).rstrip('/')}/oauth/v2/token"

    def _normalize_api_domain(self, api_domain: str | None) -> str:
        domain = (
            api_domain or os.getenv("ZOHO_BOOKS_API_DOMAIN") or self.DEFAULT_API_DOMAIN
        ).strip()
        if not domain:
            domain = self.DEFAULT_API_DOMAIN
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"
        return domain.rstrip("/")

    def _derive_accounts_server_from_api_domain(self, api_domain: str | None) -> str:
        if not api_domain:
            return self.accounts_server
        parsed = urlparse(api_domain)
        host = parsed.netloc or parsed.path
        host = host.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        if not host.startswith("zohoapis."):
            return self.accounts_server
        suffix = host[len("zohoapis.") :]
        if not suffix:
            return self.accounts_server
        return f"https://accounts.zoho.{suffix}"

    def _get_access_token(self, org_id: str, user_id: str) -> dict[str, Any]:
        cred = CredentialManager.get_credential(org_id, user_id, "zoho_books")
        if not cred:
            raise CredentialMissingError("zoho_books", org_id, user_id)

        token_expiry = cred.get("token_expiry")
        if token_expiry and token_expiry < datetime.now(UTC) + timedelta(minutes=5):
            logger.info(
                "Zoho Books token expired or expiring soon, refreshing",
                service="zoho_books",
                org_id=org_id,
                user_id=user_id,
                log_event="token_refresh_needed",
            )
            return self._refresh_token(org_id, user_id, cred)
        return cred

    def _refresh_token(self, org_id: str, user_id: str, cred: dict[str, Any]) -> dict[str, Any]:
        refresh_token = cred.get("refresh_token")
        if not refresh_token:
            raise ValidationError(
                "refresh_token", "No refresh token stored for Zoho Books credential"
            )
        if not self.client_id or not self.client_secret:
            raise ValidationError(
                "credentials",
                "ZOHO_BOOKS_CLIENT_ID and ZOHO_BOOKS_CLIENT_SECRET environment variables required",
            )

        extra_data = cred.get("extra_data") or {}
        accounts_server = extra_data.get(
            "accounts_server"
        ) or self._derive_accounts_server_from_api_domain(extra_data.get("api_domain"))

        logger.info(
            "Refreshing Zoho Books token",
            service="zoho_books",
            org_id=org_id,
            user_id=user_id,
            accounts_server=accounts_server,
            log_event="token_refresh_start",
        )

        for attempt in range(2):
            try:
                token_data = http_client.post(
                    url=self._token_url(str(accounts_server)),
                    service="zoho_books",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )

                new_expiry = datetime.now(UTC) + timedelta(
                    seconds=int(token_data.get("expires_in", 3600))
                )
                api_domain = self._normalize_api_domain(
                    token_data.get("api_domain") or extra_data.get("api_domain")
                )
                merged_extra = dict(extra_data)
                merged_extra["api_domain"] = api_domain
                merged_extra["accounts_server"] = self._derive_accounts_server_from_api_domain(
                    api_domain
                )
                if cred.get("realm_id"):
                    merged_extra.setdefault("organization_id", cred["realm_id"])

                CredentialManager.store_credential(
                    org_id=org_id,
                    user_id=user_id,
                    service="zoho_books",
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", refresh_token),
                    token_expiry=new_expiry,
                    realm_id=cred.get("realm_id"),
                    extra_data=merged_extra,
                )

                track_token_refreshed(
                    user_id=user_id,
                    org_id=org_id,
                    service="zoho_books",
                    success=True,
                )

                logger.info(
                    "Zoho Books token refresh successful",
                    service="zoho_books",
                    org_id=org_id,
                    user_id=user_id,
                    log_event="token_refresh_success",
                )

                return {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token", refresh_token),
                    "token_expiry": new_expiry,
                    "realm_id": cred.get("realm_id"),
                    "extra_data": merged_extra,
                }
            except NetworkError:
                if attempt == 0:
                    logger.warning(
                        "Zoho Books token refresh transient failure, retrying",
                        service="zoho_books",
                        log_event="token_refresh_retry",
                    )
                    time.sleep(1.0)
                    continue
                track_token_refreshed(
                    user_id=user_id,
                    org_id=org_id,
                    service="zoho_books",
                    success=False,
                )
                raise
            except Exception:
                track_token_refreshed(
                    user_id=user_id,
                    org_id=org_id,
                    service="zoho_books",
                    success=False,
                )
                raise

        raise NetworkError(service="zoho_books")

    @staticmethod
    def _coerce_string_dict(value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(k): str(v) for k, v in value.items()}

    @staticmethod
    def _extract_path_params(operation: dict[str, Any], args: dict[str, Any]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        explicit = args.get("path_params", {})
        for name in operation.get("path_params", []):
            value: Any = None
            if name in args:
                value = args[name]
            elif isinstance(explicit, dict) and name in explicit:
                value = explicit[name]
            if value is None:
                raise ValidationError("path_params", f"Missing required path parameter '{name}'")
            resolved[name] = str(value)
        return resolved

    @staticmethod
    def _extract_query_params(operation: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        query: dict[str, Any] = {}
        explicit = args.get("query_params", {})
        if isinstance(explicit, dict):
            query.update(explicit)

        for name in operation.get("query_params", []):
            if name in args:
                query[name] = args[name]
        return query

    @staticmethod
    def _extract_body(
        operation: dict[str, Any],
        args: dict[str, Any],
        path_params: dict[str, str],
        query_params: dict[str, Any],
    ) -> Any:
        if "body" in args:
            return args["body"]

        if not operation.get("has_request_body"):
            return None

        reserved = {
            "path_params",
            "query_params",
            "headers",
            "organization_id",
            "parse_json",
            "files",
            "form_data",
            "body",
        }
        excluded = reserved | set(path_params.keys()) | set(query_params.keys())
        inferred_body = {k: v for k, v in args.items() if k not in excluded}
        if inferred_body:
            return inferred_body

        if operation.get("request_body_required"):
            raise ValidationError("body", "Request body is required for this Zoho Books operation")
        return None

    def _build_operation_url(
        self,
        operation_path: str,
        path_params: dict[str, str],
        cred: dict[str, Any],
        args: dict[str, Any],
    ) -> str:
        path = operation_path
        for name, value in path_params.items():
            path = path.replace(f"{{{name}}}", quote(value, safe=""))

        extra_data = cred.get("extra_data") or {}
        api_domain = self._normalize_api_domain(
            args.get("api_domain")
            or extra_data.get("api_domain")
            or os.getenv("ZOHO_BOOKS_API_DOMAIN")
        )
        return f"{api_domain}/books/{self.api_version}{path}"

    @staticmethod
    def _format_binary_response(response: Any) -> dict[str, Any]:
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
            "content_base64": base64.b64encode(response.content).decode("ascii"),
            "headers": {
                "content-disposition": response.headers.get("Content-Disposition"),
                "content-length": response.headers.get("Content-Length"),
            },
        }

    def execute_operation(
        self, org_id: str, user_id: str, operation: dict[str, Any], args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a Zoho Books operation described by an OpenAPI manifest entry."""
        args = args or {}
        cred = self._get_access_token(org_id, user_id)

        path_params = self._extract_path_params(operation, args)
        query_params = self._extract_query_params(operation, args)

        # Zoho Books requires organization_id on almost all endpoints.
        organization_id = (
            args.get("organization_id")
            or query_params.get("organization_id")
            or cred.get("realm_id")
            or (cred.get("extra_data") or {}).get("organization_id")
        )
        requires_org_query = not str(operation.get("path", "")).startswith("/organizations")
        if requires_org_query and not organization_id:
            raise ValidationError(
                "organization_id",
                "Zoho Books organization_id is required for this endpoint. "
                "Reconnect OAuth or pass organization_id in args/query_params.",
            )
        if organization_id:
            query_params.setdefault("organization_id", str(organization_id))

        url = self._build_operation_url(
            operation_path=str(operation["path"]),
            path_params=path_params,
            cred=cred,
            args=args,
        )

        headers: dict[str, str] = {
            "Authorization": f"Zoho-oauthtoken {cred['access_token']}",
            "Accept": "application/json",
        }
        headers.update(self._coerce_string_dict(args.get("headers")))

        method = str(operation["method"]).upper()
        body = self._extract_body(operation, args, path_params, query_params)
        files = args.get("files")
        form_data = args.get("form_data")

        parse_json = bool(args.get("parse_json", not operation.get("returns_binary", False)))

        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            "service": "zoho_books",
            "headers": headers,
            "params": query_params or None,
        }

        if files is not None:
            # Multipart/form-data requests should not force JSON content type.
            request_kwargs["files"] = files
            request_kwargs["data"] = form_data or body or {}
            request_kwargs["parse_json"] = parse_json
            response = http_client.request(**request_kwargs)
            if isinstance(response, dict):
                return response
            return self._format_binary_response(response)

        if form_data is not None:
            request_kwargs["data"] = form_data
            request_kwargs["parse_json"] = parse_json
            response = http_client.request(**request_kwargs)
            if isinstance(response, dict):
                return response
            return self._format_binary_response(response)

        if body is not None:
            request_kwargs["headers"] = {
                **headers,
                "Content-Type": "application/json",
            }
            request_kwargs["json"] = body

        request_kwargs["parse_json"] = parse_json
        response = http_client.request(**request_kwargs)
        return response if isinstance(response, dict) else self._format_binary_response(response)
