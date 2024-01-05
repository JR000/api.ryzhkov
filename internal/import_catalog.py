# https://stackoverflow.com/a/67930222

from contextlib import closing
import sqlite3
import pandas as pd
from pathlib import Path

from sqlmodel import Session, text

from .models import Book, BookTmp, Folder
from .db import create_db_and_tables, engine
from .. import env
from pypdf import PdfReader

from uuid import uuid4


def record_pages(df_xlsx, books_dir):
    def count_pages(row):
        book_id = row["book_id"]
        book_path = f"{books_dir}/{book_id}.pdf"
        reader = PdfReader(book_path)
        number_of_pages = len(reader.pages)
        return number_of_pages

    df_xlsx["pages"] = df_xlsx.apply(count_pages, axis=1)


def import_catalog(
    xlsx=env.XLSX_PATH,
    sheet_name=env.SHEET,
    sql_dump_path=env.DB_DUMP_PATH,
    db_path=env.DB_PATH,
):
    Path(db_path).parent.mkdir(exist_ok=True, parents=True)

    df_xlsx = pd.read_excel(xlsx, sheet_name)
    categories_paths = sorted(list(set(df_xlsx['path'].to_list())), key=lambda x: (x.count('/'), len(x))) 
    
    processed_folders = []
    
    book_tmp = BookTmp.__tablename__

    with Session(engine) as session:
        session.exec(text("delete from folder;"))
        
        for folder_path in categories_paths:
            parent_id = None
            
            for folder in reversed(processed_folders):
                if folder_path.startswith(folder[0]):
                    parent_id = folder[1]

                    break
            
        
            folder_name = folder_path.split('/')[-1]
            id = uuid4().int & 0xfff
            processed_folders.append((folder_path, id))
            session.add(Folder(id=id, parent_id=parent_id, name=folder_name, path=folder_path))
        session.commit()
        
        session.exec(text("delete from book_tmp;"))
        for row_dict in df_xlsx.to_dict(orient="records"):
            
            folder_id = session.exec(
                text(f'select id from folder where path == "{row_dict["path"]}"')
            ).mappings().all()[0].id
            
            total_dict = {**row_dict}
            total_dict["folder_id"] = folder_id
            b = BookTmp(**total_dict)
            print(b)
            session.add(b)
        session.commit()

    book = Book.__tablename__
    book_id = "book_id"

    session.exec(
        text(f"delete from {book} where {book}.{book_id} not in (select {book_id} from {book_tmp});")
    )
    session.exec(
        text(f"insert into {book} select {book_tmp}.* from {book_tmp} where {book_tmp}.{book_id} not in (select {book_id} from {book})")
    )
    print(session.exec(text(f"select * from {book}")).mappings().all())
    session.exec(text(f"delete from {book_tmp}"))
    session.commit()


    with closing(sqlite3.connect(db_path)) as conn:
        # save book data from that database into a sql file
        with open(sql_dump_path, "w", encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")


def import_catalog_csv(
    xlsx='../parsed.csv',
    sql_dump_path=env.DB_DUMP_PATH,
    db_path=env.DB_PATH,
):
    
    
    # with open('../parsed.csv') as file:
    #     lines = file.readlines()
    #     c = lines[0].count('ख')
    #     for i in range(1, len(lines)):
    #         line = lines[i]
    #         if line.count('ख') != c:
    #             print(line)
    #             input()
    Path(db_path).parent.mkdir(exist_ok=True, parents=True)

    # df_xlsx = pd.read_csv(xlsx, sep='ख', encoding='utf-16', )
    
    data_from_csv = []
    with open('C:\\Users\\Ivan Ryzhkov\\Documents\\bollocks\\elibrary/parsed.csv', encoding='utf-16') as csv:
        data_from_csv = [x.split('ख') for x in csv.read().splitlines()]
    
    # # for x, i in enumerate(df_xlsx['dewey'].to_list()):
    # #     try:
    # #         float(i)
    # #     except:
    # #         print(x)
    # #         input()
            
    # print(len(data_from_csv))
    
    categories_paths = []
    
    for line in data_from_csv:
        categories_paths.append(line[-2])
    categories_paths = sorted(list(set(categories_paths)), key=lambda x: (x.count('/'), len(x))) 
    print(len(categories_paths))
    input()
    
    processed_folders = []
    
    book_tmp = BookTmp.__tablename__

    with Session(engine) as session:
        session.exec(text("delete from folder;"))
        
        for folder_path in categories_paths:
            parent_id = None
            
            for folder in reversed(processed_folders):
                if folder_path.startswith(folder[0]):
                    parent_id = folder[1]

                    break
            
        
            folder_name = folder_path.split('/')[-1]
            id = uuid4().int & 0xffffffffff
            processed_folders.append((folder_path, id))
            session.add(Folder(id=id, parent_id=parent_id, name=folder_name, path=folder_path))
        session.commit()
        
        session.exec(text("delete from book_tmp;"))
        for i, row_dict in enumerate(data_from_csv):
            
            if i == 0:
                continue
            
            folder_id = session.exec(
                text(f'select id from folder where path == "{row_dict[-2]}"')
            ).mappings().all()[0].id
            
            
            title = row_dict[6]
            if title.endswith('.pd'):
                title = title.replace('.pd', '')
            if title.endswith('.djv'):
                title = title.replace('.djv', '')
            if title.endswith('.djvu'):
                title = title.replace('.djvu', '')
            if title.endswith('.pdf'):
                title = title.replace('.pdf', '')
            
            total_dict = {
                'filename': row_dict[-1],
                'folder_id': folder_id,
                'title': title,
                'id': row_dict[4],
                'format': row_dict[-4]
            }
            b = BookTmp(**total_dict)
            print(b)
            # input()
            session.add(b)
        session.commit()

    book = Book.__tablename__
    book_id = "book_id"

    session.exec(
        text(f"delete from {book} where {book}.{book_id} not in (select {book_id} from {book_tmp});")
    )
    session.exec(
        text(f"insert into {book} select {book_tmp}.* from {book_tmp} where {book_tmp}.{book_id} not in (select {book_id} from {book})")
    )
    session.exec(text(f"select * from {book}")).mappings().all()
    session.exec(text(f"delete from {book_tmp}"))
    session.commit()


    with closing(sqlite3.connect(db_path)) as conn:
        # save book data from that database into a sql file
        with open(sql_dump_path, "w", encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")


def run():
    create_db_and_tables()
    import_catalog()
