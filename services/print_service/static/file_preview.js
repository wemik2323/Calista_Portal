import * as pdfjsLib from
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.min.mjs";


pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.2.108/build/pdf.worker.min.mjs";


class PdfRenderer {

    constructor(container) {
        this.container = container;

        this.pdf = null;
        this.file = null;

        this.pageNumber = 1;
        this.renderTask = null;
    }


    async show(file, options = {}) {

        this.file = file;

        this.pageNumber = 1;

        this.clear();

        try {

            const data =
                await file.arrayBuffer();

            this.pdf =
                await pdfjsLib.getDocument({
                    data,
                }).promise;


            await this.renderPage(
                options
            );

        } catch (error) {

            console.error(
                "Ошибка загрузки PDF:",
                error
            );

            this.showError(
                "Не удалось открыть PDF."
            );
        }
    }


    async renderPage(options = {}) {

        if (!this.pdf) {
            return;
        }


        if (this.renderTask) {

            try {
                this.renderTask.cancel();
            } catch {
                // Нечего отменять
            }

            this.renderTask = null;
        }


        const page =
            await this.pdf.getPage(
                this.pageNumber
            );


        const canvas =
            document.createElement("canvas");

        canvas.className =
            "preview-pdf-canvas";


        const context =
            canvas.getContext("2d");


        const containerWidth =
            this.container.clientWidth;


        const containerHeight =
            this.container.clientHeight;


        const baseViewport =
            page.getViewport({
                scale: 1,
            });


        const padding = 24;


        const availableWidth =
            Math.max(
                containerWidth - padding * 2,
                100
            );


        const availableHeight =
            Math.max(
                containerHeight - padding * 2,
                100
            );


        const scale =
            Math.min(
                availableWidth /
                baseViewport.width,

                availableHeight /
                baseViewport.height
            );


        const viewport =
            page.getViewport({
                scale,
            });


        const devicePixelRatio =
            window.devicePixelRatio || 1;


        canvas.width =
            Math.floor(
                viewport.width *
                devicePixelRatio
            );

        canvas.height =
            Math.floor(
                viewport.height *
                devicePixelRatio
            );


        canvas.style.width =
            `${viewport.width}px`;

        canvas.style.height =
            `${viewport.height}px`;


        const renderContext = {
            canvasContext: context,
            viewport,
            transform: [
                devicePixelRatio,
                0,
                0,
                devicePixelRatio,
                0,
                0,
            ],
        };


        this.container.appendChild(
            canvas
        );


        try {

            this.renderTask =
                page.render(
                    renderContext
                );

            await this.renderTask.promise;

        } catch (error) {

            if (
                error?.name !==
                "RenderingCancelledException"
            ) {

                console.error(
                    "Ошибка рендеринга PDF:",
                    error
                );
            }

        } finally {

            this.renderTask = null;
        }


        this.createControls();
    }


    createControls() {

        const controls =
            document.createElement("div");

        controls.className =
            "pdf-preview-controls";


        const previousButton =
            document.createElement("button");

        previousButton.type =
            "button";

        previousButton.className =
            "pdf-page-button";

        previousButton.textContent =
            "‹";


        const pageInfo =
            document.createElement("span");

        pageInfo.className =
            "pdf-page-info";

        pageInfo.textContent =
            `${this.pageNumber} / ${this.pdf.numPages}`;


        const nextButton =
            document.createElement("button");

        nextButton.type =
            "button";

        nextButton.className =
            "pdf-page-button";

        nextButton.textContent =
            "›";


        previousButton.disabled =
            this.pageNumber <= 1;

        nextButton.disabled =
            this.pageNumber >= this.pdf.numPages;


        previousButton.addEventListener(
            "click",
            async () => {

                if (
                    this.pageNumber <= 1
                ) {
                    return;
                }

                this.pageNumber--;

                await this.refresh();
            }
        );


        nextButton.addEventListener(
            "click",
            async () => {

                if (
                    this.pageNumber >=
                    this.pdf.numPages
                ) {
                    return;
                }

                this.pageNumber++;

                await this.refresh();
            }
        );


        controls.appendChild(
            previousButton
        );

        controls.appendChild(
            pageInfo
        );

        controls.appendChild(
            nextButton
        );


        this.container.appendChild(
            controls
        );
    }


    async refresh() {

        this.container.innerHTML = "";

        await this.renderPage();
    }


    clear() {

        if (this.renderTask) {

            try {
                this.renderTask.cancel();
            } catch {
                // Нечего отменять
            }

            this.renderTask = null;
        }


        this.container.innerHTML = "";
    }


    showError(message) {

        this.clear();

        const element =
            document.createElement("div");

        element.className =
            "preview-message error";

        element.textContent =
            message;

        this.container.appendChild(
            element
        );
    }
}


class FilePreview {

    constructor(options = {}) {

        this.container =
            options.container;

        this.pdfRenderer =
            new PdfRenderer(
                this.container
            );

        this.objectUrl = null;
    }


    clear() {

        this.releaseObjectUrl();

        this.container.innerHTML = "";
    }


    releaseObjectUrl() {

        if (this.objectUrl) {

            URL.revokeObjectURL(
                this.objectUrl
            );

            this.objectUrl = null;
        }
    }


    async show(file, options = {}) {

        this.clear();


        if (!file) {

            this.showMessage(
                "Выберите файл"
            );

            return;
        }


        const orientation =
            options.orientation ||
            "portrait";


        const scaling =
            options.scaling ||
            "auto";


        this.updatePage(
            orientation,
            scaling
        );


        if (
            file.type.startsWith(
                "image/"
            )
        ) {

            this.showImage(
                file,
                scaling
            );

            return;
        }


        if (
            file.type ===
            "application/pdf" ||
            file.name
                .toLowerCase()
                .endsWith(".pdf")
        ) {

            await this.pdfRenderer.show(
                file,
                options
            );

            return;
        }


        if (
            file.type.startsWith(
                "text/"
            ) ||
            file.name
                .toLowerCase()
                .endsWith(".txt")
        ) {

            await this.showText(file);

            return;
        }


        this.showMessage(
            `Предпросмотр файла "${file.name}" пока недоступен.`
        );
    }


    updatePage(
        orientation,
        scaling
    ) {

        this.container.className =
            `preview-page ${orientation} ${scaling}`;
    }


    showImage(
        file,
        scaling
    ) {

        const image =
            document.createElement("img");


        image.className =
            "preview-image";


        image.alt =
            `Предпросмотр ${file.name}`;


        this.objectUrl =
            URL.createObjectURL(file);


        image.src =
            this.objectUrl;


        image.classList.toggle(
            "fill",
            scaling === "fill"
        );


        image.classList.toggle(
            "fit",
            scaling !== "fill"
        );


        this.container.appendChild(
            image
        );
    }


    async showText(file) {

        try {

            const text =
                await file.text();


            const pre =
                document.createElement("pre");


            pre.className =
                "preview-text";


            pre.textContent =
                text;


            this.container.appendChild(
                pre
            );

        } catch {

            this.showMessage(
                "Не удалось прочитать текстовый файл."
            );
        }
    }


    showMessage(message) {

        this.container.className =
            "preview-page portrait auto";


        const element =
            document.createElement("div");


        element.className =
            "preview-message";


        element.textContent =
            message;


        this.container.appendChild(
            element
        );
    }
}


export {
    FilePreview,
};