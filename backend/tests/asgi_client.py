import asyncio
import json
from urllib.parse import urlparse


class ASGIResponse:
    def __init__(self, status_code, headers, body):
        self.status_code = status_code
        self.headers = {
            k.decode("latin1").lower(): v.decode("latin1") for k, v in headers
        }
        self.content = body
        self.text = body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)


class ASGITestClient:
    def __init__(self, app):
        self.app = app

    def request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        json: dict = None,
        data: dict = None,
        files: dict = None,
    ) -> ASGIResponse:
        return asyncio.run(
            self._async_request(
                method=method,
                path=path,
                headers=headers,
                json_data=json,
                data=data,
                files=files,
            )
        )

    def get(self, path: str, headers: dict = None) -> ASGIResponse:
        return self.request("GET", path, headers=headers)

    def post(
        self,
        path: str,
        headers: dict = None,
        json: dict = None,
        data: dict = None,
        files: dict = None,
    ) -> ASGIResponse:
        return self.request(
            "POST", path, headers=headers, json=json, data=data, files=files
        )

    async def _async_request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        json_data: dict = None,
        data: dict = None,
        files: dict = None,
    ) -> ASGIResponse:
        headers_dict = dict(headers or {})
        parsed_url = urlparse(path)
        raw_path = parsed_url.path.encode("utf-8")
        query_string = parsed_url.query.encode("utf-8")

        body_bytes = b""

        if json_data is not None:
            body_bytes = json.dumps(json_data).encode("utf-8")
            headers_dict["content-type"] = "application/json"
        elif files is not None:
            body_bytes, content_type = self._encode_multipart(data, files)
            headers_dict["content-type"] = content_type
        elif data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        headers_dict["content-length"] = str(len(body_bytes))

        raw_headers = [
            (k.lower().encode("latin1"), v.encode("latin1"))
            for k, v in headers_dict.items()
        ]

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": parsed_url.path,
            "raw_path": raw_path,
            "query_string": query_string,
            "headers": raw_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("127.0.0.1", 8000),
        }

        response_status = None
        response_headers = []
        response_body = bytearray()

        body_sent = False

        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": False,
                }
            await asyncio.sleep(100)
            return {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }

        async def send(message):
            nonlocal response_status, response_headers, response_body
            msg_type = message["type"]

            if msg_type == "http.response.start":
                response_status = message["status"]
                response_headers = message.get("headers", [])
            elif msg_type == "http.response.body":
                response_body.extend(message.get("body", b""))

        await self.app(scope, receive, send)

        return ASGIResponse(response_status, response_headers, bytes(response_body))

    def _encode_multipart(self, data, files):
        boundary = "----WebKitFormBoundaryVisionInspectTestClient"
        body = bytearray()

        if data:
            for key, val in data.items():
                body.extend(f"--{boundary}\r\n".encode())
                body.extend(
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                )
                body.extend(str(val).encode())
                body.extend(b"\r\n")

        if files:
            for field_name, file_info in files.items():
                if isinstance(file_info, tuple):
                    if len(file_info) == 3:
                        filename, file_content, content_type = file_info
                    elif len(file_info) == 2:
                        filename, file_content = file_info
                        content_type = "application/octet-stream"
                else:
                    filename = "uploaded_file"
                    file_content = file_info
                    content_type = "application/octet-stream"

                body.extend(f"--{boundary}\r\n".encode())
                body.extend(
                    f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
                )
                body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())

                if hasattr(file_content, "read"):
                    body.extend(file_content.read())
                elif isinstance(file_content, (bytes, bytearray)):
                    body.extend(file_content)
                elif isinstance(file_content, str):
                    body.extend(file_content.encode("utf-8"))

                body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode())
        return bytes(body), f"multipart/form-data; boundary={boundary}"
