class FilePreview {
    constructor(options = {}) {
        this.container = options.container;
        this.pageClass = "preview-page";
        this.objectUrl = null;
    }


    clear() {
        this.releaseObjectUrl();
        this.container.innerHTML = "";
    }


    releaseObjectUrl() {
        if (this.objectUrl) {
            URL.revokeObjectURL(this.objectUrl);
            this.objectUrl = null;
        }
    }


    async show(file, options = {}) {
        this.clear();

        if (!file) {
            this.showMessage("Выберите файл");
            return;
        }

        const orientation =
            options.orientation || "portrait";

        const scaling =
            options.scaling || "auto";

        this.updatePage(
            orientation,
            scaling
        );


        if (file.type.startsWith("image/")) {
            this.showImage(file, scaling);
            return;
        }


        if (
            file.type === "application/pdf" ||
            file.name.toLowerCase().endsWith(".pdf")
        ) {
            this.showPdf(file);
            return;
        }


        if (
            file.type.startsWith("text/") ||
            file.name.toLowerCase().endsWith(".txt")
        ) {
            await this.showText(file);
            return;
        }


        this.showMessage(
            `Предпросмотр файла "${file.name}" пока недоступен.`
        );
    }


    updatePage(orientation, scaling) {
        this.container.className =
            `${this.pageClass} ${orientation} ${scaling}`;
    }


    showImage(file, scaling) {
        const image =
            document.createElement("img");

        image.className = "preview-image";

        image.alt =
            `Предпросмотр ${file.name}`;

        this.objectUrl =
            URL.createObjectURL(file);

        image.src = this.objectUrl;

        if (scaling === "fill") {
            image.classList.add("fill");
        } else {
            image.classList.add("fit");
        }

        this.container.appendChild(image);
    }


    showPdf(file) {
        const frame =
            document.createElement("iframe");

        frame.className = "preview-pdf";

        frame.title =
            `Предпросмотр ${file.name}`;

        this.objectUrl =
            URL.createObjectURL(file);

        frame.src = this.objectUrl;

        this.container.appendChild(frame);
    }


    async showText(file) {
        try {
            const text = await file.text();

            const pre =
                document.createElement("pre");

            pre.className = "preview-text";
            pre.textContent = text;

            this.container.appendChild(pre);

        } catch (error) {
            this.showMessage(
                "Не удалось прочитать текстовый файл."
            );
        }
    }


    showMessage(message) {
        this.container.className =
            `${this.pageClass} portrait auto`;

        const element =
            document.createElement("div");

        element.className =
            "preview-message";

        element.textContent =
            message;

        this.container.appendChild(element);
    }
}class FilePreview {
    constructor(options = {}) {
        this.container = options.container;
        this.pageClass = "preview-page";
        this.objectUrl = null;
    }


    clear() {
        this.releaseObjectUrl();
        this.container.innerHTML = "";
    }


    releaseObjectUrl() {
        if (this.objectUrl) {
            URL.revokeObjectURL(this.objectUrl);
            this.objectUrl = null;
        }
    }


    async show(file, options = {}) {
        this.clear();

        if (!file) {
            this.showMessage("Выберите файл");
            return;
        }

        const orientation =
            options.orientation || "portrait";

        const scaling =
            options.scaling || "auto";

        this.updatePage(
            orientation,
            scaling
        );


        if (file.type.startsWith("image/")) {
            this.showImage(file, scaling);
            return;
        }


        if (
            file.type === "application/pdf" ||
            file.name.toLowerCase().endsWith(".pdf")
        ) {
            this.showPdf(file);
            return;
        }


        if (
            file.type.startsWith("text/") ||
            file.name.toLowerCase().endsWith(".txt")
        ) {
            await this.showText(file);
            return;
        }


        this.showMessage(
            `Предпросмотр файла "${file.name}" пока недоступен.`
        );
    }


    updatePage(orientation, scaling) {
        this.container.className =
            `${this.pageClass} ${orientation} ${scaling}`;
    }


    showImage(file, scaling) {
        const image =
            document.createElement("img");

        image.className = "preview-image";

        image.alt =
            `Предпросмотр ${file.name}`;

        this.objectUrl =
            URL.createObjectURL(file);

        image.src = this.objectUrl;

        if (scaling === "fill") {
            image.classList.add("fill");
        } else {
            image.classList.add("fit");
        }

        this.container.appendChild(image);
    }


    showPdf(file) {
        const frame =
            document.createElement("iframe");

        frame.className = "preview-pdf";

        frame.title =
            `Предпросмотр ${file.name}`;

        this.objectUrl =
            URL.createObjectURL(file);

        frame.src = this.objectUrl;

        this.container.appendChild(frame);
    }


    async showText(file) {
        try {
            const text = await file.text();

            const pre =
                document.createElement("pre");

            pre.className = "preview-text";
            pre.textContent = text;

            this.container.appendChild(pre);

        } catch (error) {
            this.showMessage(
                "Не удалось прочитать текстовый файл."
            );
        }
    }


    showMessage(message) {
        this.container.className =
            `${this.pageClass} portrait auto`;

        const element =
            document.createElement("div");

        element.className =
            "preview-message";

        element.textContent =
            message;

        this.container.appendChild(element);
    }
}