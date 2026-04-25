import { useRef } from "react";

export default function UploadDropzone({ file, onFileChange }) {
    const inputRef = useRef(null);

    const handleChooseFile = () => {
        inputRef.current?.click();
    };

    const handleInputChange = (event) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile) {
            onFileChange(selectedFile);
        }
    };

    return (
        <div className="card border-dashed p-6">
            <input
                ref={inputRef}
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                className="hidden"
                onChange={handleInputChange}
            />

            <div className="flex flex-col items-center justify-center text-center">
                <div className="mb-4 rounded-full bg-indigo-50 p-4 text-2xl">📄</div>
                <h3 className="text-base font-semibold text-slate-900">
                    Upload your CV
                </h3>
                <p className="mt-2 text-sm text-slate-600">
                    PDF, DOCX or TXT. Keep it under 10MB.
                </p>

                <button
                    type="button"
                    onClick={handleChooseFile}
                    className="btn-secondary mt-5"
                >
                    Choose File
                </button>

                {file && (
                    <p className="mt-4 text-sm font-medium text-slate-700">
                        Selected: {file.name}
                    </p>
                )}
            </div>
        </div>
    );
}
