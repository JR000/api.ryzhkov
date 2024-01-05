from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select, text, update
from ..internal.range_request import range_requests_response
from ..internal.models import Book, read_count_key, Folder, User
from ..internal.db import engine
from .. import env
from ..internal.check import MaybeRedirect, get_current_user
import re

from urllib.parse import unquote

router = APIRouter()


# user = Depends(get_current_user)

@router.get("/folder/")
async def root_folder_url():
    with Session(engine) as session:
        folder = session.exec(text(f'''SELECT * FROM folder 
                                 WHERE folder.path == "/"
                           
                                 ''')).mappings().all()[0]
        subfolders = session.exec(text(f'''SELECT path FROM folder WHERE folder.parent_id == {folder.id}
                                       ''')).mappings().all()
        
        books = session.exec(text(f"SELECT * FROM book WHERE book.folder_id == {folder.id}")).mappings().all()
        print(subfolders, books)
        f = {**folder}
        f["books"] = books        
        f["subfolders"] = subfolders
        if not folder:
            raise HTTPException(status_code=404, detail="Book not found")
        return f
    
@router.get("/folder/{path:path}")
async def folder_url(path: str):

    path = unquote(path)
    with Session(engine) as session:
     
        folder = session.exec(text(f'''SELECT * FROM folder 
                                 WHERE folder.path == "/{path}/"
                           
                                 ''')).mappings().all()
        print(folder)
        if not len(folder):
            raise HTTPException(status_code=404, detail="Book not found")
        folder = folder[0]
        subfolders = session.exec(text(f'''SELECT path FROM folder WHERE folder.parent_id == {folder.id}
                                    ''')).mappings().all()
        books = session.exec(text(f"SELECT * FROM book WHERE book.folder_id == {folder.id}")).mappings().all()
        print(subfolders, books)
        f = {**folder}
        f["books"] = books        
        f["subfolders"] = subfolders
        return f

@router.get("/book/{book_id}")
async def book_page(book_id: int):

    with Session(engine) as session:
        book = session.get(Book, book_id)
        folder = session.get(Folder, book.folder_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        book = {**book.__dict__}
        book["folder"] = folder.path
        return book

@router.get("/book/{book_id}/file")
async def file_post(book_id: int, request: Request, user: User = Depends(get_current_user)):

    if (user.downloads_left <= 0):
        raise HTTPException(status_code=401, detail="No downloads left")



    with Session(engine) as session:
        user.downloads_left -= 1
        session.add(user)
        session.commit()
        session.exec(update(User).where(User.email == user.email).values(downloads_left=user.downloads_left - 1))
    if (
        (range := request.headers.get("range"))
        and (start := re.search("bytes=(\d+)-\d+", range))
        and int(start.group(1)) == 0
    ):
        with Session(engine) as session:
            book: Book = session.exec(select(Book).where(Book.book_id == book_id)).one()
            time = datetime.utcnow() + timedelta(hours=env.UTC_OFFSET)
            book.read_count = defaultdict(int, book.read_count)
            book.read_count[read_count_key(time)] += 1



            session.add(book)

            session.commit()
    with Session(engine) as session:
        book: Book = session.exec(select(Book).where(Book.book_id == book_id)).one()
        folder: Folder = session.exec(select(Folder).where(Folder.id == book.folder_id)).one()
        return range_requests_response(
            request=request,
            file_path=f"{folder.path}{book.filename}",
            content_type="application/pdf" if book.format == 'pdf' else 'application/djvu',
        )
