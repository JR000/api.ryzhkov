# Adopted from
# https://stackoverflow.com/a/71309270/11790403

import os
from typing import BinaryIO

from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse

from ftplib import FTP
import string
import random

def send_bytes_range_requests(
    file_obj: BinaryIO, start: int, end: int, chunk_size: int = 10_000
):
    """Send a file in chunks using Range Requests specification RFC7233

    `start` and `end` parameters are inclusive due to specification
    """
    with file_obj as f:
        f.seek(start)
        while (pos := f.tell()) <= end:
            read_size = min(chunk_size, end + 1 - pos)
            yield f.read(read_size)


def _get_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    def _invalid_range():
        return HTTPException(
            status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Invalid request range (Range:{range_header!r})",
        )

    try:
        h = range_header.replace("bytes=", "").split("-")
        start = int(h[0]) if h[0] != "" else 0
        end = int(h[1]) if h[1] != "" else file_size - 1
    except ValueError:
        raise _invalid_range()

    if start > end or start < 0 or end > file_size - 1:
        raise _invalid_range()
    return start, end


def range_requests_response(request: Request, file_path: str, content_type: str):
    """Returns StreamingResponse using Range Requests of a given file"""

    ftp_filename = file_path.split('/')[-1]
    ftp_folder = '/'.join(file_path.split('/')[:-1])

    # print(ftp_folder)
    # print(ftp_filename)
    
    def randomword(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))

    # ftp = FTP(host='test.rebex.net', user="demo", passwd="password", timeout=30) 
    ftp = FTP(host='85.236.190.136', user="admin", passwd="Rkfdbfnehf", timeout=30)
    ftp.set_pasv(False)
    ftp.cwd('/Библиотека/книги/!' + ftp_folder)
    filename = randomword(24)
    # file_path = 'mail-editor.png'
    print(f"'${ftp_filename}'")
    if ftp_filename.startswith(' '):
        ftp_filename = ftp_filename[1:]
    with open(filename, "wb") as file:
        # Command for Downloading the file "RETR filename"
        ftp.retrbinary(f"RETR {ftp_filename}", file.write)


    file_size = os.stat(filename).st_size
    range_header = request.headers.get("range")

    headers = {
        "content-type": content_type,
        "accept-ranges": "bytes",
        "content-encoding": "identity",
        "content-length": str(file_size),
        "access-control-expose-headers": (
            "content-type, accept-ranges, content-length, "
            "content-range, content-encoding"
        ),
    }
    start = 0
    end = file_size - 1
    status_code = status.HTTP_200_OK

    if range_header is not None:
        start, end = _get_range_header(range_header, file_size)
        size = end - start + 1
        headers["content-length"] = str(size)
        headers["content-range"] = f"bytes {start}-{end}/{file_size}"
        status_code = status.HTTP_206_PARTIAL_CONTENT

    return StreamingResponse(
        send_bytes_range_requests(open(filename, mode="rb"), start, end),
        headers=headers,
        status_code=status_code,
    )
