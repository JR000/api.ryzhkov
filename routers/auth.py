import { useEffect, useRef, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import store from "../store";
import { Link, redirect } from "react-router-dom";
import axios from "axios";
import userEvent from "@testing-library/user-event";


const Book = () => {
    let { id } = useParams();
    // console.log(params)
    const [isLoading, setIsLoading] = useState(true)
    const book = useRef({})
    async function onOpen() {

        // await store.getUser()
        book.current = await store.fetchBookInfo(id)
        if (store.sourceNotFound)
            return

        setIsLoading(false)
    }


    const [pdfSource, setPdfSource] = useState('');

    // const handleRequestPdf = async () => {
    //     // try {
    //         // const response = await axios.get(`http://localhost:5001/api/book/${book.current.book_id}/file`, {
    //         //     responseType: 'blob', // Указываем, что ожидаем получить данные в виде Blob,
    //         //     headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    //         // });

    //         // Создаем URL объект для полученного Blob, чтобы его можно было использовать в iframe
    //         // const pdfUrl = URL.createObjectURL(new Blob([response.blob()]));

    //         // setPdfSource(pdfUrl);
    //         // store.user.downloads_left -= 1
    //     // } catch (error) {
    //     //     alert('Ошибка')
    //     //     console.error('Ошибка при выполнении запроса:', error);
    //     // }

    //     fetch(`http://localhost:5001/api/book/${book.current.book_id}/file`, {
    //         method: 'GET',
    //         headers: {
    //             Authorization: `Bearer ${localStorage.getItem('token')}`
    //         },
    //     })
    //         .then((response) => response.blob())
    //         .then((blob) => {
    //             const url = window.URL.createObjectURL(
    //                 new Blob([blob]),
    //             );
    //             setPdfSource(url)
    //             store.user.downloads_left -= 1
    //         })
    // };

    async function handleRequestPdf() {
        downloadFile(`http://localhost:5001/api/book/${book.current.book_id}/file`, book.current.title + '.pdf')
    }

    async function handleRequestDjvu() {
        downloadFile(`http://localhost:5001/api/book/${book.current.book_id}/file`, book.current.title + '.djvu')
    }

    async function downloadFile(fileUrl, outputLocationPath) {
        fetch(fileUrl, {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('token')}`
            },
        })
            .then((response) => response.blob())
            .then((blob) => {
                // Create blob link to download
                const url = window.URL.createObjectURL(
                    new Blob([blob]),
                );
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute(
                    'download',
                    outputLocationPath,
                );

                // Append to html link element page
                document.body.appendChild(link);

                // Start download
                link.click();

                // Clean up and remove the link
                link.parentNode.removeChild(link);
                store.user.downloads_left -= 1
            });
    }


    function renderButtons() {
        console.log(store.book)
        
        if (!store.user)
            return <div>Авторизуйтесь, чтобы скачать</div>
        if (store.user.downloads_left > 0)
            return (<button onClick={
                book.current.format == 'pdf' ? handleRequestPdf : handleRequestDjvu
            }>Загрузить {book.current.format == 'pdf' ? 'PDF' : 'DJVU'}</button>)
        return <div>У вас закончились скачивания. Обратитесь к <a href="https://vk.com/iwanryzhkov">владельцу</a></div>
    }


    function renderPage() {
        return (
            <div>
                <h1 style={{ marginBottom: 0 }}>{book.current.title}</h1>
                <div>

                    {<a href={'/folder' + book.current.folder}>[parent folder]</a>}

                    {<a style={{ marginLeft: 5 }} href={'/folder' + book.current.folder}>See error?</a>}
                </div>
                <br />

                <div>
                    Author(s): {book.current.authors}
                </div>
                <div>
                    ESBN: {book.current.esbn}
                </div>
                <div>
                    ISBN: {book.current.isbn}
                </div>
                <div>
                    Pages: {book.current.pages}
                </div>

                <br />

                {renderButtons()}
                {pdfSource && <iframe src={pdfSource} width="100%" height="500px" />}
            </div>)
    }

    useEffect(() => {
        onOpen()
    }, [])

    return (
        <div>
            {store.sourceNotFound && <Navigate to={"/404"} />}
            {isLoading ? <>Loaidng...</> : renderPage()
            }
        </div>)
};

export default Book;
