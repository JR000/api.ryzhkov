from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Relationship
from collections import defaultdict
from .. import env
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class BookSchema(BaseModel):
    bisac: Optional[str]
    lc: Optional[str]
    publisher: Optional[str]
    year: Optional[int]
    book_id: int = Field(primary_key=True)
    authors: Optional[str]
    title: str
    imprint_publisher: Optional[str]
    isbn: Optional[int]
    esbn: Optional[int]
    oclc: Optional[int]
    lcc: Optional[str]
    # dewey: Optional[str]
    filename: str
    format: str
    pages: Optional[int]
    folder_id: Optional[int]
    read_count: defaultdict[str, int] = Field(
        sa_column=Column(JSON), default_factory=defaultdict[str, int]#nullable=False
    )

class BookTmpSchema(BaseModel):
    bisac: Optional[str]
    lc: Optional[str]
    publisher: Optional[str]
    year: Optional[int]
    book_id: int = Field(primary_key=True)
    authors: Optional[str]
    title: str
    imprint_publisher: Optional[str]
    isbn: Optional[int]
    esbn: Optional[int]
    oclc: Optional[int]
    lcc: Optional[str]
    # dewey: Optional[str]
    filename: str
    format: str
    pages: Optional[int]
    folder_id: Optional[int]
    read_count: defaultdict[str, int] = Field(
        sa_column=Column(JSON), default_factory=defaultdict[str, int]#nullable=False
    )

class FolderSchema(BaseModel):
    id: int = Field(primary_key=True)
    parent_id: Optional[int] = Field(foreign_key="folder.id")
    name: str  
    path: str
    
class UserSchema(BaseModel):
    email: str = Field(primary_key=True)
    is_verified: Optional[bool] = Field(default=False)
    hashed_password: str
    email_token: Optional[str] = Field(default="")
    downloads_left: int = Field(default=10)
    
class Book(SQLModel, BookSchema, table=True):
    __tablename__ = env.DB_TABLE_BOOK

class BookTmp(SQLModel, BookTmpSchema, table=True):
    __tablename__ = "book_tmp"

class Folder(SQLModel, FolderSchema, table=True):
    __tablename__ = "folder"

class User(SQLModel, UserSchema, table=True):
    __tablename__ = "user"

def read_count_key(datetime: datetime):
    return datetime.strftime("%Y-%m")

def parse_read_count_key(key):
    return datetime.strptime(key, "%Y-%m")